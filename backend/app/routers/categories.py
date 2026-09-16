from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..auth import get_current_user
from ..database import get_db
from ..models import Category, ConsultSession, ExpertCategory, Match, Review, User, UserRole
from ..schemas import CategoryOut, ExpertCandidate, ExpertCategoriesUpdate

router = APIRouter(tags=["categories"])

BASE_TEMPERATURE = 36.5


def _compute_temperature(avg_rating: float | None) -> float:
    """당근마켓 매너온도 스타일 숙련도 지표.

    리뷰가 없으면 기준 온도(36.5도)에서 시작하고, 평균 평점(1~5)이
    3점보다 높으면 온도가 오르고 낮으면 내려간다.
    """
    if avg_rating is None:
        return BASE_TEMPERATURE
    temp = BASE_TEMPERATURE + (avg_rating - 3.0) * 10
    return round(min(max(temp, 0.0), 99.9), 1)


@router.get("/categories", response_model=list[CategoryOut])
def list_categories(db: Session = Depends(get_db)):
    return db.query(Category).order_by(Category.id).all()


@router.get("/experts", response_model=list[ExpertCandidate], tags=["categories"])
def list_experts(
    category_id: int | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """케이스 상세에서 매칭 요청 대상으로 고를 숙련자 목록.

    category_id를 넘기면 해당 분야를 전문분야로 등록한 숙련자만 반환하며,
    각 숙련자의 리뷰 평점을 매너온도 스타일 지표로 함께 내려준다.
    """
    query = db.query(User).filter(User.role == UserRole.expert, User.status == "active")
    if category_id is not None:
        matched_expert_ids = (
            db.query(ExpertCategory.expert_id)
            .filter(ExpertCategory.category_id == category_id)
            .subquery()
        )
        query = query.filter(User.id.in_(matched_expert_ids))
    experts = query.all()

    rating_rows = (
        db.query(Match.expert_id, func.avg(Review.rating), func.count(Review.id))
        .join(ConsultSession, ConsultSession.match_id == Match.id)
        .join(Review, Review.session_id == ConsultSession.id)
        .group_by(Match.expert_id)
        .all()
    )
    rating_map = {expert_id: (float(avg), count) for expert_id, avg, count in rating_rows}

    result = []
    for e in experts:
        avg_rating, review_count = rating_map.get(e.id, (None, 0))
        result.append(
            ExpertCandidate(
                id=e.id,
                name=e.name,
                nickname=e.nickname,
                temperature=_compute_temperature(avg_rating),
                review_count=review_count,
            )
        )
    return result


@router.get("/users/me/categories", response_model=list[CategoryOut])
def get_my_categories(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != UserRole.expert:
        raise HTTPException(status_code=403, detail="숙련자만 전문분야를 조회할 수 있습니다.")
    return [ec.category for ec in current_user.expert_categories]


@router.put("/users/me/categories", response_model=list[CategoryOut])
def set_my_categories(
    payload: ExpertCategoriesUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != UserRole.expert:
        raise HTTPException(status_code=403, detail="숙련자만 전문분야를 등록할 수 있습니다.")

    unique_ids = set(payload.category_ids)
    categories = db.query(Category).filter(Category.id.in_(unique_ids)).all()
    if len(categories) != len(unique_ids):
        raise HTTPException(status_code=400, detail="존재하지 않는 카테고리가 포함되어 있습니다.")

    db.query(ExpertCategory).filter(ExpertCategory.expert_id == current_user.id).delete()
    for category_id in unique_ids:
        db.add(ExpertCategory(expert_id=current_user.id, category_id=category_id))
    db.commit()

    return sorted(categories, key=lambda c: c.id)
