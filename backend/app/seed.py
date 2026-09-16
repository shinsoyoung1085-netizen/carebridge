"""최초 실행 시 기본 카테고리를 채워 넣는다 (없을 때만)."""

from sqlalchemy.orm import Session

from .models import Category

DEFAULT_CATEGORIES = [
    ("급여내역 신고", "급여내역 신고·변경 관련 문의"),
    ("청구 오류", "장기요양보험 급여비용 청구 반려·오류"),
    ("시스템 사용법", "롱텀 등 공단 시스템 조작 문의"),
    ("서류 처리", "각종 신고·제출 서류 작성 및 처리"),
    ("평가 매뉴얼", "시설급여 평가 기준·절차 문의"),
]


def seed_categories(db: Session) -> None:
    if db.query(Category).count() > 0:
        return
    for name, description in DEFAULT_CATEGORIES:
        db.add(Category(name=name, description=description))
    db.commit()
