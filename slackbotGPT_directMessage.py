import logging
import threading
import os
import time
import openai

from queue import Queue
from logging.handlers import QueueHandler, QueueListener
from multiprocessing import Queue
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from dotenv import load_dotenv
from openai import OpenAI
from tokenizer import count_token_usage

# Constants
WAITING_MESSAGE_DELAY = 5  # seconds

# 로그 큐 생성
log_queue = Queue()

# 기본 콘솔 핸들러 생성
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)  # 로그 레벨 설정
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)

# QueueListener 생성, 콘솔 핸들러 추가
queue_listener = QueueListener(log_queue, console_handler)

# 루트 로거 설정
root_logger = logging.getLogger()
root_logger.setLevel(logging.INFO)  # 로그 레벨 설정

# 기존의 모든 핸들러 제거 및 QueueHandler 추가
for handler in root_logger.handlers[:]:
    root_logger.removeHandler(handler)
queue_handler = QueueHandler(log_queue)
root_logger.addHandler(queue_handler)

# QueueListener 시작
queue_listener.start()

# .env 파일에서 환경 변수 로드
load_dotenv()

# 환경 변수에서 Slack 토큰 및 OpenAI API 키 가져오기
slack_app_token = os.environ.get("SLACK_APP_TOKEN")
slack_bot_token = os.environ.get("SLACK_BOT_TOKEN")
slack_signing_secret = os.environ.get("SLACK_SIGNING_KEY")

# OpenAI API 키를 저장할 딕셔너리 생성
openai_api_keys = {key.replace('OPEN_AI_API_', ''): value for key, value in os.environ.items() if key.startswith('OPEN_AI_API_')}
default_openai_api_key = openai_api_keys.get("DEFAULT")

# 환경 변수 확인
required_env_vars = [slack_app_token, slack_bot_token, slack_signing_secret, default_openai_api_key]
if not all(required_env_vars):
    logging.error("환경 변수가 올바르게 설정되지 않았습니다.")
    exit(1)

# OpenAI API 키 확인 및 로깅
for key, value in openai_api_keys.items():
    if not value:
        logging.error(f"OpenAI API 키 '{key}'가 설정되지 않았습니다.")
        exit(1)

# Slack 앱 초기화
app = App(token=slack_bot_token, signing_secret=slack_signing_secret)

# 봇 토큰 유효성 검증
def validate_bot_token():
    try:
        auth_response = app.client.auth_test()
        if not auth_response["ok"]:
            logging.error(f"Error during auth_test: {auth_response['error']}")
            exit(1)
        else:
            logging.info("Slack Bot Token is valid")
    except Exception as e:
        logging.error("Error testing Slack Bot Token validity", exc_info=True)
        exit(1)

validate_bot_token()

# 사용자 대화 히스토리를 저장할 딕셔너리
user_conversations = {}

def debug_log(message, event=None):
    if event:
        logging.debug(f"{message}: {event}")
    else:
        logging.debug(message)

def send_waiting_message(say, thread_ts, channel_id, stop_event):
    delay_seconds = 0
    while not stop_event.is_set():
        delay_seconds += WAITING_MESSAGE_DELAY
        stop_event.wait(WAITING_MESSAGE_DELAY)
        if not stop_event.is_set():
            say(text=f"ChatGPT가 답변을 열심히 만들고 있습니다. 잠시만 기다려주세요 ({delay_seconds}sec...)", thread_ts=thread_ts, channel=channel_id)

# 사용자 ID로부터 Slack 사용자 이름 가져오기
def get_user_name(user_id):
    try:
        user_info = app.client.users_info(user=user_id)
        if user_info["ok"]:
            user_name = user_info["user"]["real_name"]
            return user_name
        else:
            logging.error(f"Error fetching user info for user_id {user_id}: {user_info['error']}")
            return None
    except Exception as e:
        logging.error(f"Error retrieving user name for user_id {user_id}", exc_info=True)
        return None

# 유저 ID에 따른 OpenAI API 키 가져오기
def get_openai_api_key(user_id):
    return openai_api_keys.get(user_id, default_openai_api_key)

