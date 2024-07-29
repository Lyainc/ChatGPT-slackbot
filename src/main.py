import logging
import asyncio

from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from typing import Any, Callable
from utils.logger import stop_listener
from slack.slack_events import *
from config.config import *
from slack.message_handler import handle_message_event
from utils.notion_utils import *

app = App(token=slack_bot_token, signing_secret=slack_signing_secret)

# 전역 데이터 캐시 딕셔너리 선언
notion_data_cache = {}

async def preload_notion_data():
   global notion_data_cache
   for page_id in NOTION_PAGE_IDS:
       try:
           if page_id == "dcaf6463dc8b4dfbafa6eafe6ea3881c":
               # 특정 UUID일 때 fetch_notion_restaurant_data 호출
               notion_data = await asyncio.get_event_loop().run_in_executor(None, fetch_notion_restaurant_data, page_id)
           else:
               # 나머지 UUID일 때 fetch_notion_page_data 호출
               notion_data = await asyncio.get_event_loop().run_in_executor(None, fetch_notion_page_data, page_id)
           notion_data_cache[page_id] = notion_data  # 데이터 캐시에 저장
           logging.info(f"Notion 데이터 {page_id} 초기화했습니다.")
       except Exception as e:
           logging.error(f"Notion 데이터 {page_id} 초기화 중 오류 발생: {e}")

@app.event("message")
def message_handler(event: dict[str, Any], say: Callable[..., None]):
    handle_message_event(event, say)

def start_bot():
    try:
        logging.info("Starting Slack bot")
        # 데이터 미리 로딩 시작
        asyncio.run(preload_notion_data())
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