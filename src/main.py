import logging

from slack_bolt.adapter.socket_mode import SocketModeHandler
from utils.logger import stop_listener
from config.config import slack_app_token
from slack.slack_events import app

def start_bot():
    try:
        logging.info("Starting Slack bot")
        handler = SocketModeHandler(app, app_token=slack_app_token)
        handler.start()
    except Exception as e:
        logging.error("Error starting Slack app:", exc_info=True)

if __name__ == "__main__":
    try:
        start_bot()
    except KeyboardInterrupt:
        logging.info("Bot stopped by user")
    except Exception as e:
        logging.error("Unhandled error:", exc_info=True)
    finally:
        stop_listener()
        logging.info("Bot shutdown complete")