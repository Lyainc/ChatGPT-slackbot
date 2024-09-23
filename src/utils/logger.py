import logging
from queue import Queue as ThreadQueue
from logging.handlers import QueueHandler, QueueListener

# Create log queue
log_queue = ThreadQueue()

# Create console handler
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)  # Fix: Corrected logging level setting
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)

# Create QueueListener and add console handler
queue_listener = QueueListener(log_queue, console_handler)

# Configure root logger
root_logger = logging.getLogger()
root_logger.setLevel(logging.INFO)  # Fix: Corrected logging level setting

file_handler = logging.FileHandler('heartbeat.log')
file_handler.setLevel(logging.INFO)

# Remove any existing handlers from the root logger
for handler in root_logger.handlers[:]:
    root_logger.removeHandler(handler)

# Add QueueHandler to root logger
queue_handler = QueueHandler(log_queue)
root_logger.addHandler(queue_handler)

file_handler.setFormatter(formatter)

# Start QueueListener
queue_listener.start()

def stop_listener():
    '''
    logging listener를 중지합니다.
    '''
    logging.info("Shutting down QueueListener")
    queue_listener.stop()