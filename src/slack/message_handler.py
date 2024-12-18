import logging
from slack_bolt.app import App
from typing import Any, Callable
from config.config import slack_bot_token, slack_signing_secret, basic_prompt, notion_prompt_template, complex_model, advanced_model
from utils.utils import get_user_name, healthcheck_response
from utils.openai_utils import user_conversations, user_conversations_lock
from slack.slack_events import respond_to_user, recognize_conversation, delete_thread_messages
from utils.cache import load_summarized_cache

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

    try:
        user_message = event["text"]
        user_id = event["user"]
        channel_id = event["channel"]
        thread_ts = event.get("thread_ts") or event["ts"]
        channel_type = event.get("channel_type")
        user_name = get_user_name(app, user_id)
        
        if channel_type in ["channel", "group"] and event["type"] != "app_mention":
            logging.info(f"Not eligible for response")
            return

        if "thread_ts" not in event:
                
            if "!healthcheck" in user_message:
                healthcheck_results = healthcheck_response()
                say(text=healthcheck_results, 
                    thread_ts=thread_ts, 
                    mrkdwn=True, 
                    icon_emoji=True
                )

            elif "!숨고" in user_message:
                logging.info(f"Received message: {user_message}")    
                initial_message = say(
                    text=":spinner: _Soomgo Notion을 확인하고 있습니다._", 
                    thread_ts=thread_ts, 
                    mrkdwn=True, 
                    icon_emoji=True
                ) 
                logging.info(f"Fetched data from Notion")
                
                notion_cache = list(load_summarized_cache().values())
                notion_prompt = f"{notion_cache}\n{notion_prompt_template}"
                
                respond_to_user(user_id, user_name, thread_ts, user_message, say, notion_prompt, advanced_model)
                update_finsh_message(channel_id, initial_message['ts'])
                
            
            elif "!o1" in user_message:
                logging.info(f"Received message: {user_message}")    
                initial_message = say(
                    text=":spinner: _o1-preview를 사용하여 ChatGPT에게 질문을 하고 있습니다._", 
                    thread_ts=thread_ts, 
                    mrkdwn=True, 
                    icon_emoji=True
                ) 
                logging.info(f"Received message(o1-preview): {user_message}")
                
                respond_to_user(user_id, user_name, thread_ts, user_message, say, basic_prompt, complex_model)
                update_finsh_message(channel_id, initial_message['ts'])   

            elif "text" in event and "!대화삭제" in user_message and user_id == "U024AL7PN0Y":
                delete_thread_messages(channel_id, thread_ts)
                
            else:
                logging.info(f"Received message: {user_message}")
                initial_message = say(
                    text=f":robot_face: _안녕하세요 {user_name}님!_ \n:spinner: _대화 시작을 인식했습니다. ChatGPT에게 질문을 하고 있습니다._", 
                    thread_ts=thread_ts, 
                    mrkdwn=True, 
                    icon_emoji=True
                )
                respond_to_user(user_id, user_name, thread_ts, user_message, say, basic_prompt, advanced_model)
                update_finsh_message(channel_id, initial_message['ts'])
                logging.info(f"Started conversation for user: {user_name} (ID: {user_id}) in thread: {thread_ts}")
            
        elif "thread_ts" in event:
            
            if "!대화인식" in user_message:
                say(":robot_face: _기존 대화 이력을 인식했습니다._", 
                    thread_ts=thread_ts
                )
                recognize_conversation(event)
                logging.info(f"Recognized thread history for user: {user_name} (ID: {user_id}) in thread: {thread_ts}")
                logging.info(f"Queue size: {len(user_conversations[user_id][thread_ts])}")                
                
            elif "!대화종료" in user_message:
                with user_conversations_lock:
                    if user_id in user_conversations and thread_ts in user_conversations[user_id]:
                        del user_conversations[user_id][thread_ts]
                    say(text=":robot_face: _대화를 종료합니다. 메모리에서 대화 이력이 삭제됩니다._", 
                        thread_ts=thread_ts, 
                        mrkdwn=True, 
                        icon_emoji=True
                    )
                    logging.info(f"Ended conversation for user: {user_name} (ID: {user_id}) in thread: {thread_ts}") 

            elif "!healthcheck" in user_message:
                healthcheck_results = healthcheck_response()
                say(text=healthcheck_results, 
                    thread_ts=thread_ts, 
                    mrkdwn=True, 
                    icon_emoji=True
                )
                
            elif "!숨고" in user_message:
                logging.info(f"Received message: {user_message}")    
                initial_message = say(
                    text=":spinner: _Soomgo Notion을 확인하고 있습니다._", 
                    thread_ts=thread_ts, 
                    mrkdwn=True, 
                    icon_emoji=True
                ) 
                logging.info(f"Fetched data from Notion")
                
                notion_cache = list(load_summarized_cache().values())
                notion_prompt = f"{notion_cache}\n{notion_prompt_template}"
                
                respond_to_user(user_id, user_name, thread_ts, user_message, say, notion_prompt, advanced_model)
                update_finsh_message(channel_id, initial_message['ts']) 

            elif "!대화삭제" in user_message:
                delete_thread_messages(channel_id, thread_ts)
                
            elif "!도움말" in user_message:
                say(text=f"""
                        _안녕하세요. {user_name}님! 숨고팀 챗봇입니다._\n\n_챗봇을 이용하시려면 명령어와 함께 질문을 입력해주세요._\n\n`!숨고` [사내 규정에 대한 질문] :arrow_right: `!숨고` 생일반차는 언제까지 쓰면 돼?\n`!메뉴추천` [숨고의 식탁/주변 맛집 추천 질문] :arrow_right: `!메뉴추천` 일식 먹고 싶어\n`!대화시작` [ChatGPT에게 자유로운 질문] :arrow_right: `!대화시작` 예가체프 커피에 대해 알려줘\n\n_DM에서의 두번째 질문부터는 명령어를 입력하지 않아도 주제에 맞게 자동으로 대화가 이어집니다._\n\n_DM이 아닌 채널의 쓰레드에서 사용할때는 모든 질문에 멘션(@SoomgoBot-ChatGPT)를 붙여야 질문으로 인식합니다._\n\n_대화를 끝내고 싶다면 쓰레드에서 `!대화종료`를, 이전 대화기록에 이어 대화하고 싶다면 쓰레드에서 `!대화인식`을 입력해주세요._
                        """, 
                    thread_ts=thread_ts, 
                    mrkdwn=True, 
                    icon_emoji=True
                )
                
            else:
                initial_message = say(
                    text=":spinner: _이어지는 대화를 인식했습니다. ChatGPT에게 질문을 하고 있습니다._", 
                    thread_ts=thread_ts, 
                    mrkdwn=True, 
                    icon_emoji=True
                    )
                logging.info(f"Received message: {user_message}")
                
                respond_to_user(user_id, user_name, thread_ts, user_message, say, basic_prompt, advanced_model)
                update_finsh_message(channel_id, initial_message['ts'])   

    except Exception as e:
        logging.error("Unexpected error:", exc_info=True)