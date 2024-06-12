import logging
import time

from threading import Thread, Event
from slack_bolt.app import App
from config.config import prompt
from utils.tokenizer import count_token_usage, calculate_token_per_price, question_tokenizer
from utils.utils import get_user_name, send_waiting_message, reset_timer, timer, handle_exit_command
from utils.openai_utils import get_openai_response, user_conversations, user_conversations_lock, healthcheck_response
from config.config import slack_bot_token, slack_signing_secret

WAITING_MESSAGE_DELAY = 5  # seconds

# Initialize start_time at the beginning of the script
app = App(token=slack_bot_token, signing_secret=slack_signing_secret)

def respond_to_user(user_id, user_name, thread_ts, user_message, say, channel_id):
    
    model_name = "gpt-4o-2024-05-13"
    
    with user_conversations_lock:
        if user_id not in user_conversations:
            user_conversations[user_id] = {}
        if thread_ts not in user_conversations[user_id]:
            user_conversations[user_id][thread_ts] = [
                {"role": "system", "content": prompt}
            ]
        
        user_conversations[user_id][thread_ts].append({"role": "user", "content": user_message})
        question = user_conversations[user_id][thread_ts][-1]["content"]
        tokenized_question = question_tokenizer(question, model_name)
        
    logging.info(f"Extracted question(Tokenized): {tokenized_question}")
    logging.info(f"Queued message for user: {user_name} (ID: {user_id}) in thread: {thread_ts}")
    logging.info(f"Queue size: {len(user_conversations[user_id][thread_ts])}")  
    
    start_time = time.time()
    stop_event = Event()
    waiting_thread = Thread(target=send_waiting_message, args=(say, thread_ts, channel_id, stop_event, WAITING_MESSAGE_DELAY))
    waiting_thread.start()
    
    answer = get_openai_response(user_id, thread_ts, model_name)
    
    stop_event.set()  # Signal the waiting thread to stop
    waiting_thread.join()
    
    end_time = time.time()
    elapsed_time_ms = (end_time - start_time) * 1000
    
    question_tokens, answer_tokens = count_token_usage(question, answer, model_name)
    expected_price = calculate_token_per_price(question_tokens, answer_tokens, model_name)
    
    say(text=f":soomgo_: {answer}", thread_ts=thread_ts, mrkdwn=True, icon_emoji=True)
    logging.info(f"Response sent: {answer}")
    logging.info(f"Elapsed time: {elapsed_time_ms:.2f} ms")
    logging.info(f"Question Token Count: {question_tokens} / Answer Token Count: {answer_tokens}")
    logging.info(f"Expected Price: $ {expected_price:.4f}")

def read_coversation_history(channel_id, thread_ts):
    conversation = app.client.conversations_replies(channel=channel_id, ts=thread_ts)
    messages = conversation.get("messages", [])
    return messages

def recognize_conversation(user_id, thread_ts, channel_id):
    conversation_history = read_coversation_history(channel_id, thread_ts)
    
    try:
        with user_conversations_lock:
        # 대화 딕셔너리 조회 및 생성
            if user_id not in user_conversations:
                user_conversations[user_id] = {}
            
            user_conversations[user_id][thread_ts] = []
            
            for message in conversation_history:
                
                if message["text"].startswith("//"):
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
            say(text=":bookmark: _사용자 이름을 가져오지 못했습니다._", thread_ts=thread_ts, mrkdwn=True, icon_emoji=True)
            return
        
        logging.info(f"Received message: {user_message}")
        timer = reset_timer()
        
        if user_message.startswith("//대화시작"):
            user_message = user_message.replace("//대화시작", "").strip()
            say(text=":bookmark: _대화 시작을 인식했습니다. ChatGPT에게 질문을 하고 있습니다._", thread_ts=thread_ts, mrkdwn=True, icon_emoji=True)
            respond_to_user(user_id, user_name, thread_ts, user_message, say, channel_id)
            logging.info(f"Started conversation for user: {user_name} (ID: {user_id}) in thread: {thread_ts}")

        elif user_message == "//대화인식":
            recognize_conversation(user_id, thread_ts, channel_id)
            say(":bookmark: _기존 대화 이력을 인식했습니다._", thread_ts=thread_ts)
            logging.info(f"Recognized thread history for user: {user_name} (ID: {user_id}) in thread: {thread_ts}")
            logging.info(f"Queue size: {len(user_conversations[user_id][thread_ts])}")                
            
        elif user_message == "//대화종료":
            with user_conversations_lock:
                if user_id in user_conversations and thread_ts in user_conversations[user_id]:
                    del user_conversations[user_id][thread_ts]
                say(text=":bookmark: _대화를 종료합니다._", thread_ts=thread_ts, mrkdwn=True, icon_emoji=True)
                logging.info(f"Ended conversation for user: {user_name} (ID: {user_id}) in thread: {thread_ts}")

        elif user_message == "//슬랙봇종료":
            handle_exit_command(user_name)    
            
        elif user_message == "//healthcheck":
            healthcheck_results = healthcheck_response()
            say(text=healthcheck_results, thread_ts=thread_ts)   
            
        elif "thread_ts" in event and user_message not in ["//슬랙봇종료", "//healthcheck", "//대화종료", "//대화시작", "//대화인식"]:
            say(text=":bookmark: _이어지는 질문을 인식했습니다. ChatGPT에게 질문을 하고 있습니다._", thread_ts=thread_ts, mrkdwn=True, icon_emoji=True)   
            respond_to_user(user_id, user_name, thread_ts, user_message, say, channel_id)
            
        else:
            logging.error("Cannot read conversation: ", exc_info=True)
            say(text=":bookmark: _ChatGPT가 대화를 인식하지 못했습니다._", thread_ts=thread_ts, mrkdwn=True, icon_emoji=True)

    except Exception as e:
        logging.error("Unexpected error:", exc_info=True)