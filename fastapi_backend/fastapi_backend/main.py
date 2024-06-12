from fastapi import FastAPI, HTTPException, Path, Query, Depends
from typing import List, Optional
from contextlib import asynccontextmanager
from sqlmodel import Session, select
from .models import Task
from .db import init_db, get_session


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield

app = FastAPI(lifespan=lifespan)


@app.post("/tasks/", response_model=Task)
async def create_task(task_data: Task,
                      session: Session = Depends(get_session)
                      ):
    task = Task(title=task_data.title,
                description=task_data.description, completed=task_data.completed)
    session.add(task)
    session.commit()
    session.refresh(task)
    return task


@app.get("/tasks/", response_model=List[Task])
async def read_task(session: Session = Depends(get_session)):
    task_list = session.exec(select(Task)).all()
    return task_list


@app.get("/tasks/{task_id}", response_model=Task)
async def read_individual_task(task_id: int,
                               session: Session = Depends(get_session)):
    task = session.get(Task, task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task Not Found")
    return task



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
