from fastapi import FastAPI, HTTPException, Path, Query
from typing import List, Optional
from uuid import UUID, uuid4
from .models import Task
from .db import init_db
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield

app = FastAPI(lifespan=lifespan)


# @app.post("/tasks/", response_model=Task)
# def create_task(task: Task):
#     task.id = uuid4()
#     tasks.append(task)
#     return task


# @app.get("/tasks/", response_model=List[Task])
# def read_task():
#     return tasks


# @app.get("/tasks/{task_id}", response_model=Task)
# def read_individual_task(task_id: UUID):
#     for task in tasks:
#         if task.id == task_id:
#             return task

#     raise HTTPException(status_code=404, detail="Task Not Found")

# @app.put("/tasks/{task_id}", response_model=Task)
# def update_individual_task(task_id: UUID, task_update: Task):
#     for index, task in enumerate(tasks):
#         if task.id == task_id:
#             updated_task = task.copy(update=task_update.model_dump(exclude_unset=True))
#             tasks[index] = updated_task
#             return updated_task
        
#     raise HTTPException(status_code=404, detail="task not found")

# @app.delete("/tasks/{task_id}", response_model=Task)
# def delete_individual_task(task_id: UUID):
#     for index, task in enumerate(tasks):
#         if task.id == task_id:
#             return tasks.pop(index)
        
#     raise HTTPException(status_code=404, detail="task not found")
