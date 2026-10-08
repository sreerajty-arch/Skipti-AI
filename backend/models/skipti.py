from datetime import datetime, timezone
from typing import Literal
from uuid import uuid4

from pydantic import BaseModel, Field, field_validator


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class UserView(BaseModel):
    id: str
    email: str
    display_name: str
    auth_mode: str = "demo_owner"


class PersonaEntryCreate(BaseModel):
    category: str = Field(min_length=2, max_length=60)
    label: str = Field(min_length=2, max_length=100)
    value: str = Field(min_length=1, max_length=2000)
    entry_type: Literal["fact", "preference", "constraint", "goal"] = "fact"
    scope: Literal["global", "domain", "project", "session"] = "global"
    sensitivity: Literal["standard", "sensitive"] = "standard"
    temporary: bool = False


class PersonaEntryUpdate(BaseModel):
    category: str | None = Field(default=None, min_length=2, max_length=60)
    label: str | None = Field(default=None, min_length=2, max_length=100)
    value: str | None = Field(default=None, min_length=1, max_length=2000)
    entry_type: Literal["fact", "preference", "constraint", "goal"] | None = None
    scope: Literal["global", "domain", "project", "session"] | None = None
    sensitivity: Literal["standard", "sensitive"] | None = None
    temporary: bool | None = None


class PersonaEntry(PersonaEntryCreate):
    id: str = Field(default_factory=lambda: str(uuid4()))
    owner_id: str
    approval_status: Literal["candidate", "approved", "rejected"] = "approved"
    source: str = "owner"
    last_confirmed_at: datetime = Field(default_factory=utc_now)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class PersonaView(BaseModel):
    owner: UserView
    revision: int
    entries: list[PersonaEntry]
    categories: list[str]


class InterviewStart(BaseModel):
    session_id: str
    question: str
    category: str
    progress: int


class InterviewAnswerRequest(BaseModel):
    session_id: str
    answer: str = Field(min_length=1, max_length=3000)
    skipped: bool = False


class InterviewAnswerResponse(BaseModel):
    session_id: str
    question: str | None
    category: str | None
    progress: int
    candidates: list[PersonaEntry]
    complete: bool
    ai_available: bool


class InterviewCompleteRequest(BaseModel):
    session_id: str
    approved_entry_ids: list[str]


class ProjectCreate(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    description: str = Field(min_length=3, max_length=2000)
    purpose: str = Field(default="", max_length=1000)
    stack: list[str] = Field(default_factory=list, max_length=20)

    @field_validator("stack")
    @classmethod
    def clean_stack(cls, value: list[str]) -> list[str]:
        return [item.strip()[:80] for item in value if item.strip()]


class Project(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    owner_id: str
    name: str
    description: str
    purpose: str = ""
    stack: list[str] = Field(default_factory=list)
    status: Literal["active", "paused", "archived"] = "active"
    revision: int = 1
    completed: list[str] = Field(default_factory=list)
    in_progress: list[str] = Field(default_factory=list)
    blockers: list[str] = Field(default_factory=list)
    decisions: list[str] = Field(default_factory=list)
    next_steps: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class ProjectDetail(BaseModel):
    project: Project
    context_entries: list[PersonaEntry]
    pending_proposals: int


class ProgressProposalCreate(BaseModel):
    update_text: str = Field(min_length=3, max_length=5000)
    expected_revision: int = Field(ge=1)
    source_provider: str = "manual"


class ProgressProposal(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    project_id: str
    owner_id: str
    summary: str
    completed: list[str] = Field(default_factory=list)
    in_progress: list[str] = Field(default_factory=list)
    blockers: list[str] = Field(default_factory=list)
    decisions: list[str] = Field(default_factory=list)
    next_steps: list[str] = Field(default_factory=list)
    source_provider: str
    verification_status: Literal["reported", "user_confirmed", "test_verified", "blocked", "superseded"] = "reported"
    status: Literal["pending_approval", "approved", "rejected", "conflict"] = "pending_approval"
    base_revision: int
    created_at: datetime = Field(default_factory=utc_now)


class ApproveProposalRequest(BaseModel):
    expected_revision: int = Field(ge=1)


class RestoreRequest(BaseModel):
    revision: int = Field(ge=1)
    expected_revision: int = Field(ge=1)


class ProjectCheckpoint(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    project_id: str
    owner_id: str
    revision: int
    summary: str
    state: dict
    source: str
    approval_status: str = "approved"
    created_at: datetime = Field(default_factory=utc_now)


class ContextSearchRequest(BaseModel):
    query: str = Field(min_length=2, max_length=2000)
    project_id: str | None = None
    max_entries: int = Field(default=6, ge=1, le=20)


class ContextSelection(BaseModel):
    id: str
    category: str
    label: str
    value: str
    source: str
    reason: str
    project_id: str | None = None


class ContextSearchResponse(BaseModel):
    query: str
    selected: list[ContextSelection]
    available_count: int
    excluded_count: int
    approximate_tokens: int
    project_revision: int | None = None


class PlaygroundRequest(ContextSearchRequest):
    session_id: str | None = None


class PlaygroundResponse(BaseModel):
    answer: str
    retrieval: ContextSearchResponse
    provider: str
    model: str
    mcp_tool: str = "search_context"


class ShareCreate(BaseModel):
    project_id: str | None = None
    permissions: list[str] = Field(min_length=1)
    duration_minutes: Literal[5, 15, 30, 60]


class ShareGrant(BaseModel):
    id: str
    project_id: str | None
    permissions: list[str]
    expires_at: datetime
    revoked_at: datetime | None = None
    redeemed_at: datetime | None = None
    status: str


class ShareCreated(ShareGrant):
    connect_url: str
    qr_data_uri: str


class RedeemRequest(BaseModel):
    token: str = Field(min_length=20, max_length=300)


class GuestContext(BaseModel):
    grant: ShareGrant
    persona_entries: list[PersonaEntry]
    project: Project | None = None


class Overview(BaseModel):
    owner: UserView
    persona_revision: int
    persona_entries: int
    project_count: int
    active_shares: int
    projects: list[Project]
    recent_entries: list[PersonaEntry]
    mcp_endpoint: str
    integration_status: dict[str, str]


class MessageResponse(BaseModel):
    message: str


class ExportResponse(BaseModel):
    filename: str
    markdown: str
    revision: int
    exported_at: datetime
