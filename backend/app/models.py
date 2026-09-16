"""
케어브릿지 핵심 플로우 데이터 모델.

DB 설계서(PG7반_P222_소영_케어브릿지_DB.dbml)의 12개 테이블 중
users/categories/expert_categories/cases/attachments/matches/
consult_sessions/reviews/solution_archive 9개를 구현했다.
organizations/expert_profiles/notifications는 아직 없다.
"""

from __future__ import annotations

import enum
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


class UserRole(str, enum.Enum):
    staff = "staff"
    expert = "expert"
    admin = "admin"


class UserStatus(str, enum.Enum):
    active = "active"
    suspended = "suspended"


class CaseStatus(str, enum.Enum):
    등록 = "등록"
    매칭요청 = "매칭요청"
    상담중 = "상담중"
    해결 = "해결"


class MatchStatus(str, enum.Enum):
    요청 = "요청"
    수락 = "수락"
    거절 = "거절"


class SessionStatus(str, enum.Enum):
    대기 = "대기"
    진행중 = "진행중"
    완료 = "완료"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), nullable=False)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    email: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    org_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    nickname: Mapped[str | None] = mapped_column(String(30), nullable=True)
    status: Mapped[UserStatus] = mapped_column(Enum(UserStatus), default=UserStatus.active, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    cases: Mapped[list["Case"]] = relationship(back_populates="requester", foreign_keys="Case.requester_id")
    matches: Mapped[list["Match"]] = relationship(back_populates="expert", foreign_keys="Match.expert_id")
    expert_categories: Mapped[list["ExpertCategory"]] = relationship(foreign_keys="ExpertCategory.expert_id")


class Category(Base):
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(String(200), nullable=True)


class ExpertCategory(Base):
    __tablename__ = "expert_categories"
    __table_args__ = (UniqueConstraint("expert_id", "category_id", name="uq_expert_category"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    expert_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    category_id: Mapped[int] = mapped_column(ForeignKey("categories.id"), nullable=False)

    category: Mapped[Category] = relationship()


class Case(Base):
    __tablename__ = "cases"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    requester_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    category_id: Mapped[int] = mapped_column(ForeignKey("categories.id"), nullable=False)
    title: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[CaseStatus] = mapped_column(Enum(CaseStatus), default=CaseStatus.등록, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    requester: Mapped[User] = relationship(back_populates="cases", foreign_keys=[requester_id])
    category: Mapped[Category] = relationship()
    matches: Mapped[list["Match"]] = relationship(back_populates="case")
    attachments: Mapped[list["Attachment"]] = relationship(
        back_populates="case", order_by="Attachment.uploaded_at"
    )


class Attachment(Base):
    __tablename__ = "attachments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    case_id: Mapped[int] = mapped_column(ForeignKey("cases.id"), nullable=False)
    file_url: Mapped[str] = mapped_column(String(255), nullable=False)
    file_name: Mapped[str] = mapped_column(String(100), nullable=False)
    uploaded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    case: Mapped[Case] = relationship(back_populates="attachments")


class Match(Base):
    __tablename__ = "matches"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    case_id: Mapped[int] = mapped_column(ForeignKey("cases.id"), nullable=False)
    expert_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    status: Mapped[MatchStatus] = mapped_column(Enum(MatchStatus), default=MatchStatus.요청, nullable=False)
    requested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    responded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    case: Mapped[Case] = relationship(back_populates="matches")
    expert: Mapped[User] = relationship(back_populates="matches", foreign_keys=[expert_id])
    session: Mapped["ConsultSession | None"] = relationship(back_populates="match", uselist=False)


class ConsultSession(Base):
    __tablename__ = "consult_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    match_id: Mapped[int] = mapped_column(ForeignKey("matches.id"), unique=True, nullable=False)
    remote_tool: Mapped[str | None] = mapped_column(String(30), nullable=True)
    access_code: Mapped[str | None] = mapped_column(String(20), nullable=True)
    status: Mapped[SessionStatus] = mapped_column(Enum(SessionStatus), default=SessionStatus.대기, nullable=False)
    memo: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    match: Mapped[Match] = relationship(back_populates="session")
    review: Mapped["Review | None"] = relationship(back_populates="session", uselist=False)


class Review(Base):
    __tablename__ = "reviews"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("consult_sessions.id"), unique=True, nullable=False)
    rater_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    rating: Mapped[int] = mapped_column(Integer, nullable=False)
    comment: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    session: Mapped[ConsultSession] = relationship(back_populates="review")


class SolutionArchive(Base):
    __tablename__ = "solution_archive"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    category_id: Mapped[int] = mapped_column(ForeignKey("categories.id"), nullable=False)
    source_case_id: Mapped[int | None] = mapped_column(ForeignKey("cases.id"), nullable=True)
    title: Mapped[str] = mapped_column(String(100), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    is_published: Mapped[bool] = mapped_column(default=False, nullable=False)
    view_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_by: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    category: Mapped[Category] = relationship()
    source_case: Mapped[Case | None] = relationship()
    author: Mapped[User] = relationship()
