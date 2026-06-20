from pydantic import BaseModel
from typing import Optional, Literal
from datetime import datetime, date


# ── Auth ──────────────────────────────────────────────────────────────────
class UserOut(BaseModel):
    id: int
    github_id: str
    username: str
    name: Optional[str]
    avatar_url: Optional[str]
    role: str
    team_id: Optional[int]
    created_at: datetime

    class Config:
        from_attributes = True


# ── Teams ─────────────────────────────────────────────────────────────────
class TeamCreate(BaseModel):
    name: str


class TeamOut(BaseModel):
    id: int
    name: str
    created_at: datetime

    class Config:
        from_attributes = True


# ── Premises (대전제 / 소전제) ─────────────────────────────────────────────
class PremiseCreate(BaseModel):
    type: Literal["initiative", "goal"]
    title: str
    description: Optional[str] = None
    team_id: Optional[int] = None
    parent_id: Optional[int] = None  # goal이 initiative를 참조


class PremiseUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None
    parent_id: Optional[int] = None


class PremiseOut(BaseModel):
    id: int
    type: str
    title: str
    description: Optional[str]
    team_id: Optional[int]
    created_by: Optional[int]
    parent_id: Optional[int]
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ── Daily Todos ───────────────────────────────────────────────────────────
class DailyTodoCreate(BaseModel):
    title: str
    detail: Optional[str] = None
    todo_date: Optional[date] = None


class DailyTodoUpdate(BaseModel):
    title: Optional[str] = None
    detail: Optional[str] = None
    status: Optional[Literal["todo", "done"]] = None


class DailyTodoOut(BaseModel):
    id: int
    user_id: int
    title: str
    detail: Optional[str]
    status: str
    todo_date: date
    created_at: datetime
    completed_at: Optional[datetime]

    class Config:
        from_attributes = True


class DailyTodoWithAnalysis(DailyTodoOut):
    analysis: Optional[dict] = None


# ── AI Analysis ───────────────────────────────────────────────────────────
class AnalysisOut(BaseModel):
    id: int
    todo_id: int
    premise_id: Optional[int]
    relation: Optional[str]
    confidence: float
    reason: Optional[str]
    analyzed_at: datetime

    class Config:
        from_attributes = True


class AnalysisTriggerResponse(BaseModel):
    message: str
    analyzed: int


# ── Team Dashboard ────────────────────────────────────────────────────────
class MemberTodaySummary(BaseModel):
    user_id: int
    username: str
    avatar_url: Optional[str]
    total: int
    done: int
    grand_related: int
    small_related: int


class TeamDashboard(BaseModel):
    date: date
    team_id: int
    members: list[MemberTodaySummary]
    unsubmitted: list[str]
