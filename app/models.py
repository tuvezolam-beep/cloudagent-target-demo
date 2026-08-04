from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class TaskStatus(StrEnum):
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    DONE = "done"


class ProjectCreate(BaseModel):
    name: str = Field(min_length=1, max_length=80)


class Project(BaseModel):
    id: int
    name: str
    created_at: datetime


class TaskCreate(BaseModel):
    title: str = Field(min_length=1, max_length=120)
    description: str = Field(default="", max_length=2000)
    priority: int = Field(default=3, ge=1, le=5)
    due_at: datetime | None = None


class BulkTaskCreate(BaseModel):
    tasks: list[TaskCreate] = Field(min_length=1, max_length=50)


class TaskStatusUpdate(BaseModel):
    status: TaskStatus


class Task(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    id: int
    project_id: int
    title: str
    description: str
    priority: int
    status: TaskStatus
    due_at: datetime | None
    created_at: datetime
    completed_at: datetime | None = None


class TaskPage(BaseModel):
    items: list[Task]
    page: int
    page_size: int
    total: int


class AuditEvent(BaseModel):
    id: int
    project_id: int
    task_id: int
    action: str
    created_at: datetime


class ProjectMetrics(BaseModel):
    total: int
    by_status: dict[str, int]
    overdue: int
    completion_rate: float

