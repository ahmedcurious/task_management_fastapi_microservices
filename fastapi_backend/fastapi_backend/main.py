from fastapi import FastAPI, HTTPException, Depends, status
from typing import List
from contextlib import asynccontextmanager
from sqlmodel import Session, select
from .models import Task, User
from .db import init_db, get_session, engine
from .kafka_logic import consumer_kafka, producer_kafka
from aiokafka import AIOKafkaProducer
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from passlib.hash import bcrypt
from jose import jwt, JWTError
from datetime import datetime, timedelta, timezone
import asyncio
import json

ALGORITHM = "HS256"
SECRET_KEY = "My secure key"

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


def create_access_token(subject: str, expires_delta: timedelta) -> str:
    expire = datetime.now(timezone.utc) + expires_delta
    to_encode = {"exp": expire, "sub": str(subject)}
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_access_token(access_token: str):
    decoded_jwt = jwt.decode(access_token, SECRET_KEY, algorithms=ALGORITHM)
    return decoded_jwt


def authenticate_user(username: str,
                      password: str):
    with Session(engine) as session:
        statement_user = select(User).where(User.username == username)
        user_object = session.exec(statement=statement_user).first()
        if username != user_object.username:
            return False
        if not user_object.verify_password(password=password):
            return False
        return user_object
    

def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        user_token_data = decode_access_token(access_token=token)
        with Session(engine) as session:
            statement = select(User).where(User.username == user_token_data)
            user_object = session.exec(statement).first()
            if not user_object:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )
            return User.model_validate(user_object)
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )


@asynccontextmanager
async def lifespan(app: FastAPI):
    await asyncio.sleep(30)  # Add a 30-second delay
    asyncio.create_task(consumer_kafka(
        ['task_created', 'task_updated'], 'broker_kafka:19092'))
    init_db()
    yield


app = FastAPI(lifespan=lifespan)


@app.post("/token")
async def token_generation(form_data: OAuth2PasswordRequestForm = Depends(OAuth2PasswordRequestForm)):
    user = authenticate_user(username=form_data.username,
                             password=form_data.password)
    if not user:
        return {'error': 'invalid credentials'}

    access_token_expiry = timedelta(minutes=1)
    acces_token = create_access_token(subject=user,
                                      expires_delta=access_token_expiry)
    return {"access_token": acces_token, "token_type": "bearer", "expires_in": access_token_expiry.total_seconds()}


@app.post("/users/", response_model=User)
async def create_user(user_data: User,
                      session: Session = Depends(get_session)
                      ):
    user = User(fullname=user_data.fullname,
                email=user_data.email,
                username=user_data.username,
                passwordhash=bcrypt.hash(user_data.passwordhash))
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


@app.get("/users/me", response_model=User)
async def get_user(user: User = Depends(get_current_user)):
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
