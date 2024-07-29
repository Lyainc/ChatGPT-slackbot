import logging
from slack_bolt.app import App
from typing import Any, Callable
from config.config import *
from utils.utils import *
from slack.slack_events import *

app = App(token=slack_bot_token, signing_secret=slack_signing_secret)

@app.event("message")
def handle_message_event(event: dict[str, Any], say: Callable[..., None]):
    '''
    User가 입력한 메시지를 인식해 메시지의 내용에 따라 결과값을 반환합니다.
    '''
    
    logging.info("Received an event")  # Logging the event receipt
    
    try:
        if event.get("channel_type") != "im":
            logging.info("Event is not a direct message. Ignoring.")
            return
        
        global timer
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
            return
        
        logging.info(f"Received message: {user_message}")
        timer = reset_timer()
        
        if user_message.startswith("!대화시작"):
            user_message = user_message[len("!대화시작"):].strip()
            initial_message = say(
                text=f":robot_face: _안녕하세요 {user_name}님!_ \n:spinner: _대화 시작을 인식했습니다. ChatGPT에게 질문을 하고 있습니다._", 
                thread_ts=thread_ts, 
                mrkdwn=True, 
                icon_emoji=True
            )
            respond_to_user(user_id, user_name, thread_ts, user_message, say, prompt=basic_prompt)
            logging.info(f"Started conversation for user: {user_name} (ID: {user_id}) in thread: {thread_ts}")
            app.client.chat_update(
                channel=channel_id,
                ts=initial_message['ts'],
                text=f":robot_face: _답변이 완료되었습니다._",
            )
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

        elif user_message == "!슬랙봇종료":
            handle_exit_command(user_name)    

        elif user_message == "!healthcheck":
            healthcheck_results = healthcheck_response()
            say(text=healthcheck_results, 
                thread_ts=thread_ts
            )   
            
        elif user_message.startswith("!메뉴추천") or user_message == "!메뉴추천":
            if user_message.startswith("!메뉴추천"):
                user_message = user_message[len("!메뉴추천"):].strip()
                
            initial_message = say(text=":spinner: _추천 메뉴를 선택하고 있습니다._", thread_ts=thread_ts, mrkdwn=True, icon_emoji=True) 
            logging.info(f"Fetched data from Notion")
            notion_cache = load_cache()["dcaf6463dc8b4dfbafa6eafe6ea3881c"]
            prompt = f"{notion_cache}\n 위 json에서 가져온 데이터를 바탕으로 사용자의 메시지에 맞춰서 가게를 세 곳 추천해줘. 만약 별도의 요청이 없다면 전체 데이터에서 랜덤으로 데이터를 추천해줘. 단 데이터베이스에 없는 대답을 추측성으로 하면 절대 안돼."
            
            respond_to_user(user_id, user_name, thread_ts, user_message, say, prompt)
            app.client.chat_update(
                channel=channel_id,
                ts=initial_message['ts'],
                text=f":robot_face: _답변이 완료되었습니다._",
            )
            
        elif user_message.startswith("!숨고") or user_message == "!숨고":
            if user_message.startswith("!숨고"):
                user_message = user_message[len("!숨고"):].strip()
                
            initial_message = say(text=":spinner: _Soomgo Notion을 확인하고 있습니다._", thread_ts=thread_ts, mrkdwn=True, icon_emoji=True) 
            logging.info(f"Fetched data from Notion")
            notion_cache = {key: value for key, value in load_summarized_cache().items() if key != "dcaf6463dc8b4dfbafa6eafe6ea3881c"}
            prompt = f"{notion_cache}\n 위 json에서 가져온 데이터를 바탕으로 사용자의 메시지에 맞춰서 친절하게 설명해줘. 네가 이해했을때 추가로 필요한 정보가 있다면 데이터를 기반으로 함께 이야기해줘. 단 데이터에 없는 대답을 추측성으로 하면 절대 안돼."
            
            respond_to_user(user_id, user_name, thread_ts, user_message, say, prompt)
            app.client.chat_update(
                channel=channel_id,
                ts=initial_message['ts'],
                text=f":robot_face: _답변이 완료되었습니다._",
            )
            
        elif "text" in event and user_message.startswith("!대화삭제"):
            delete_thread_messages(channel_id, thread_ts)

        elif "thread_ts" in event and user_message not in ["!슬랙봇종료", "!healthcheck", "!대화종료", "!대화시작", "!대화인식", "!메뉴추천", "!숨고", "!대화삭제"]:
            initial_message = say(text=":spinner: _이어지는 질문을 인식했습니다. ChatGPT에게 질문을 하고 있습니다._", thread_ts=thread_ts, mrkdwn=True, icon_emoji=True)   
            respond_to_user(user_id, user_name, thread_ts, user_message, say, prompt=basic_prompt)
            app.client.chat_update(
                channel=channel_id,
                ts=initial_message['ts'],
                text=f":robot_face: _답변이 완료되었습니다._",
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