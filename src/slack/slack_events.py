import logging
import time
import re

from slack_bolt.app import App
from utils.utils import *
from utils.openai_utils import *
from config.config import *

app = App(token=slack_bot_token, signing_secret=slack_signing_secret)

def respond_to_user(user_id, user_name, thread_ts, user_message, say, prompt):
    
    model_name = "gpt-4o-2024-05-13"
    
    with user_conversations_lock:
        if user_id not in user_conversations:
            user_conversations[user_id] = {}
            
        if thread_ts not in user_conversations[user_id]:
            user_conversations[user_id][thread_ts] = [
                {"role": "system", "content": prompt}
            ]
            
        user_conversations[user_id][thread_ts].append({"role": "user", "content": user_message})
    
    logging.info(f"Queued message for user: {user_name} (ID: {user_id}) in thread: {thread_ts}")
    logging.info(f"Queue size: {len(user_conversations[user_id][thread_ts])}")
    start_time = time.time()
    
    response = get_openai_response(user_id, thread_ts, model_name)
    
    answer = response["answer"]
    prompt_tokens = response["prompt_tokens"]
    completion_tokens = response["completion_tokens"]

    answer = answer.replace("**", "*")
    answer = answer.replace("- ", " - ")
    answer = answer.replace("###", ">")
    answer = re.sub(r'\[(.*?)\]\((.*?)\)', r'<\2|\1>', answer) 

    message_blocks = split_message_into_blocks(answer)
    
    end_time = time.time()
    elapsed_time_ms = (end_time - start_time) * 1000

    expected_price = calculate_token_per_price(prompt_tokens, completion_tokens, model_name)
    current_time = time.localtime()
    formatted_time = time.strftime("%Y년 %m월 %d일 %H시 %M분 %S초", current_time)
 
    for block in message_blocks:
        say(
            blocks=[
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": ":soomgo_:  생성된 답변",
                        "emoji": True
                    }
                },
                {
                    "type": "divider"
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": block
                    }
                },
                {
                    "type": "divider"
                },
                {
                    "type": "context",
                    "elements": [
                        {
                            "type": "mrkdwn",
                            "text": f":alarm_clock: _생성 시간(초) : {elapsed_time_ms / 1000:.2f} | {user_name}에 의해 {formatted_time}에 생성됨_"
                        }
                    ]
                },
            ],
        thread_ts=thread_ts, 
        icon_emoji=True
    )
        
    logging.info(f"Response sent: {answer}")
    logging.info(f"Elapsed time: {elapsed_time_ms:.2f} ms")
    logging.info(f"Prompt Token Count (From API): {prompt_tokens} / Completion Token Count (From API): {completion_tokens} / Expected Price(incl. Prompt Token): $ {expected_price:.4f}")

def read_conversation_history(channel_id, thread_ts):
    conversation = app.client.conversations_replies(channel=channel_id, ts=thread_ts)
    messages = conversation.get("messages", [])
    return messages

def recognize_conversation(user_id, thread_ts, channel_id):
    conversation_history = read_conversation_history(channel_id, thread_ts)
    
    try:
        with user_conversations_lock:
        # 대화 딕셔너리 조회 및 생성
            if user_id not in user_conversations:
                user_conversations[user_id] = {}
            
            user_conversations[user_id][thread_ts] = []
            
            for message in conversation_history:
                
                if message["text"].startswith("!대화시작"):
                    message["text"] = message["text"][len("!대화시작"):].strip()
                    continue
                
                if message["text"].startswith("//대화시작"):
                    message["text"] = message["text"][len("//대화시작"):].strip()
                    continue
                
                if message["text"].startswith(":robot_face:") or message["text"].startswith(":spinner:") or message["text"].startswith("//") or message["text"].startswith("!"):
                    continue
                
                if message["user"] == user_id:
                    role = "user"
                else:
                    role = "assistant" if message["user"] == "U076EJQTPNC" else "system"
                    
                user_conversations[user_id][thread_ts].append({
                    "role": role,
                    "content": message["text"]
                })
            
    except Exception as e:
        logging.error("Unexpected error:", exc_info=True)
    
        
@app.event("message")
def handle_message_event(event, say):
    
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
            
        elif "thread_ts" in event and user_message not in ["!슬랙봇종료", "!healthcheck", "!대화종료", "!대화시작", "!대화인식", "!cot"]:
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