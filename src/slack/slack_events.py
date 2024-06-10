import logging
import time

from threading import Thread, Event
from slack_bolt.app import App
from src.config.config import prompt
from src.utils.tokenizer import count_token_usage, calculate_token_per_price, question_tokenizer
from src.utils.utils import get_user_name, send_waiting_message, reset_timer, timer, handle_exit_command
from src.utils.openai_utils import get_openai_response, user_conversations, user_conversations_lock
from src.config.config import slack_bot_token, slack_signing_secret

WAITING_MESSAGE_DELAY = 5  # seconds

# Initialize start_time at the beginning of the script
app = App(token=slack_bot_token, signing_secret=slack_signing_secret)

def validate_bot_token():
    """
    Slack Bot 토큰의 유효성을 검사합니다.
    """
    try:
        auth_response = app.client.auth_test()
        if not auth_response["ok"]:
            logging.error(f"Error during auth_test: {auth_response['error']}")
            exit(1)
        logging.info("Slack Bot Token is valid")
    except Exception as e:
        logging.error("Error testing Slack Bot Token validity", exc_info=True)
        exit(1)
        
validate_bot_token()

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
    
    say(text=answer, thread_ts=thread_ts)
    logging.info(f"Response sent: {answer}")
    logging.info(f"Elapsed time: {elapsed_time_ms:.2f} ms")
    logging.info(f"Question Token Count: {question_tokens} / Answer Token Count: {answer_tokens}")
    logging.info(f"Expected Price: $ {expected_price:.4f}")

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
            say(text="_사용자 이름을 가져오지 못했습니다._", thread_ts=thread_ts)
            return
        
        logging.info(f"Received message: {user_message}")
        timer = reset_timer()
        
        if user_message.startswith("//대화시작"):
            user_message = user_message.replace("//대화시작", "").strip()
            say(text="_대화 시작을 인식했습니다. ChatGPT에게 질문을 하고 있습니다._", thread_ts=thread_ts)
            respond_to_user(user_id, user_name, thread_ts, user_message, say, channel_id)

        elif user_message == "//대화종료":
            with user_conversations_lock:
                if user_id in user_conversations and thread_ts in user_conversations[user_id]:
                    del user_conversations[user_id][thread_ts]
                say(text="_대화를 종료합니다._", thread_ts=thread_ts)
                logging.info(f"Ended conversation for user: {user_name} (ID: {user_id}) in thread: {thread_ts}")

        elif user_message == "//슬랙봇종료":
            handle_exit_command(user_name)
            
        elif user_message == "//답변재생성":
            with user_conversations_lock:
                if user_id in user_conversations:
                    user_threads = user_conversations[user_id]
                    if thread_ts in user_threads:
                        messages = user_threads[thread_ts]
                        if len(messages) > 1:
                            last_user_message = messages[-2]["content"]
                            logging.info(f"Regenerating response for user: {user_name} with message: {last_user_message}")
                            say(text="_직전 질문에 대한 답변을 다시 생성합니다._", thread_ts=thread_ts)
                            respond_to_user(user_id, user_name, thread_ts, last_user_message, say, channel_id)
                        else:
                            logging.info("No previous messages found for regeneration.")
                            say(text="_이전에 입력한 질문이 없습니다._", thread_ts=thread_ts)
                    else:
                        logging.info("Thread timestamp not found in user conversations.")
                        say(text="_이전에 입력한 질문이 없습니다._", thread_ts=thread_ts)
                else:
                    logging.info("User ID not found in user conversations.")
                    say(text="_이전에 입력한 질문이 없습니다._", thread_ts=thread_ts)
        
        elif "thread_ts" in event:
            say(text="_이어지는 질문을 인식했습니다. ChatGPT에게 질문을 하고 있습니다._", thread_ts=thread_ts)   
            respond_to_user(user_id, user_name, thread_ts, user_message, say, channel_id)

    except Exception as e:
        logging.error("Unexpected error:", exc_info=True)