from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

import secrets

from ..auth import create_access_token, get_current_user, hash_password, verify_password
from ..database import get_db
from ..models import Category, ExpertCategory, User, UserRole, UserStatus
from ..schemas import (
    EmailUpdate,
    GuestRequest,
    LoginRequest,
    NameUpdate,
    NicknameUpdate,
    OrgNameUpdate,
    PasswordUpdate,
    SignupRequest,
    TokenResponse,
    UserOut,
    UserStatusUpdate,
)

router = APIRouter(tags=["auth"])

# 회원가입 없이 둘러보기용 공용 체험 계정. 비밀번호는 아무도 모르는 무작위 값이라 일반 로그인은 불가능하다.
GUEST_EMAIL_DOMAIN = "@guest.carebridge.app"
GUEST_ACCOUNTS = {
    UserRole.staff: ("체험 기관담당자", "체험 요양원"),
    UserRole.expert: ("체험 숙련자", None),
}


def is_guest(user: User) -> bool:
    return user.email.endswith(GUEST_EMAIL_DOMAIN)


def forbid_guest(user: User) -> None:
    if is_guest(user):
        raise HTTPException(status_code=403, detail="체험 계정은 계정 정보를 변경할 수 없습니다.")


@router.post("/auth/signup", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def signup(payload: SignupRequest, db: Session = Depends(get_db)):
    if payload.role.value == "admin":
        raise HTTPException(status_code=400, detail="관리자 계정은 셀프 가입으로 생성할 수 없습니다.")
    if db.query(User).filter(User.email == payload.email).first():
        raise HTTPException(status_code=409, detail="이미 가입된 이메일입니다.")

    user = User(
        name=payload.name,
        email=payload.email,
        password_hash=hash_password(payload.password),
        role=payload.role,
        org_name=payload.org_name,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token(user.id)
    return TokenResponse(access_token=token, user=UserOut.model_validate(user))


@router.post("/auth/login", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="이메일 또는 비밀번호를 확인하세요.")

    token = create_access_token(user.id)
    return TokenResponse(access_token=token, user=UserOut.model_validate(user))


@router.post("/auth/guest", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def guest_login(payload: GuestRequest, db: Session = Depends(get_db)):
    if payload.role not in GUEST_ACCOUNTS:
        raise HTTPException(status_code=400, detail="체험은 기관담당자 또는 숙련자만 선택할 수 있습니다.")
    email = f"guest-{payload.role.value}{GUEST_EMAIL_DOMAIN}"
    user = db.query(User).filter(User.email == email).first()
    if user is None:
        name, org_name = GUEST_ACCOUNTS[payload.role]
        user = User(
            name=name,
            email=email,
            password_hash=hash_password(secrets.token_urlsafe(32)),
            role=payload.role,
            org_name=org_name,
        )
        db.add(user)
        db.flush()
        if payload.role == UserRole.expert:
            # 체험 숙련자는 모든 분야의 요청을 받아볼 수 있게 전문분야를 전부 등록한다.
            for category in db.query(Category).all():
                db.add(ExpertCategory(expert_id=user.id, category_id=category.id))
        db.commit()
        db.refresh(user)
    elif user.status != UserStatus.active:
        raise HTTPException(status_code=403, detail="체험 계정을 사용할 수 없습니다.")

    token = create_access_token(user.id)
    return TokenResponse(access_token=token, user=UserOut.model_validate(user))


@router.get("/users/me", response_model=UserOut)
def read_me(current_user: User = Depends(get_current_user)):
    return current_user


@router.put("/users/me/name", response_model=UserOut)
def update_name(
    payload: NameUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    forbid_guest(current_user)
    name = payload.name.strip()
    if not name:
        raise HTTPException(status_code=400, detail="이름을 입력하세요.")
    current_user.name = name
    db.commit()
    db.refresh(current_user)
    return current_user


@router.put("/users/me/email", response_model=UserOut)
def update_email(
    payload: EmailUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    forbid_guest(current_user)
    # 이메일은 로그인 아이디라, 토큰만 탈취돼도 계정을 가로챌 수 없도록 현재 비밀번호를 확인한다
    if not verify_password(payload.current_password, current_user.password_hash):
        raise HTTPException(status_code=400, detail="현재 비밀번호가 올바르지 않습니다.")
    if payload.email != current_user.email:
        if db.query(User).filter(User.email == payload.email).first():
            raise HTTPException(status_code=409, detail="이미 가입된 이메일입니다.")
        current_user.email = payload.email
        db.commit()
        db.refresh(current_user)
    return current_user


@router.put("/users/me/password", status_code=status.HTTP_204_NO_CONTENT)
def update_password(
    payload: PasswordUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    forbid_guest(current_user)
    if not verify_password(payload.current_password, current_user.password_hash):
        raise HTTPException(status_code=400, detail="현재 비밀번호가 올바르지 않습니다.")
    current_user.password_hash = hash_password(payload.new_password)
    db.commit()


@router.put("/users/me/nickname", response_model=UserOut)
def update_nickname(
    payload: NicknameUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != UserRole.expert:
        raise HTTPException(status_code=403, detail="숙련자만 별명을 등록할 수 있습니다.")
    current_user.nickname = payload.nickname
    db.commit()
    db.refresh(current_user)
    return current_user


@router.put("/users/me/org-name", response_model=UserOut)
def update_org_name(
    payload: OrgNameUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != UserRole.staff:
        raise HTTPException(status_code=403, detail="기관담당자만 소속 기관을 등록할 수 있습니다.")
    current_user.org_name = payload.org_name
    db.commit()
    db.refresh(current_user)
    return current_user


@router.get("/admin/users", response_model=list[UserOut])
def list_admin_users(
    role: UserRole | None = Query(default=None),
    status_filter: UserStatus | None = Query(default=None, alias="status"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != UserRole.admin:
        raise HTTPException(status_code=403, detail="접근 권한이 없습니다.")

    query = db.query(User)
    if role is not None:
        query = query.filter(User.role == role)
    if status_filter is not None:
        query = query.filter(User.status == status_filter)
    return query.order_by(User.id).all()


@router.put("/admin/users/{user_id}/status", response_model=UserOut)
def update_user_status(
    user_id: int,
    payload: UserStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != UserRole.admin:
        raise HTTPException(status_code=403, detail="접근 권한이 없습니다.")

    target = db.get(User, user_id)
    if target is None:
        raise HTTPException(status_code=404, detail="요청하신 정보를 찾을 수 없습니다.")
    if target.id == current_user.id and payload.status == UserStatus.suspended:
        raise HTTPException(status_code=400, detail="본인 계정은 정지할 수 없습니다.")

    target.status = payload.status
    db.commit()
    db.refresh(target)
    return target
