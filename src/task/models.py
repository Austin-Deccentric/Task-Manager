from pydantic import BaseModel, EmailStr, Field
# from datetime import datetime, timezone
# from sqlalchemy import func
from enum import Enum


class TaskStatus(str, Enum):
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    DONE = "done"


class TaskBase(BaseModel):
    title: str
    description: str

class TaskCreate(TaskBase):
    status: TaskStatus = TaskStatus.TODO

class TaskUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    status: TaskStatus | None = None

class TaskResponse(TaskCreate):
    id: int
    user_id: EmailStr
