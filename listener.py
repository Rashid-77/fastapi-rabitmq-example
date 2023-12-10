import asyncio
import json
import logging 

from aio_pika import connect, IncomingMessage

logging.basicConfig(
    filename="log.log",
    level=logging.INFO,
    format="[%(asctime)s] %(levelname).1s %(message)s",
    datefmt="%Y.%m.%d %H:%M:%S",
    )
logging.info('hello - listener')


async def on_message(message: IncomingMessage):
    txt = message.body.decode("utf-8")
    logging.info(f'new msg = {json.loads(txt)}')


async def on_message_ws(message: IncomingMessage):
    txt = message.body.decode("utf-8")
    logging.info(f'new msg_ws = {json.loads(txt)}')
    loop = asyncio.get_event_loop()
    loop.stop()


async def main(loop):
    connection = await connect("amqp://guest:guest@rabbitmq/", loop = loop)
    channel = await connection.channel()
    logging.info('listener - start consuming')

    queue = await channel.declare_queue("fastapi_task")
    await queue.consume(on_message, no_ack = True)

    queue_ws = await channel.declare_queue("websocket_server")
    await queue_ws.consume(on_message_ws, no_ack = True)


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.create_task(main(loop))
    loop.run_forever()
    logging.info('listener - exit')
