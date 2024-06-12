from sqlmodel import SQLModel, Field
from typing import Optional

class TaskBase(SQLModel):
    title: str = Field(max_length=255)
    description: Optional[str] = Field(default=None)
    completed: bool = False

class Task(TaskBase, table=True):
    id: int = Field(default=None, primary_key=True)
