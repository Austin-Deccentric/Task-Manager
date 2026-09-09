# from pydantic import EmailStr
from datetime import datetime

from sqlalchemy import func
from sqlmodel import Field, Relationship, SQLModel
from sqlmodel.main import EmailStr

from src.task.models import TaskStatus
from src.auth.schema import User


class Task(SQLModel, table=True):
    id: int | None = Field(primary_key=True)
    title: str = Field(max_length=128)
    description: str
    status: TaskStatus 
    created_at: datetime = Field(
        # default_factory=lambda: datetime.now(tz=timezone.utc),
        sa_column_kwargs={"server_default": func.timezone("utc", func.now())},
    )

    # Define the Foreign Key
    user_id: EmailStr = Field(
        foreign_key="user.email",
        nullable= False,
        ondelete="CASCADE",
    )

    # Define the relationship back User so Task.user gets author of the task
    user: User = Relationship(back_populates="tasks")