@app.event("message")
def handle_dm(event, say):
    logging.info("Received an event")  # Logging the event receipt
    try:
        # Only process the events that are direct messages
        if event.get("channel_type") != "im":
            logging.info("Event is not a direct message. Ignoring.")
            return

        user_message = event["text"]
        user_id = event["user"]
        channel_id = event["channel"]
        thread_ts = event.get("thread_ts") or event["ts"]
        user_name = get_user_name(user_id)

        if not user_name:
            say(text="사용자 이름을 가져오는 데 실패했습니다. 나중에 다시 시도해 주세요.", thread_ts=thread_ts)
            return

        logging.info(f"Received message: {user_message}")

        if user_message.startswith("//대화시작"):
            question = user_message.replace("//대화시작", "").strip()
            logging.info(f"Extracted question: {question}")
            say(text="질문을 인식했습니다. ChatGPT에게 질문하고 있습니다.", thread_ts=thread_ts)

            if user_id not in user_conversations:
                user_conversations[user_id] = {}

            if thread_ts not in user_conversations[user_id]:
                user_conversations[user_id][thread_ts] = [
                    {"role": "system", "content": "You are a helpful assistant."}
                ]

            # 대화 히스토리에 사용자 메시지 추가
            user_conversations[user_id][thread_ts].append({"role": "user", "content": question})

            logging.info(f"User conversation updated for user: {user_name} (ID: {user_id}) in thread: {thread_ts}")

            # 시간 측정 시작
            start_time = time.time()

            # 시작 대기 메시지 타이머
            stop_event = threading.Event()
            waiting_message_thread = threading.Thread(target=send_waiting_message, args=(say, thread_ts, channel_id, stop_event))
            waiting_message_thread.start()

            # Get initial response from OpenAI
            model_name = "gpt-4o-2024-05-13"
            answer = get_openai_response(user_id, thread_ts, model_name)

            # 시간 측정 종료
            end_time = time.time()
            elapsed_time_ms = (end_time - start_time) * 1000  # 시간 차이를 밀리초로 변환

            # 대기 메시지 타이머 종료
            stop_event.set()
            waiting_message_thread.join()

            # 답변과 시간 정보를 슬랙에 출력
            say(text=f"{answer}\n응답 시간: {elapsed_time_ms:.2f} ms", thread_ts=thread_ts)
            logging.info(f"Response sent: {answer} (Elapsed time: {elapsed_time_ms:.2f} ms)")

        elif user_message == "//대화종료":
            if user_id in user_conversations and thread_ts in user_conversations[user_id]:
                del user_conversations[user_id][thread_ts]
            say(text="대화를 종료합니다.", thread_ts=thread_ts)
            logging.info(f"Ended conversation for user: {user_name} (ID: {user_id}) in thread: {thread_ts}")

        elif user_message == "//대화계속":
            if user_id in user_conversations and thread_ts in user_conversations[user_id]:
                if len(user_conversations[user_id][thread_ts]) > 1:
                    last_messages = user_conversations[user_id][thread_ts][-2:]
                    last_messages_text = "\n".join([msg["content"] for msg in last_messages])
                    say(text=f"마지막 두 개의 대화:\n{last_messages_text}\n대화를 계속 진행합니다.", thread_ts=thread_ts)
                else:
                    say(text="이 쓰레드에서 저장된 대화가 없습니다.", thread_ts=thread_ts)
            else:
                say(text="이 쓰레드에서 저장된 대화가 없습니다.", thread_ts=thread_ts)

        elif "thread_ts" in event:  # Check if message is in a thread
            # Handle ordinary messages in a thread
            if user_id not in user_conversations:
                user_conversations[user_id] = {}
            if thread_ts not in user_conversations[user_id]:
                user_conversations[user_id][thread_ts] = [
                    {"role": "system", "content": "You are a helpful assistant."}
                ]
            user_conversations[user_id][thread_ts].append({"role": "user", "content": user_message})
            say(text="질문을 인식했습니다. ChatGPT에게 질문하고 있습니다.", thread_ts=thread_ts)
            
            logging.info(f"Queued message for user: {user_name} (ID: {user_id}) in thread: {thread_ts}")
            logging.info(f"Queue size: {len(user_conversations[user_id][thread_ts])}")

            # 시간 측정 시작
            start_time = time.time()

            # 시작 대기 메시지 타이머
            stop_event = threading.Event()
            waiting_message_thread = threading.Thread(target=send_waiting_message, args=(say, thread_ts, channel_id, stop_event))
            waiting_message_thread.start()

            # Get response from OpenAI
            model_name = "gpt-4o-2024-05-13"
            answer = get_openai_response(user_id, thread_ts, model_name)

            # 시간 측정 종료
            end_time = time.time()
            elapsed_time_ms = (end_time - start_time) * 1000  # 시간 차이를 밀리초로 변환

            # 대기 메시지 타이머 종료
            stop_event.set()
            waiting_message_thread.join()

            # 답변과 시간 정보를 슬랙에 출력
            say(text=f"{answer}\n응답 시간: {elapsed_time_ms:.2f} ms", thread_ts=thread_ts)
            logging.info(f"Response sent: \n\n{answer}\n\n--\n\n(Elapsed time: {elapsed_time_ms:.2f} ms)")

    except Exception as e:
        logging.error("Unexpected error:", exc_info=True)

def get_openai_response(user_id, thread_ts, model_name):
    try:
        
        # 유저별 OpenAI API 키 가져오기 및 클라이언트 초기화
        api_key = get_openai_api_key(user_id)
        openai_client = OpenAI(api_key=api_key)
        masked_api_key = '-'.join(api_key.split('-')[:3])
        
        # 로그에 요청을 보낸 API 키 마스킹 후 출력
        logging.info(f"Using OpenAI API Key(Masked): {masked_api_key}...")
        
        # Slack API로부터 User Name을 가져옵니다.
        user_name = get_user_name(user_id)

        if not user_name:
            raise Exception("User name could not be retrieved.")
        
        # 대화 내역 가져오기 및 로그 출력
        received_message = user_conversations[user_id][thread_ts][-1]["content"]

        completion = openai_client.chat.completions.create(
            model=model_name,
            messages=user_conversations[user_id][thread_ts],
            user=user_name  # 실제 사용자를 식별할 수 있도록 user_name 추가
        )

        answer = completion.choices[0].message.content.strip()

        # Count token usage
        question_tokens, answer_tokens = count_token_usage(
            user_conversations[user_id][thread_ts][-1]["content"],
            answer,
            model_name
        )

        token_usage_message = f"질문에 사용된 토큰 수: {question_tokens}, 답변에 사용된 토큰 수: {answer_tokens}"
        # 답변에 token_usage_message 추가 (개행 후 이탤릭체로)

        answer += f"\n\n{token_usage_message}"

        return answer
    
    except openai.RateLimitError as e:
        logging.error("Rate limit exceeded:", exc_info=True)
        return "서버 요청 한도 초과로 인해 잠시 후 다시 시도해 주세요."

    except Exception as e:
        logging.error("Error generating OpenAI response:", exc_info=True)
        return "문제가 발생했습니다. 다시 시도해 주세요."

if __name__ == "__main__":
    try:
        logging.info("Starting Slack bot")
        handler = SocketModeHandler(app, app_token=slack_app_token)
        handler.start()
    except Exception as e:
        logging.error("Error starting Slack app:", exc_info=True)