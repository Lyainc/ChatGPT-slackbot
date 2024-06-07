import logging
import sys
import os
import asyncio
from slack_bolt.adapter.socket_mode.async_handler import AsyncSocketModeHandler

from .logger import stop_listener
from .config import slack_app_token
from .slack_events import app

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

async def start_bot():
    try:
        logging.info("Starting Slack bot")
        handler = AsyncSocketModeHandler(app, app_token=slack_app_token)
        await handler.start_async()
    except Exception as e:
        logging.error("Error starting Slack app:", exc_info=True)

if __name__ == "__main__":
    try:
        asyncio.run(start_bot())
    except KeyboardInterrupt:
        logging.info("Bot stopped by user")
    except Exception as e:
        logging.error("Unhandled error:", exc_info=True)
    finally:
        stop_listener()
        logging.info("Bot shutdown complete")