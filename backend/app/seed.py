"""최초 실행 시 기본 카테고리를 채워 넣는다 (없을 때만)."""

from sqlalchemy.orm import Session

from .models import Category

DEFAULT_CATEGORIES = [
    ("롱텀", "장기요양보험 정보시스템(롱텀) 사용 관련 문의"),
    ("케어포", "케어포 시스템 사용 관련 문의"),
    ("희망이음", "희망이음 시스템 사용 관련 문의"),
    ("평가규정", "시설급여 평가 기준·규정 문의"),
    ("인사/노무", "직원 인사·노무 관련 문의"),
    ("기타", "그 외 문의사항"),
]


def seed_categories(db: Session) -> None:
    if db.query(Category).count() > 0:
        return
    for name, description in DEFAULT_CATEGORIES:
        db.add(Category(name=name, description=description))
    db.commit()
