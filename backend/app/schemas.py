from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from .models import CaseStatus, MatchStatus, SessionStatus, UserRole, UserStatus


# ---------- User / Auth ----------

class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    role: UserRole
    name: str
    nickname: str | None
    email: EmailStr
    org_name: str | None
    status: UserStatus
    created_at: datetime


class NicknameUpdate(BaseModel):
    nickname: str | None = Field(default=None, max_length=30)


class OrgNameUpdate(BaseModel):
    org_name: str | None = Field(default=None, max_length=100)


class SignupRequest(BaseModel):
    name: str = Field(min_length=1, max_length=50)
    email: EmailStr
    password: str = Field(min_length=8, max_length=100)
    role: UserRole
    org_name: str | None = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


# ---------- Category ----------

class CategoryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str | None


class ExpertCategoriesUpdate(BaseModel):
    category_ids: list[int]


class ExpertCandidate(BaseModel):
    id: int
    name: str
    nickname: str | None
    temperature: float
    review_count: int


# ---------- Case ----------

class CaseCreate(BaseModel):
    category_id: int
    title: str = Field(min_length=1, max_length=100)
    description: str = Field(min_length=1, max_length=2000)


class AttachmentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    file_url: str
    file_name: str
    uploaded_at: datetime


class SolutionSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    view_count: int


class CaseOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    requester_id: int
    category: CategoryOut
    title: str
    description: str
    status: CaseStatus
    created_at: datetime
    resolved_at: datetime | None
    attachments: list[AttachmentOut] = []
    related_solutions: list[SolutionSummary] = []
    has_solution: bool = False
    active_match_id: int | None = None
    session_memo: str | None = None


# ---------- Match ----------

class MatchCreate(BaseModel):
    expert_id: int


class MatchDecision(BaseModel):
    action: str = Field(pattern="^(accept|reject)$")


class MatchOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    case_id: int
    case_title: str = ""
    case_description: str = ""
    expert_id: int
    expert_display_name: str = ""
    status: MatchStatus
    requested_at: datetime
    responded_at: datetime | None
    session_id: int | None = None


# ---------- Session ----------

class SessionUpdate(BaseModel):
    remote_tool: str | None = None
    access_code: str | None = None
    memo: str | None = None
    status: SessionStatus | None = None


class SessionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    match_id: int
    case_id: int
    expert_id: int
    requester_id: int
    remote_tool: str | None
    access_code: str | None
    status: SessionStatus
    memo: str | None
    started_at: datetime | None
    ended_at: datetime | None


# ---------- Review ----------

class ReviewCreate(BaseModel):
    rating: int = Field(ge=1, le=5)
    comment: str | None = Field(default=None, max_length=500)


class ReviewOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    session_id: int
    rater_id: int
    rating: int
    comment: str | None
    created_at: datetime


# ---------- Solution archive ----------

class SolutionCreate(BaseModel):
    title: str = Field(min_length=1, max_length=100)
    content: str = Field(min_length=1)


class SolutionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    category: CategoryOut
    source_case_id: int | None
    title: str
    content: str
    is_published: bool
    view_count: int
    created_by: int
    created_at: datetime


class SolutionPublishRequest(BaseModel):
    is_published: bool


# ---------- Manual chatbot ----------

class ChatRequest(BaseModel):
    message: str = Field(min_length=1)


class ChatResponse(BaseModel):
    answer: str
    sources: list[str]
