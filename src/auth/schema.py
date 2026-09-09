from datetime import datetime

from sqlalchemy import func
from sqlmodel import Field, SQLModel, Relationship

# from pydantic import EmailStr
from sqlmodel.main import EmailStr

from src.task.schema import Task


class User(SQLModel, table=True):
    email: EmailStr = Field(primary_key=True)
    username: str = Field(min_length=3, max_length=50, unique=True)
    hashed_password: str
    age: int = Field(ge=16, lt= 120)
    # is_active: bool = Field(default=True)
    created_at: datetime = Field(
        # default_factory = lambda: datetime.now(tz=timezone.utc),
        sa_column_kwargs={"server_default": func.timezone("utc", func.now())},
    )

    tasks: list[Task] = Relationship(
        back_populates="user",
        cascade_delete=True,
    )