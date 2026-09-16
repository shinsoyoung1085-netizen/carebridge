from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..auth import get_current_user
from ..database import get_db
from ..models import (
    Case,
    CaseStatus,
    ConsultSession,
    ExpertCategory,
    Match,
    MatchStatus,
    SessionStatus,
    User,
    UserRole,
)
from ..schemas import MatchCreate, MatchDecision, MatchOut

router = APIRouter(tags=["matches"])


def _to_match_out(match: Match) -> MatchOut:
    out = MatchOut.model_validate(match)
    out.session_id = match.session.id if match.session else None
    out.case_title = match.case.title
    out.case_description = match.case.description
    out.expert_display_name = match.expert.nickname or match.expert.name
    return out


@router.post("/cases/{case_id}/matches", response_model=MatchOut, status_code=201)
def request_match(
    case_id: int,
    payload: MatchCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    case = db.get(Case, case_id)
    if case is None:
        raise HTTPException(status_code=404, detail="요청하신 정보를 찾을 수 없습니다.")
    if case.requester_id != current_user.id:
        raise HTTPException(status_code=403, detail="접근 권한이 없습니다.")

    active_match = next(
        (m for m in case.matches if m.status in (MatchStatus.요청, MatchStatus.수락)), None
    )
    if active_match is not None:
        raise HTTPException(status_code=409, detail="이미 매칭이 진행 중인 케이스입니다.")

    expert = db.get(User, payload.expert_id)
    if expert is None or expert.role != UserRole.expert:
        raise HTTPException(status_code=400, detail="존재하지 않는 숙련자입니다.")

    has_category = (
        db.query(ExpertCategory)
        .filter(
            ExpertCategory.expert_id == payload.expert_id,
            ExpertCategory.category_id == case.category_id,
        )
        .first()
    )
    if has_category is None:
        raise HTTPException(
            status_code=400,
            detail="선택한 숙련자는 이 카테고리를 전문분야로 등록하지 않았습니다.",
        )

    match = Match(case_id=case.id, expert_id=payload.expert_id)
    case.status = CaseStatus.매칭요청
    db.add(match)
    db.commit()
    db.refresh(match)
    return _to_match_out(match)


@router.get("/cases/{case_id}/matches", response_model=list[MatchOut])
def list_case_matches(
    case_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    case = db.get(Case, case_id)
    if case is None:
        raise HTTPException(status_code=404, detail="요청하신 정보를 찾을 수 없습니다.")

    is_owner = case.requester_id == current_user.id
    is_related_expert = any(m.expert_id == current_user.id for m in case.matches)
    if current_user.role != UserRole.admin and not is_owner and not is_related_expert:
        raise HTTPException(status_code=403, detail="접근 권한이 없습니다.")

    return [_to_match_out(m) for m in case.matches]


@router.get("/matches", response_model=list[MatchOut])
def list_my_matches(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """숙련자 매칭 요청함: 나에게 들어온 매칭 요청 목록."""
    matches = (
        db.query(Match)
        .filter(Match.expert_id == current_user.id)
        .order_by(Match.requested_at.desc())
        .all()
    )
    return [_to_match_out(m) for m in matches]


@router.put("/matches/{match_id}", response_model=MatchOut)
def decide_match(
    match_id: int,
    payload: MatchDecision,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    match = db.get(Match, match_id)
    if match is None:
        raise HTTPException(status_code=404, detail="요청하신 정보를 찾을 수 없습니다.")
    if match.expert_id != current_user.id:
        raise HTTPException(status_code=403, detail="접근 권한이 없습니다.")
    if match.status != MatchStatus.요청:
        raise HTTPException(status_code=409, detail="이미 처리된 요청입니다.")

    match.responded_at = datetime.now(timezone.utc)
    if payload.action == "accept":
        match.status = MatchStatus.수락
        match.case.status = CaseStatus.상담중
        session = ConsultSession(match_id=match.id, status=SessionStatus.대기)
        db.add(session)
    else:
        match.status = MatchStatus.거절
        match.case.status = CaseStatus.등록

    db.commit()
    db.refresh(match)
    return _to_match_out(match)


@router.delete("/matches/{match_id}", status_code=204)
def delete_match_request(
    match_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """기관담당자가 아직 처리되지 않은(요청 상태) 매칭 요청을 취소한다."""
    match = db.get(Match, match_id)
    if match is None:
        raise HTTPException(status_code=404, detail="요청하신 정보를 찾을 수 없습니다.")
    if match.case.requester_id != current_user.id:
        raise HTTPException(status_code=403, detail="접근 권한이 없습니다.")
    if match.status != MatchStatus.요청:
        raise HTTPException(status_code=409, detail="이미 처리된 매칭 요청은 삭제할 수 없습니다.")

    case = match.case
    db.delete(match)
    case.status = CaseStatus.등록
    db.commit()
