from pathlib import Path
from typing import Annotated

from fastapi import Depends
from sqlmodel import Session, SQLModel, create_engine
from src.auth.schemas import User
from src.task.schemas import Task


parent_folder = Path(__file__).parent.parent
DB_FILE = parent_folder / "task_manager.db"

engine = create_engine(f"sqlite:///{DB_FILE}", echo=True, connect_args={"check_same_thread": False})


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session

SessionDep = Annotated[Session, Depends(get_session)]
