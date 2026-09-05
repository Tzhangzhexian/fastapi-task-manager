from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from database import Base, SessionLocal, engine
from models import Project, Task, User
from schemas import (
    ProjectCreate,
    ProjectResponse,
    TaskCreate,
    TaskResponse,
    UserCreate,
    UserResponse,
)


Base.metadata.create_all(bind=engine)


app = FastAPI(
    title="Task Manager API",
    description="Task management backend with users, projects and tasks",
    version="0.3.0",
)


def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()


@app.get("/")
def root():
    return {
        "message": "Task Manager API is running!"
    }


# ==================================================
# Users
# ==================================================


@app.post(
    "/users",
    response_model=UserResponse,
    status_code=201,
)
def create_user(
    user: UserCreate,
    db: Session = Depends(get_db),
):
    existing_user = db.scalar(
        select(User).where(
            User.username == user.username
        )
    )

    if existing_user is not None:
        raise HTTPException(
            status_code=409,
            detail="Username already exists",
        )

    db_user = User(
        username=user.username,
    )

    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    return db_user


@app.get(
    "/users",
    response_model=list[UserResponse],
)
def get_users(
    db: Session = Depends(get_db),
):
    return db.scalars(
        select(User).order_by(User.id)
    ).all()


# ==================================================
# Projects
# ==================================================


@app.post(
    "/projects",
    response_model=ProjectResponse,
    status_code=201,
)
def create_project(
    project: ProjectCreate,
    db: Session = Depends(get_db),
):
    user = db.get(User, project.user_id)

    if user is None:
        raise HTTPException(
            status_code=404,
            detail="User not found",
        )

    db_project = Project(
        name=project.name,
        user_id=project.user_id,
    )

    db.add(db_project)
    db.commit()
    db.refresh(db_project)

    return db_project


@app.get(
    "/projects",
    response_model=list[ProjectResponse],
)
def get_projects(
    db: Session = Depends(get_db),
):
    return db.scalars(
        select(Project).order_by(Project.id)
    ).all()


@app.get(
    "/users/{user_id}/projects",
    response_model=list[ProjectResponse],
)
def get_user_projects(
    user_id: int,
    db: Session = Depends(get_db),
):
    user = db.get(User, user_id)

    if user is None:
        raise HTTPException(
            status_code=404,
            detail="User not found",
        )

    statement = (
        select(Project)
        .where(Project.user_id == user_id)
        .order_by(Project.id)
    )

    return db.scalars(statement).all()


# ==================================================
# Tasks
# ==================================================


@app.post(
    "/tasks",
    response_model=TaskResponse,
    status_code=201,
)
def create_task(
    task: TaskCreate,
    db: Session = Depends(get_db),
):
    project = db.get(Project, task.project_id)

    if project is None:
        raise HTTPException(
            status_code=404,
            detail="Project not found",
        )

    db_task = Task(
        title=task.title,
        description=task.description,
        completed=task.completed,
        project_id=task.project_id,
    )

    db.add(db_task)
    db.commit()
    db.refresh(db_task)

    return db_task


@app.get(
    "/tasks",
    response_model=list[TaskResponse],
)
def get_tasks(
    db: Session = Depends(get_db),
):
    return db.scalars(
        select(Task).order_by(Task.id)
    ).all()


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


@app.get(
    "/projects/{project_id}/tasks",
    response_model=list[TaskResponse],
)
def get_project_tasks(
    project_id: int,
    db: Session = Depends(get_db),
):
    project = db.get(Project, project_id)

    if project is None:
        raise HTTPException(
            status_code=404,
            detail="Project not found",
        )

    statement = (
        select(Task)
        .where(Task.project_id == project_id)
        .order_by(Task.id)
    )

    return db.scalars(statement).all()


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

    project = db.get(
        Project,
        updated_task.project_id,
    )

    if project is None:
        raise HTTPException(
            status_code=404,
            detail="Project not found",
        )

    task.title = updated_task.title
    task.description = updated_task.description
    task.completed = updated_task.completed
    task.project_id = updated_task.project_id

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
