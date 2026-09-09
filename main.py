from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.db import create_db_and_tables, engine


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
app = FastAPI(title="Task Manager", prefix="/api/v1", lifespan=lifespan)


@app.get("/")
async def root():
    return {"message": "Hello World"}