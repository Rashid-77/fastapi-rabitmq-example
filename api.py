from fastapi import FastAPI
from pydantic import BaseModel
from starlette.responses import HTMLResponse
from aio_pika import connect, Message
from typing import Dict
import json
import logging 

logging.basicConfig(
    filename="log.log",
    level=logging.INFO,
    format="[%(asctime)s] %(levelname).1s %(message)s",
    datefmt="%Y.%m.%d %H:%M:%S",
    )


queued_tasks = 0
connection = None


class Task(BaseModel):
    taskid: str
    description: str
    params: Dict[str, str] = {}


async def stop_websocket_server():
    task = Task(
        taskid = "task1",
        description = "Stop websocket server",
        params = {
            "ws": "stop",
        },
    )
    await send_rabbitmq(task, "websocket_server")


async def lifespan(app: FastAPI):
    global connection
    logging.info(f'start FastApi')
    connection = await connect("amqp://guest:guest@rabbitmq/")
    yield
    logging.info(f'stop FastApi')
    await stop_websocket_server()
    await connection.close()

app = FastAPI(lifespan=lifespan)


@app.get("/")
async def read_root():
    return HTMLResponse(content = "POST /add-tasks<br>GET /queued-tasks")


async def send_rabbitmq(msg: Task, routing_key: str):
    global connection
    channel = await connection.channel()

    await channel.default_exchange.publish(
        Message(json.dumps(msg.model_dump()).encode("utf-8")),
        routing_key = routing_key
    )


@app.get("/add-tasks")
async def add_tasks():
    global queued_tasks
    task = Task(
        taskid = "task2",
        description = "Example description",
        params = {
            "param1": "1",
            "param2": "2",
        },
    )
    await send_rabbitmq(task, "fastapi_task")
    queued_tasks += 1
    return {"message": f"Task {task.taskid} added"}


@app.get("/queued-tasks")
def get_quueu_stats():
    global queued_tasks
    return queued_tasks


@app.get("/healtz")
def get_healtz():
    return {"healtz": "ok"}


@app.get("/ws_stop")
async def get_ws_stop():
    await stop_websocket_server()
    return {"ws_started_stopping": "ok"}