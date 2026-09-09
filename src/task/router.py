from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, Path, Query
from fastapi.exceptions import HTTPException
from pydantic import EmailStr
from sqlmodel import select

from src.auth.schemas import User
from src.db import SessionDep
from src.task.dependencies import PaginationParams, api_dep
from src.task.models import TaskCreate, TaskResponse, TaskStatus, TaskUpdate
from src.task.report import log_completion_report
from src.task.schemas import Task

router = APIRouter(prefix="/tasks", dependencies=[api_dep])


@router.get("/", response_model=list[Task], summary="List tasks")
async def get_tasks(
    session: SessionDep,
    q: Annotated[PaginationParams, Depends()]
):
    """Return a paginated list of all tasks.

    - `skip` (query): number of tasks to skip (default 0)
    - `limit` (query): max number of tasks to return (default 10)
    - `X-API-Key` header required
    """
    tasks = session.exec(select(Task).offset(q.skip).limit(q.limit)).all()
    return tasks


@router.post("/", response_model=TaskResponse, status_code=201, summary="Create a task")
async def create_task(
    task: TaskCreate,
    session: SessionDep,
    user_id: Annotated[EmailStr, Query(description="Email of the user that owns the task")],
):
    """Create a new task for an existing user.

    - `user_id` (query): email of the task's owner
    - 404 if no user matches `user_id`
    """
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    db_task = Task(**task.model_dump(), user_id=user_id)
    session.add(db_task)
    session.commit()
    session.refresh(db_task)
    
    return db_task

@router.put("/{task_id}", response_model=TaskCreate, summary="Update a task by ID")
async def update_task(
    task_id: Annotated[int, Path(gt=0, description="The ID of the task to update")],
    task: TaskUpdate,
    session: SessionDep,
    background_tasks: BackgroundTasks,
):
    """Partially update a task's title, description, and/or status.

    - `task_id` (path): existing task ID
    - body: any of `title`, `description`, `status` to overwrite
    - 404 if no task matches `task_id`
    """
    db_task = session.get(Task, task_id)
    if not db_task:
        raise HTTPException(status_code=404, detail="Task not found")

    was_done = db_task.status == TaskStatus.DONE # check if the status was already done before update
    task_data = task.model_dump(exclude_unset=True)
    db_task.sqlmodel_update(task_data)

    session.add(db_task)
    session.commit()
    session.refresh(db_task)
    if not was_done and db_task.status == TaskStatus.DONE:
        background_tasks.add_task(
            log_completion_report,
            db_task.id, 
            db_task.title, 
            db_task.user_id, 
            datetime.now(timezone.utc)
        )
    
    return db_task

@router.delete("/{task_id}", summary="Delete a task by ID")
async def delete_task(
    task_id: Annotated[int, Path(gt=0, description="The ID of the task to delete")],
    session: SessionDep,
):
    """Delete a task and return a confirmation message.

    - `task_id` (path): existing task ID
    - 404 if no task matches `task_id`
    """
    db_task = session.get(Task, task_id)
    if not db_task:
        raise HTTPException(status_code=404, detail="Task not found")

    session.delete(db_task)
    session.commit()
    return {
        "message": "Task deleted successfully"
    }

@router.patch("/{task_id}/status", response_model=TaskResponse, summary="Update a task status by ID")
async def update_task_status(
    task_id: Annotated[int, Path(gt=0, description="The ID of the task to update")],
    status: Annotated[TaskStatus, Query(description="The new status of the task")],
    session: SessionDep,
    background_tasks: BackgroundTasks,
):
    """Update a task's status by ID.

    - `task_id` (path): existing task ID
    - `status` (query): new status to set
    - 404 if no task matches `task_id`
    """
    db_task = session.get(Task, task_id)
    if not db_task:
        raise HTTPException(status_code=404, detail="Task not found")
        
    was_done = db_task.status == TaskStatus.DONE
    db_task.status = status
    session.add(db_task)
    session.commit()
    session.refresh(db_task)

    if db_task.status == TaskStatus.DONE and not was_done:
        background_tasks.add_task(
            log_completion_report,
            task_id=db_task.id,
            title=db_task.title,
            user_id=db_task.user_id,
            completed_at=datetime.now(timezone.utc),
        )

    return db_task