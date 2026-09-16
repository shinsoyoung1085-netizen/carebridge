from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..auth import create_access_token, get_current_user, hash_password, verify_password
from ..database import get_db
from ..models import User, UserRole
from ..schemas import LoginRequest, NicknameUpdate, OrgNameUpdate, SignupRequest, TokenResponse, UserOut

router = APIRouter(tags=["auth"])


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


@router.get("/users/me", response_model=UserOut)
def read_me(current_user: User = Depends(get_current_user)):
    return current_user


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
