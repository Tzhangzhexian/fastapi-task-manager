from datetime import timedelta

from fastapi import (
    Depends,
    FastAPI,
    HTTPException,
    status,
)
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.orm import Session

from auth import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    create_access_token,
    get_current_user,
    get_password_hash,
    verify_password,
)
from database import Base, engine, get_db
from models import Project, Task, User
from schemas import (
    ProjectCreate,
    ProjectResponse,
    TaskCreate,
    TaskResponse,
    Token,
    UserCreate,
    UserResponse,
)


Base.metadata.create_all(bind=engine)


app = FastAPI(
    title="Task Manager API",
    description=(
        "Task management backend "
        "with JWT authentication"
    ),
    version="0.4.0",
)


# ==================================================
# Helper functions
# ==================================================


def get_owned_project(
    project_id: int,
    current_user: User,
    db: Session,
) -> Project:
    project = db.get(
        Project,
        project_id,
    )

    if (
        project is None
        or project.user_id != current_user.id
    ):
        raise HTTPException(
            status_code=404,
            detail="Project not found",
        )

    return project


def get_owned_task(
    task_id: int,
    current_user: User,
    db: Session,
) -> Task:
    statement = (
        select(Task)
        .join(
            Project,
            Task.project_id == Project.id,
        )
        .where(
            Task.id == task_id,
            Project.user_id == current_user.id,
        )
    )

    task = db.scalar(statement)

    if task is None:
        raise HTTPException(
            status_code=404,
            detail="Task not found",
        )

    return task


# ==================================================
# Root
# ==================================================


@app.get("/")
def root():
    return {
        "message": "Task Manager API is running!"
    }


# ==================================================
# Authentication
# ==================================================


@app.post(
    "/auth/register",
    response_model=UserResponse,
    status_code=201,
)
def register(
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
        hashed_password=get_password_hash(
            user.password
        ),
    )

    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    return db_user


@app.post(
    "/auth/login",
    response_model=Token,
)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    user = db.scalar(
        select(User).where(
            User.username == form_data.username
        )
    )

    if (
        user is None
        or not verify_password(
            form_data.password,
            user.hashed_password,
        )
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={
                "WWW-Authenticate": "Bearer",
            },
        )

    access_token = create_access_token(
        data={
            "sub": user.username,
        },
        expires_delta=timedelta(
            minutes=ACCESS_TOKEN_EXPIRE_MINUTES
        ),
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
    }


@app.get(
    "/users/me",
    response_model=UserResponse,
)
def get_me(
    current_user: User = Depends(
        get_current_user
    ),
):
    return current_user


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
    current_user: User = Depends(
        get_current_user
    ),
):
    db_project = Project(
        name=project.name,
        user_id=current_user.id,
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
    current_user: User = Depends(
        get_current_user
    ),
):
    statement = (
        select(Project)
        .where(
            Project.user_id == current_user.id
        )
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
    current_user: User = Depends(
        get_current_user
    ),
):
    get_owned_project(
        task.project_id,
        current_user,
        db,
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
    current_user: User = Depends(
        get_current_user
    ),
):
    statement = (
        select(Task)
        .join(
            Project,
            Task.project_id == Project.id,
        )
        .where(
            Project.user_id == current_user.id
        )
        .order_by(Task.id)
    )

    return db.scalars(statement).all()


@app.get(
    "/tasks/{task_id}",
    response_model=TaskResponse,
)
def get_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        get_current_user
    ),
):
    return get_owned_task(
        task_id,
        current_user,
        db,
    )


@app.get(
    "/projects/{project_id}/tasks",
    response_model=list[TaskResponse],
)
def get_project_tasks(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        get_current_user
    ),
):
    get_owned_project(
        project_id,
        current_user,
        db,
    )

    statement = (
        select(Task)
        .where(
            Task.project_id == project_id
        )
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
    current_user: User = Depends(
        get_current_user
    ),
):
    task = get_owned_task(
        task_id,
        current_user,
        db,
    )

    get_owned_project(
        updated_task.project_id,
        current_user,
        db,
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
    current_user: User = Depends(
        get_current_user
    ),
):
    task = get_owned_task(
        task_id,
        current_user,
        db,
    )

    db.delete(task)
    db.commit()

    return {
        "message": "Task deleted successfully",
        "deleted_task_id": task_id,
    }
