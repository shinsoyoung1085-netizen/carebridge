from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..auth import get_current_user
from ..database import get_db
from ..models import Case, Category, Match, MatchStatus, Review, SessionStatus, SolutionArchive, User, UserRole
from ..schemas import CaseCreate, CaseOut
from .attachments import UPLOAD_DIR

router = APIRouter(tags=["cases"])


def _completed_session_memo(case: Case) -> str | None:
    """완료된 상담 세션의 메모(숙련자가 남긴 해결 내용)를 찾는다."""
    for match in case.matches:
        if match.session and match.session.status == SessionStatus.완료 and match.session.memo:
            return match.session.memo
    return None


@router.post("/cases", response_model=CaseOut, status_code=201)
def create_case(
    payload: CaseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != UserRole.staff:
        raise HTTPException(status_code=403, detail="기관담당자만 케이스를 등록할 수 있습니다.")

    category = db.get(Category, payload.category_id)
    if category is None:
        raise HTTPException(status_code=400, detail="존재하지 않는 카테고리입니다.")

    case = Case(
        requester_id=current_user.id,
        category_id=payload.category_id,
        title=payload.title,
        description=payload.description,
    )
    db.add(case)
    db.commit()
    db.refresh(case)
    return case


@router.get("/cases", response_model=list[CaseOut])
def list_cases(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    query = db.query(Case)
    if current_user.role == UserRole.staff:
        query = query.filter(Case.requester_id == current_user.id)
    elif current_user.role == UserRole.expert:
        matched_case_ids = (
            db.query(Match.case_id).filter(Match.expert_id == current_user.id).subquery()
        )
        query = query.filter(Case.id.in_(matched_case_ids))
    # admin은 전체 조회
    cases = query.order_by(Case.created_at.desc()).all()

    solved_case_ids = {
        row[0]
        for row in db.query(SolutionArchive.source_case_id)
        .filter(SolutionArchive.source_case_id.isnot(None))
        .all()
    }
    for case in cases:
        case.has_solution = case.id in solved_case_ids
        case.active_match_id = next(
            (m.id for m in case.matches if m.status == MatchStatus.요청), None
        )
        case.session_memo = _completed_session_memo(case)

    return cases


@router.get("/cases/{case_id}", response_model=CaseOut)
def get_case(case_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    case = db.get(Case, case_id)
    if case is None:
        raise HTTPException(status_code=404, detail="요청하신 정보를 찾을 수 없습니다.")

    is_owner = case.requester_id == current_user.id
    is_matched_expert = any(m.expert_id == current_user.id for m in case.matches)
    if current_user.role != UserRole.admin and not is_owner and not is_matched_expert:
        raise HTTPException(status_code=403, detail="접근 권한이 없습니다.")

    # 같은 카테고리의 승인된 해결 사례를 최대 5건 노출 (REQ-FUNC-004)
    case.related_solutions = (
        db.query(SolutionArchive)
        .filter(
            SolutionArchive.category_id == case.category_id,
            SolutionArchive.is_published.is_(True),
        )
        .order_by(SolutionArchive.created_at.desc())
        .limit(5)
        .all()
    )
    case.has_solution = (
        db.query(SolutionArchive).filter(SolutionArchive.source_case_id == case.id).first()
        is not None
    )
    case.active_match_id = next(
        (m.id for m in case.matches if m.status == MatchStatus.요청), None
    )
    case.session_memo = _completed_session_memo(case)

    return case


@router.delete("/cases/{case_id}", status_code=204)
def delete_case(
    case_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """케이스를 매칭·세션 기록까지 포함해 완전히 삭제한다.

    이미 공개된 해결 사례(solution_archive)는 지우지 않고 원본 케이스
    연결(source_case_id)만 끊어서, 다른 사용자에게 이미 도움을 준 내용은 보존한다.
    """
    case = db.get(Case, case_id)
    if case is None:
        raise HTTPException(status_code=404, detail="요청하신 정보를 찾을 수 없습니다.")
    if case.requester_id != current_user.id:
        raise HTTPException(status_code=403, detail="본인이 등록한 케이스만 삭제할 수 있습니다.")

    db.query(SolutionArchive).filter(SolutionArchive.source_case_id == case.id).update(
        {SolutionArchive.source_case_id: None}
    )

    for match in case.matches:
        if match.session:
            db.query(Review).filter(Review.session_id == match.session.id).delete()
            db.delete(match.session)
        db.delete(match)

    case_dir = UPLOAD_DIR / str(case.id)
    for attachment in case.attachments:
        file_path = case_dir / Path(attachment.file_url).name
        if file_path.exists():
            file_path.unlink()
        db.delete(attachment)
    if case_dir.exists() and not any(case_dir.iterdir()):
        case_dir.rmdir()

    db.delete(case)
    db.commit()
