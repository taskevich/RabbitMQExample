import time

from threading import Thread
from kombu import Message
from producer import AMQPWorkerProducer
from consumer import AMQPWorkerConsumer


def produce_messages():
    while True:
        data = {
            "message": "Hello, world!"
        }
        producer.send_data_queue(data=data)
        print(f"Send data: {data}")
        time.sleep(5)


def receive_messages(message: Message):
    print(f"Received: {message.body}")


producer = AMQPWorkerProducer(queue="msgp")
producer.run(5, "sender")
consumer = AMQPWorkerConsumer(queue="msgp", handler=receive_messages)
consumer.run(5, "receiver")


def main():
    thread = Thread(target=produce_messages, daemon=True)
    thread.start()
    thread.join()


if __name__ == "__main__":
    main()
