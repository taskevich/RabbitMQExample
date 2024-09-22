import time
from threading import Thread
from typing import Any

from base import AMQPWorkerProducerBase


class AMQPWorkerProducer(AMQPWorkerProducerBase):
    """
    Класс AMQPWorkerProducer предназначен для отправки сообщений в очереди сервисов
    """

    def run(self, num_handlers: int, handler_name: str, **kwargs):
        """
        Неблокирующий запуск одного или нескольких экземпляров для прослушивания очереди.
        :param num_handlers: Количество запускаемых обработчиков
        :param handler_name: Имя обработчика (для логов)
        :param kwargs: Дополнительные аргументы
        :return: Список потоков обработчиков
        """
        threads: list[Thread] = []

        def queue_handler(name, **kwargs):
            """ Поток обработки отправляемых сообщений в RabbitMQ. """
            worker = None

            while True:
                try:
                    worker = AMQPWorkerProducerBase(
                        self.messages_queue,
                        self.publish,
                        queue=self.queue_name,
                        exchange=self.exchange,
                        create_queue=self.create_queue
                    )
                    worker.run(**kwargs)
                except Exception as e:
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
                name=f'{handler_name} {i}',
                args=(handler_name,),
                kwargs=kwargs,
                daemon=True
            )
            thread.start()
            threads.append(thread)
        return threads

    def send_data_queue(self, data: Any, priority: int = 0):
        self.send_message(data, priority)
