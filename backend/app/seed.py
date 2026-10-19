"""최초 실행 시 기본 카테고리를 채워 넣는다 (없을 때만)."""

from sqlalchemy.orm import Session

from .auth import hash_password
from .models import Category, ExpertCategory, User, UserRole

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


# 둘러보기용 공용 체험 계정. 로그인 화면에 공개되는 계정이므로 이 계정으로는 개인정보를 입력하지 않는다.
DEMO_PASSWORD = "carebridge1234"
DEMO_ACCOUNTS = [
    ("demo.staff@carebridge.app", "체험 기관담당자", UserRole.staff, "체험 요양원"),
    ("demo.expert@carebridge.app", "체험 숙련자", UserRole.expert, None),
]
DEMO_EMAILS = {email for email, *_ in DEMO_ACCOUNTS}


def seed_demo_accounts(db: Session) -> None:
    """체험 계정이 없을 때만 만든다. 숙련자에게는 모든 분야를 전문분야로 등록한다."""
    for email, name, role, org_name in DEMO_ACCOUNTS:
        if db.query(User).filter(User.email == email).first():
            continue
        user = User(
            name=name,
            email=email,
            password_hash=hash_password(DEMO_PASSWORD),
            role=role,
            org_name=org_name,
        )
        db.add(user)
        db.flush()
        if role == UserRole.expert:
            for category in db.query(Category).all():
                db.add(ExpertCategory(expert_id=user.id, category_id=category.id))
    db.commit()
