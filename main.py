from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from database import Base, SessionLocal, engine
from models import Task
from schemas import TaskCreate, TaskResponse


Base.metadata.create_all(bind=engine)


app = FastAPI(
    title="Task Manager API",
    description="My first FastAPI backend project",
    version="0.2.0",
)


def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()


@app.get("/")
def root():
    return {"message": "Task Manager API is running!"}


@app.get(
    "/tasks",
    response_model=list[TaskResponse],
)
def get_tasks(db: Session = Depends(get_db)):
    statement = select(Task).order_by(Task.id)

    tasks = db.scalars(statement).all()

    return tasks


@app.get(
    "/tasks/{task_id}",
    response_model=TaskResponse,
)
def get_task(
    task_id: int,
    db: Session = Depends(get_db),
):
    task = db.get(Task, task_id)

    if task is None:
        raise HTTPException(
            status_code=404,
            detail="Task not found",
        )

    return task


@app.post(
    "/tasks",
    response_model=TaskResponse,
    status_code=201,
)
def create_task(
    task: TaskCreate,
    db: Session = Depends(get_db),
):
    db_task = Task(
        title=task.title,
        description=task.description,
        completed=task.completed,
    )

    db.add(db_task)

    db.commit()

    db.refresh(db_task)

    return db_task


@app.put(
    "/tasks/{task_id}",
    response_model=TaskResponse,
)
def update_task(
    task_id: int,
    updated_task: TaskCreate,
    db: Session = Depends(get_db),
):
    task = db.get(Task, task_id)

    if task is None:
        raise HTTPException(
            status_code=404,
            detail="Task not found",
        )

    task.title = updated_task.title
    task.description = updated_task.description
    task.completed = updated_task.completed

    db.commit()

    db.refresh(task)

    return task


@app.delete("/tasks/{task_id}")
def delete_task(
    task_id: int,
    db: Session = Depends(get_db),
):
    task = db.get(Task, task_id)

    if task is None:
        raise HTTPException(
            status_code=404,
            detail="Task not found",
        )

    db.delete(task)

    db.commit()

    return {
        "message": "Task deleted successfully",
        "deleted_task_id": task_id,
    }
