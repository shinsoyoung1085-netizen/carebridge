from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import or_
from sqlalchemy.orm import Session

from ..auth import get_current_user
from ..database import get_db
from ..models import (
    Case,
    ConsultSession,
    Match,
    MatchStatus,
    SessionStatus,
    SolutionArchive,
    User,
    UserRole,
)
from ..schemas import SolutionCreate, SolutionOut, SolutionPublishRequest

router = APIRouter(tags=["solutions"])


@router.get("/solutions", response_model=list[SolutionOut])
def search_solutions(
    category_id: int | None = Query(default=None),
    keyword: str | None = Query(default=None),
    db: Session = Depends(get_db),
):
    query = db.query(SolutionArchive).filter(SolutionArchive.is_published.is_(True))
    if category_id is not None:
        query = query.filter(SolutionArchive.category_id == category_id)
    if keyword:
        like = f"%{keyword}%"
        query = query.filter(
            or_(SolutionArchive.title.ilike(like), SolutionArchive.content.ilike(like))
        )
    return query.order_by(SolutionArchive.created_at.desc()).all()


@router.get("/solutions/{solution_id}", response_model=SolutionOut)
def get_solution(solution_id: int, db: Session = Depends(get_db)):
    solution = db.get(SolutionArchive, solution_id)
    if solution is None or not solution.is_published:
        raise HTTPException(status_code=404, detail="요청하신 정보를 찾을 수 없습니다.")
    solution.view_count += 1
    db.commit()
    db.refresh(solution)
    return solution


@router.post("/cases/{case_id}/solutions", response_model=SolutionOut, status_code=201)
def create_solution(
    case_id: int,
    payload: SolutionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != UserRole.expert:
        raise HTTPException(status_code=403, detail="숙련자만 해결 사례를 등록할 수 있습니다.")

    case = db.get(Case, case_id)
    if case is None:
        raise HTTPException(status_code=404, detail="요청하신 정보를 찾을 수 없습니다.")

    completed_session = (
        db.query(ConsultSession)
        .join(Match, ConsultSession.match_id == Match.id)
        .filter(
            Match.case_id == case_id,
            Match.expert_id == current_user.id,
            Match.status == MatchStatus.수락,
            ConsultSession.status == SessionStatus.완료,
        )
        .first()
    )
    if completed_session is None:
        raise HTTPException(
            status_code=400,
            detail="세션이 종료된 케이스에 대해서만 해결 사례를 등록할 수 있습니다.",
        )

    already_exists = (
        db.query(SolutionArchive).filter(SolutionArchive.source_case_id == case_id).first()
    )
    if already_exists is not None:
        raise HTTPException(status_code=409, detail="이미 이 케이스에 등록된 해결 사례가 있습니다.")

    solution = SolutionArchive(
        category_id=case.category_id,
        source_case_id=case.id,
        title=payload.title,
        content=payload.content,
        is_published=False,
        created_by=current_user.id,
    )
    db.add(solution)
    db.commit()
    db.refresh(solution)
    return solution


@router.get("/admin/solutions", response_model=list[SolutionOut])
def list_admin_solutions(
    is_published: bool | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """관리자용 사례 목록 조회 — 검수 대기(is_published=false) 큐 등에 사용."""
    if current_user.role != UserRole.admin:
        raise HTTPException(status_code=403, detail="접근 권한이 없습니다.")

    query = db.query(SolutionArchive)
    if is_published is not None:
        query = query.filter(SolutionArchive.is_published.is_(is_published))
    return query.order_by(SolutionArchive.created_at.desc()).all()


@router.put("/admin/solutions/{solution_id}/publish", response_model=SolutionOut)
def publish_solution(
    solution_id: int,
    payload: SolutionPublishRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != UserRole.admin:
        raise HTTPException(status_code=403, detail="접근 권한이 없습니다.")

    solution = db.get(SolutionArchive, solution_id)
    if solution is None:
        raise HTTPException(status_code=404, detail="요청하신 정보를 찾을 수 없습니다.")

    solution.is_published = payload.is_published
    db.commit()
    db.refresh(solution)
    return solution
