from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class TaskCreate(BaseModel):
    title: str
    detail: Optional[str] = None
    priority: Optional[str] = "medium"
    parent_id: Optional[int] = None


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    detail: Optional[str] = None
    priority: Optional[str] = None
    status: Optional[str] = None


class Task(BaseModel):
    id: int
    title: str
    detail: Optional[str]
    priority: str
    status: str
    parent_id: Optional[int]
    created_at: datetime

    class Config:
        from_attributes = True


class AIBreakdownRequest(BaseModel):
    goal: str
    model: str = "gpt-4.1"


class SubTask(BaseModel):
    title: str
    detail: str
    priority: str  # high | medium | low


class AIBreakdownResponse(BaseModel):
    goal: str
    subtasks: list[SubTask]
