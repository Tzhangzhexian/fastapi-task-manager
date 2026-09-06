from pydantic import BaseModel, ConfigDict, Field


# ======================
# Authentication / User
# ======================

class UserCreate(BaseModel):
    username: str
    password: str = Field(
        min_length=8,
        max_length=128,
    )


class UserResponse(BaseModel):
    id: int
    username: str

    model_config = ConfigDict(from_attributes=True)


class Token(BaseModel):
    access_token: str
    token_type: str


# ======================
# Project
# ======================

class ProjectCreate(BaseModel):
    name: str


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
    priority: str = "medium"
    project_id: int


class TaskResponse(BaseModel):
    id: int
    title: str
    description: str
    completed: bool
    project_id: int
    priority: str


    model_config = ConfigDict(from_attributes=True)
