from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..auth import get_current_user
from ..database import get_db
from ..models import CaseStatus, ConsultSession, Review, SessionStatus, User, UserRole
from ..schemas import ReviewCreate, ReviewOut, SessionOut, SessionUpdate

router = APIRouter(tags=["sessions"])


def _authorize(session: ConsultSession, user: User) -> None:
    is_requester = session.match.case.requester_id == user.id
    is_expert = session.match.expert_id == user.id
    if user.role != UserRole.admin and not is_requester and not is_expert:
        raise HTTPException(status_code=403, detail="접근 권한이 없습니다.")


def _to_session_out(session: ConsultSession) -> SessionOut:
    return SessionOut(
        id=session.id,
        match_id=session.match_id,
        case_id=session.match.case_id,
        expert_id=session.match.expert_id,
        requester_id=session.match.case.requester_id,
        remote_tool=session.remote_tool,
        access_code=session.access_code,
        status=session.status,
        memo=session.memo,
        started_at=session.started_at,
        ended_at=session.ended_at,
    )


@router.get("/sessions/{session_id}", response_model=SessionOut)
def get_session(session_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    session = db.get(ConsultSession, session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="요청하신 정보를 찾을 수 없습니다.")
    _authorize(session, current_user)
    return _to_session_out(session)


@router.put("/sessions/{session_id}", response_model=SessionOut)
def update_session(
    session_id: int,
    payload: SessionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    session = db.get(ConsultSession, session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="요청하신 정보를 찾을 수 없습니다.")
    _authorize(session, current_user)

    is_expert = session.match.expert_id == current_user.id

    if payload.remote_tool is not None or payload.access_code is not None:
        if not is_expert:
            raise HTTPException(status_code=403, detail="원격지원 도구·접속코드는 숙련자만 입력할 수 있습니다.")
        if payload.remote_tool is not None:
            session.remote_tool = payload.remote_tool
        if payload.access_code is not None:
            session.access_code = payload.access_code

    if payload.memo is not None:
        session.memo = payload.memo

    if payload.status is not None:
        if payload.status == SessionStatus.진행중 and session.status == SessionStatus.대기:
            if not session.remote_tool or not session.access_code:
                raise HTTPException(
                    status_code=400,
                    detail="원격지원 도구와 접속코드를 입력해주세요.",
                )
            session.status = SessionStatus.진행중
            session.started_at = datetime.now(timezone.utc)
        elif payload.status == SessionStatus.완료 and session.status == SessionStatus.진행중:
            session.status = SessionStatus.완료
            session.ended_at = datetime.now(timezone.utc)
            session.match.case.status = CaseStatus.해결
            session.match.case.resolved_at = session.ended_at
        elif payload.status != session.status:
            raise HTTPException(status_code=400, detail="허용되지 않는 상태 전이입니다.")

    db.commit()
    db.refresh(session)
    return _to_session_out(session)


@router.post("/sessions/{session_id}/reviews", response_model=ReviewOut, status_code=201)
def create_review(
    session_id: int,
    payload: ReviewCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    session = db.get(ConsultSession, session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="요청하신 정보를 찾을 수 없습니다.")
    if session.match.case.requester_id != current_user.id:
        raise HTTPException(status_code=403, detail="기관담당자만 평가를 등록할 수 있습니다.")
    if session.status != SessionStatus.완료:
        raise HTTPException(status_code=400, detail="세션 종료 후에만 평가할 수 있습니다.")
    if session.review is not None:
        raise HTTPException(status_code=409, detail="이미 평가가 등록된 세션입니다.")

    review = Review(
        session_id=session.id,
        rater_id=current_user.id,
        rating=payload.rating,
        comment=payload.comment,
    )
    db.add(review)
    db.commit()
    db.refresh(review)
    return review
