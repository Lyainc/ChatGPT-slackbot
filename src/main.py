import logging

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))


from slack_bolt.adapter.socket_mode import SocketModeHandler
from logger import stop_listener
from config import slack_app_token
from slack_events import app

if __name__ == "__main__":
    try:
        logging.info("Starting Slack bot")
        handler = SocketModeHandler(app, app_token=slack_app_token)
        handler.start()
    except Exception as e:
        logging.error("Error starting Slack app:", exc_info=True)
    finally:
        stop_listener()