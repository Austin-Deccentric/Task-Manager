from contextlib import asynccontextmanager

from fastapi import FastAPI

# from src.auth.schemas import User
# from src.task.schemas import Task
from src.auth.router import router as auth_router
from src.db import create_db_and_tables, engine
from src.task.router import router as task_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # ---- STARTUP LOGIC ----
    # This runs BEFORE the application starts accepting requests
    print("Application is starting up, creating database...")
    create_db_and_tables()
    
    yield  
    
    engine.dispose()
    print("Application is shutting down...")


# Pass the lifespan context manager to the FastAPI instance
app = FastAPI(
    title="Task Manager", 
    prefix="/api/v1", 
    lifespan=lifespan
)


app.include_router(auth_router, tags=['User'])
app.include_router(task_router, tags=['Task'])

@app.get("/")
async def root():
    return {"message": "Hello World"}