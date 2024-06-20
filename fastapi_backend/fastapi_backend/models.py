from sqlmodel import SQLModel, Field
from typing import Optional

class TaskBase(SQLModel):
    title: str = Field(max_length=255)
    description: Optional[str] = Field(default=None)
    completed: bool = False

class Task(TaskBase, table=True):
    id: int = Field(default=None, primary_key=True)


class UserBase(SQLModel):
    username: str = Field(max_length=64, unique=True)
    passwordhash: str = Field(max_length=128)

    @classmethod
    async def get_user(cls, username):
        return cls.get(username=username)
    
    def verify_password(self, password):
        return True

class User(UserBase, table=True):
    id: int = Field(default=None, primary_key=True)
