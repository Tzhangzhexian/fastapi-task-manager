from pydantic import BaseModel, ConfigDict


# ======================
# User
# ======================

class UserCreate(BaseModel):
    username: str


class UserResponse(BaseModel):
    id: int
    username: str

    model_config = ConfigDict(from_attributes=True)


# ======================
# Project
# ======================

class ProjectCreate(BaseModel):
    name: str
    user_id: int


class ProjectResponse(BaseModel):
    id: int
    name: str
    user_id: int

    model_config = ConfigDict(from_attributes=True)


# ======================
# Task
# ======================

class TaskCreate(BaseModel):
    title: str
    description: str = ""
    completed: bool = False
    project_id: int


class TaskResponse(BaseModel):
    id: int
    title: str
    description: str
    completed: bool
    project_id: int

    model_config = ConfigDict(from_attributes=True)
