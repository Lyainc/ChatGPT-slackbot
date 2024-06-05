import logging
from queue import Queue as ThreadQueue
from logging.handlers import QueueHandler, QueueListener

# Create log queue
log_queue = ThreadQueue()

# Create console handler
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)

# Create QueueListener and add console handler
queue_listener = QueueListener(log_queue, console_handler)

# Configure root logger
root_logger = logging.getLogger()
root_logger.setLevel(logging.INFO)
root_logger.handlers = [QueueHandler(log_queue)]

# 기존의 모든 핸들러 제거 및 QueueHandler 추가
for handler in root_logger.handlers[:]:
    root_logger.removeHandler(handler)
queue_handler = QueueHandler(log_queue)
root_logger.addHandler(queue_handler)

# QueueListener 시작
queue_listener.start()

def stop_listener():
    logging.info("Shutting down QueueListener")
    queue_listener.stop()