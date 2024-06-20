from fastapi import FastAPI, HTTPException, Depends
from typing import List
from contextlib import asynccontextmanager
from sqlmodel import Session, select
from .models import Task, User
from .db import init_db, get_session
from .kafka_logic import consumer_kafka, producer_kafka
from aiokafka import AIOKafkaProducer
import asyncio
import json
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from passlib.hash import bcrypt


@asynccontextmanager
async def lifespan(app: FastAPI):
    await asyncio.sleep(30)  # Add a 30-second delay
    asyncio.create_task(consumer_kafka(
        ['task_created', 'task_updated'], 'broker_kafka:19092'))
    init_db()
    yield

app = FastAPI(lifespan=lifespan)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


@app.post("/users/", response_model=User)
async def create_user(user_data: User,
                      session: Session = Depends(get_session)
                      ):
    user = User(username=user_data.username,
                passwordhash=bcrypt.hash(user_data.passwordhash))
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


@app.post("/tasks/", response_model=Task)
async def create_task(task_data: Task,
                      session: Session = Depends(get_session),
                      producer: AIOKafkaProducer = Depends(producer_kafka)
                      ):
    task = Task(title=task_data.title,
                description=task_data.description, completed=task_data.completed)
    session.add(task)
    session.commit()
    session.refresh(task)
    task_dictionary = task.model_dump()
    task_json = json.dumps(task_dictionary).encode("utf-8")
    print(f"Tasks Json: {task_json}")
    await producer.send_and_wait("task_created", task_json)
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


@app.put("/tasks/{task_id}", response_model=Task)
async def update_individual_task(task_id: int,
                                 task_update: Task,
                                 session: Session = Depends(get_session),
                                 producer: AIOKafkaProducer = Depends(producer_kafka)):
    taskupdate_data = Task(title=task_update.title,
                           description=task_update.description,
                           completed=task_update.completed)
    task = session.get(Task, task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task Not Found")
    task.title = task_update.title
    task.description = task_update.description
    task.completed = task_update.completed
    session.commit()
    session.refresh(task)
    taskupdate_data_dictionary = taskupdate_data.model_dump()
    taskupdate_data_json = json.dumps(
        taskupdate_data_dictionary).encode("utf-8")
    print(f"Updated Tasks Json: {taskupdate_data_json}")
    await producer.send_and_wait('task_updated', taskupdate_data_json)
    return task


@app.delete("/tasks/{task_id}", response_model=Task)
async def delete_individual_task(task_id: int,
                                 session: Session = Depends(get_session)):
    task = session.get(Task, task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task Not Found")
    session.delete(task)
    session.commit()
    return task
