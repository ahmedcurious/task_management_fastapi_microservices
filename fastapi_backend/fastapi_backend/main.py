from fastapi import FastAPI, HTTPException, Depends
from typing import List
from contextlib import asynccontextmanager
from sqlmodel import Session, select
from .models import Task
from .db import init_db, get_session
from aiokafka import AIOKafkaConsumer, AIOKafkaProducer
import asyncio
import json


async def consumer_kafka(topic, bootstrap_servers):
    consumer = AIOKafkaConsumer(
        topic,
        bootstrap_servers=bootstrap_servers,
        group_id="my-group",
        auto_offset_reset="earliest"
    )

    await consumer.start()
    try:
        async for message in consumer:
            task_data = json.loads(message.value.decode("utf-8"))
            print(f"Recieved Message: {task_data} on topic {message.topic}")
    except asyncio.CancelledError:
        pass
    finally:
        await consumer.stop()


async def producer_kafka():
    producer_var = AIOKafkaProducer(bootstrap_servers='broker_kafka:19092')
    await producer_var.start()
    try:
        yield producer_var
    finally:
        await producer_var.stop()


@asynccontextmanager
async def lifespan(app: FastAPI):
    await asyncio.sleep(30)  # Add a 30-second delay
    asyncio.create_task(consumer_kafka('task_created', 'broker_kafka:19092'))
    init_db()
    yield

app = FastAPI(lifespan=lifespan)


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
                                 session: Session = Depends(get_session)):
    task = session.get(Task, task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task Not Found")
    task.title = task_update.title
    task.description = task_update.description
    task.completed = task_update.completed
    session.commit()
    session.refresh(task)
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
