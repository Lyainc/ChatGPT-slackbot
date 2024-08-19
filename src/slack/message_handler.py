import logging
from slack_bolt.app import App
from typing import Any, Callable
from config.config import slack_bot_token, slack_signing_secret, basic_prompt, notion_prompt_templete, menu_recommendation_prompt_templete
from utils.utils import get_user_name, healthcheck_response
from utils.openai_utils import user_conversations, user_conversations_lock
from slack.slack_events import respond_to_user, recognize_conversation, delete_thread_messages
from utils.cache import load_cache, load_summarized_cache

app = App(token=slack_bot_token, signing_secret=slack_signing_secret)

def process_message(event: dict[str, Any], say: Callable[..., None]) -> str:
    '''
    User가 입력한 메시지를 인식해 메시지의 내용에 따라 결과값을 반환합니다.
    '''
    def update_finsh_message(channel_id: str, message_ts: str) -> None:
        app.client.chat_update(
            channel=channel_id,
            ts=message_ts,
            text=f":robot_face: _답변이 완료되었습니다._",
        )
    
    logging.info("Received an event")
    
    try:
       
        if "text" not in event:
            logging.warning("No text found in the event. Processing with default response.")
            return
        
        user_message = event["text"]
        user_id = event["user"]
        channel_id = event["channel"]
        thread_ts = event.get("thread_ts") or event["ts"]
        user_name = get_user_name(app, user_id)

        if not user_name:
            say(
                text=":robot_face: _사용자 이름을 가져오지 못했습니다._", 
                thread_ts=thread_ts, 
                mrkdwn=True, 
                icon_emoji=True
            )
        
        logging.info(f"Received message: {user_message}")
        
        if "@U076EJQTPNC" in user_message:
            user_message = user_message.replace("<@U076EJQTPNC>", "")
    
        if user_message.startswith("!대화시작") or event["type"] == "app_mention":
            user_message = user_message.replace("!대화시작", "")
            initial_message = say(
                text=f":robot_face: _안녕하세요 {user_name}님!_ \n:spinner: _대화 시작을 인식했습니다. ChatGPT에게 질문을 하고 있습니다._", 
                thread_ts=thread_ts, 
                mrkdwn=True, 
                icon_emoji=True
            )
            respond_to_user(user_id, user_name, thread_ts, user_message, say, basic_prompt)
            logging.info(f"Started conversation for user: {user_name} (ID: {user_id}) in thread: {thread_ts}")
            update_finsh_message(channel_id, initial_message['ts'])

        elif user_message == "!대화인식":
            say(":robot_face: _기존 대화 이력을 인식했습니다._", 
                thread_ts=thread_ts
            )
            recognize_conversation(user_id, thread_ts, channel_id)
            logging.info(f"Recognized thread history for user: {user_name} (ID: {user_id}) in thread: {thread_ts}")
            logging.info(f"Queue size: {len(user_conversations[user_id][thread_ts])}")                
            
        elif user_message == "!대화종료":
            with user_conversations_lock:
                if user_id in user_conversations and thread_ts in user_conversations[user_id]:
                    del user_conversations[user_id][thread_ts]
                say(text=":robot_face: _대화를 종료합니다._", 
                    thread_ts=thread_ts, 
                    mrkdwn=True, 
                    icon_emoji=True
                )
                logging.info(f"Ended conversation for user: {user_name} (ID: {user_id}) in thread: {thread_ts}") 

        elif user_message == "!healthcheck":
            healthcheck_results = healthcheck_response()
            say(text=healthcheck_results, 
                thread_ts=thread_ts, 
                mrkdwn=True, 
                icon_emoji=True
            )
            
        elif user_message.startswith("!메뉴추천") or "!메뉴추천" in user_message:
            if user_message.startswith("!메뉴추천"):
                user_message = user_message[len("!메뉴추천"):].strip()
                
            initial_message = say(text=":spinner: _추천 메뉴를 선택하고 있습니다._", thread_ts=thread_ts, mrkdwn=True, icon_emoji=True) 
            logging.info(f"Fetched data from Notion")
            
            notion_cache = load_cache()["dcaf6463dc8b4dfbafa6eafe6ea3881c"]
            menu_recommendation_prompt = f"원본 데이터: \n```json{notion_cache}```\n{menu_recommendation_prompt_templete}"
            
            respond_to_user(user_id, user_name, thread_ts, user_message, say, menu_recommendation_prompt)
            update_finsh_message(channel_id, initial_message['ts'])
            
        elif user_message.startswith("!숨고") or "!숨고" in user_message:
            if user_message.startswith("!숨고"):
                user_message = user_message[len("!숨고"):].strip()
                
            initial_message = say(
                text=":spinner: _Soomgo Notion을 확인하고 있습니다._", 
                thread_ts=thread_ts, 
                mrkdwn=True, 
                icon_emoji=True
            ) 
            logging.info(f"Fetched data from Notion")
            
            notion_cache = list(load_summarized_cache().values())
            notion_prompt = f"{notion_cache}\n{notion_prompt_templete}"
            
            respond_to_user(user_id, user_name, thread_ts, user_message, say, notion_prompt)
            update_finsh_message(channel_id, initial_message['ts'])
            
        elif "text" in event and user_message.startswith("!대화삭제"):
            delete_thread_messages(channel_id, thread_ts)

        elif "thread_ts" in event and user_message not in ["!슬랙봇종료", "!healthcheck", "!대화시작", "!대화인식", "!대화삭제", "!숨고", "!메뉴추천", "!도움말"]:
            initial_message = say(
                text=":spinner: _이어지는 질문을 인식했습니다. ChatGPT에게 질문을 하고 있습니다._", 
                thread_ts=thread_ts, 
                mrkdwn=True, 
                icon_emoji=True
                )   
            respond_to_user(user_id, user_name, thread_ts, user_message, say, prompt="")
            update_finsh_message(channel_id, initial_message['ts'])
            
        elif "text" in event and "!도움말" in user_message:
            say(text=f"""
                    _안녕하세요. {user_name}님! 숨고팀 챗봇입니다._\n\n_챗봇을 이용하시려면 명령어와 함께 질문을 입력해주세요._\n\n`!숨고` [사내 규정에 대한 질문] :arrow_right: `!숨고` 생일반차는 언제까지 쓰면 돼?\n`!메뉴추천` [숨고의 식탁/주변 맛집 추천 질문] :arrow_right: `!메뉴추천` 일식 먹고 싶어\n`!대화시작` [ChatGPT에게 자유로운 질문] :arrow_right: `!대화시작` 예가체프 커피에 대해 알려줘\n\n_두번째 질문부터는 명령어를 입력하지 않아도 주제에 맞게 자동으로 대화가 이어집니다._\n\n_대화를 끝내고 싶다면 `!대화종료`를, 이전 대화기록에 이어 대화하고 싶다면 `!대화인식`을 입력해주세요._
                    """, 
                thread_ts=thread_ts, 
                mrkdwn=True, 
                icon_emoji=True
            )
                
        else:
            logging.error("Cannot read conversation: ", exc_info=True)
            say(text=":robot_face: _ChatGPT가 대화를 인식하지 못했습니다._", 
                thread_ts=thread_ts, 
                mrkdwn=True, 
                icon_emoji=True
            )

    except Exception as e:
        logging.error("Unexpected error:", exc_info=True)