import logging
import asyncio
import json

from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from utils.logger import stop_listener
from utils.cache import summary_cache, load_summarized_cache, SUMMARY_CACHE_FILE
from config.config import slack_bot_token, slack_app_token, slack_signing_secret, NOTION_PAGE_IDS
from slack.message_handler import process_message
# from utils.notion_utils import fetch_notion_page_data, fetch_notion_restaurant_data
from utils.notion_utils import fetch_notion_page_data

app = App(token=slack_bot_token, signing_secret=slack_signing_secret)

# 전역 데이터 캐시 딕셔너리 선언
notion_data_cache = {}

async def preload_notion_data() -> None:
    global notion_data_cache
    summarized_data = {}
    
    for page_id in NOTION_PAGE_IDS:
        try:
            # if page_id == "dcaf6463dc8b4dfbafa6eafe6ea3881c":
            #    # 특정 UUID일 때 fetch_notion_restaurant_data 호출
            #    notion_data = await asyncio.get_event_loop().run_in_executor(None, fetch_notion_restaurant_data, page_id)
            # else:
            #    # 나머지 UUID일 때 fetch_notion_page_data 호출
            #    notion_data = await asyncio.get_event_loop().run_in_executor(None, fetch_notion_page_data, page_id)
            
            notion_data = await asyncio.get_event_loop().run_in_executor(None, fetch_notion_page_data, page_id)
            notion_data_cache[page_id] = notion_data  # 데이터 캐시에 저장
            logging.info(f"Notion 데이터 {page_id} 초기화했습니다.")
        except Exception as e:
            logging.error(f"Notion 데이터 {page_id} 초기화 중 오류 발생: {e}")

    if load_summarized_cache():
        logging.info("Summarized data is already cached. Skipping caching.")
        return
    else:
        summarized_data = summary_cache()
        with open(SUMMARY_CACHE_FILE, 'w', encoding='utf-8') as f:
            json.dump(summarized_data, f, ensure_ascii=False, indent=4)
            
            
@app.event("message")
def handle_message_event(event, say):
    # 메시지가 멘션을 포함하지 않는 경우만 처리
    if "text" in event and f"<@U076EJQTPNC>" not in event["text"] and event.get("channel_type") not in ["channel", "group"]:
        process_message(event, say)

@app.event("app_mention")
def handle_app_mention_event(event, say):
    # 멘션된 경우 메시지 처리
    process_message(event, say)
    
@app.event("member_joined_channel")
def handle_member_joined_channel_events(event, say):
    if event["user"] == "U076EJQTPNC":
        say(
            text=f"""
                _안녕하세요! 숨고팀 챗봇입니다._\n\n_챗봇을 이용하시려면 명령어와 함께 질문을 입력해주세요._\n\n`!숨고` [사내 규정에 대한 질문] :arrow_right: `!숨고` 생일반차는 언제까지 쓰면 돼?\n`!메뉴추천` [숨고의 식탁/주변 맛집 추천 질문] :arrow_right: `!메뉴추천` 일식 먹고 싶어\n`!대화시작` [ChatGPT에게 자유로운 질문] :arrow_right: `!대화시작` 예가체프 커피에 대해 알려줘\n\n_DM에서의 두번째 질문부터는 명령어를 입력하지 않아도 주제에 맞게 자동으로 대화가 이어집니다._\n\n_DM이 아닌 채널의 쓰레드에서 사용할때는 모든 질문에 멘션(@SoomgoBot-ChatGPT)를 붙여야 질문으로 인식합니다._\n\n_대화를 끝내고 싶다면 쓰레드에서 `!대화종료`를, 이전 대화기록에 이어 대화하고 싶다면 쓰레드에서 `!대화인식`을 입력해주세요._
                """, 
            mrkdwn=True, 
            icon_emoji=True
        )

def start_bot() -> None:
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