from aiokafka import AIOKafkaConsumer, AIOKafkaProducer
from typing import List
import asyncio
import json

async def consumer_kafka(topics: List[str], bootstrap_servers):
    consumer = AIOKafkaConsumer(
        *topics,
        bootstrap_servers=bootstrap_servers,
        group_id="my-group",
        auto_offset_reset="earliest"
    )

    await consumer.start()
    try:
        async for message in consumer:
            if message.topic == "task_created":
                task_created_message = json.loads(
                    message.value.decode("utf-8"))
                print(f"Recieved Message: {
                      task_created_message} on topic {message.topic}")
            elif message.topic == "task_updated":
                task_updated_message = json.loads(
                    message.value.decode("utf-8"))
                print(f"Recieved Message: {
                      task_updated_message} on topic {message.topic}")
            else:
                # Handle unexpected topics (optional)
                unknown_topic_message = json.loads(
                    message.value.decode("utf-8"))
                print(f"Recieved Message: {
                      unknown_topic_message} on topic {message.topic}")
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