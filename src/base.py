import multiprocessing
import os
import time

from typing import Callable, Type, Any
from uuid import uuid4
from kombu import Connection, Queue, Message, Producer
from kombu.mixins import Consumer as KombuConsumer, ConsumerProducerMixin

AMQP_HOST = os.getenv("AMQP_HOST")
AMQP_PORT = os.getenv("AMQP_PORT")
AMQP_LOGIN = os.getenv("AMQP_LOGIN")
AMQP_PASSWORD = os.getenv("AMQP_PASSWORD")
AMQP_EXCHANGE = os.getenv("AMQP_EXCHANGE")
AMQP_CONNECTION_CONFIG = {
    "hostname": f"amqp://{AMQP_LOGIN}:{AMQP_PASSWORD}@{AMQP_HOST}:{AMQP_PORT}//",
    "transport_options": {"confirm_publish": True}
}


class AMQPWorker(ConsumerProducerMixin):
    """
    Базовый класс воркера
    """
    connection: Connection
    queue: Queue
    queue_name: str
    exchange: str

    def __init__(
            self,
            queue: str,
            exchange: str = AMQP_EXCHANGE,
            create_queue: bool = True
    ):
        self.connection = Connection(**AMQP_CONNECTION_CONFIG)
        self.queue_name = queue
        self.create_queue = create_queue
        if self.create_queue:
            self.queue = Queue(
                name=f"{queue}",
                exchange=exchange,
                routing_key=queue,
                channel=self.connection.channel(),
                max_priority=5
            )
            self.queue.declare()
        self.exchange = exchange

    def run(self, **kwargs):
        super().run(**kwargs)


class AMQPWorkerConsumerBase(AMQPWorker):
    handler: Callable

    def __init__(self, handler: Callable, **kwargs):
        super().__init__(**kwargs)
        self.handler = handler

    def get_consumers(self, Consumer: Type[KombuConsumer], channel):
        return [
            Consumer(
                queues=[self.queue],
                accept=["json"],
                on_message=self.handle_message,
                prefetch_count=1
            )
        ]

    def handle_message(self, message: Message):
        try:
            self.handler(message)
        except Exception as ex:
            print(f"AMQPConsumer error: {ex}")
        finally:
            try:
                message.ack()
            except:
                pass


class AMQPWorkerProducerBase(AMQPWorker):
    messages_queue: multiprocessing.Queue

    def __init__(self, messages_queue: multiprocessing.Queue = None, publish: Callable = None, **kwargs):
        self.messages_queue = messages_queue or multiprocessing.Queue()
        self.publish = publish or self.publish

        super().__init__(**kwargs)

    def send_message(self, data: Any, priority: int, wait_if_overflow: int = 10):
        self.messages_queue.put((data, priority))
        while self.messages_queue.qsize() > wait_if_overflow:
            time.sleep(0.01)

    def run(self, **kwargs):
        producer = self.producer
        while True:
            self.publish(producer)

    def publish(self, producer: Producer):
        data, priority = self.messages_queue.get()

        producer.publish(
            body=data,
            routing_key=self.queue_name,  # имя очереди куда отправляем
            correlation_id=uuid4().hex,
            priority=priority,
            exchange=self.exchange,
            serializer="json",
            retry=True,
            retry_policy={
                "interval_start": 0,
                "interval_step": 1,
                "interval_max": 5,
                "max_retries": 3,
            },
            timeout=10,
        )
