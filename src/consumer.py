import time

from threading import Thread
from base import AMQPWorkerConsumerBase


class AMQPWorkerConsumer(AMQPWorkerConsumerBase):
    def run(self, num_handlers: int, handler_name: str, **kwargs):
        threads: list[Thread] = []

        def queue_handler(name, **kwargs):
            worker = None

            while True:
                try:
                    print(f"Run queue consumer {self.queue_name}")
                    worker = AMQPWorkerConsumerBase(
                        handler=self.handler,
                        queue=self.queue_name,
                        exchange=self.exchange
                    )
                    worker.run(**kwargs)
                except Exception as ex:
                    print(f"Start consumer error: {ex}")
                    continue
                finally:
                    try:
                        worker.connection.close()
                    except Exception:
                        pass
                    time.sleep(30)

        for i in range(num_handlers):
            thread = Thread(
                target=queue_handler,
                name=f"{handler_name} {i}",
                args=(handler_name,),
                kwargs=kwargs,
                daemon=True
            )
            thread.start()
            threads.append(thread)
        return threads
