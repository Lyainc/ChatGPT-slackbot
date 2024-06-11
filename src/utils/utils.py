import logging
import threading
import sys
import time
from slack_bolt import App
from slack_sdk import WebClient
from config.config import slack_bot_token

TIMEOUT_INTERVAL = 36000  # 10시간
timer = None

def get_user_name(app: App, user_id: str) -> str:
    try:
        user_info = app.client.users_info(user=user_id)
        if user_info["ok"]:
            return user_info["user"]["real_name"]
        logging.error(f"Error fetching user info for user_id {user_id}: {user_info['error']}")
    except Exception as e:
        logging.error(f"Error retrieving user name for user_id {user_id}", exc_info=True)
    return None

def send_waiting_message(say, thread_ts, channel_id, stop_event, initial_delay_seconds):
    # Slack 클라이언트 초기화
    client = WebClient(token=slack_bot_token) 
    
    delay_seconds = initial_delay_seconds
    start_time = time.time()
    stopped = stop_event.wait(delay_seconds)
    
    if stopped:
        return
    
    # 처음으로 메시지를 보낸 후 메시지 타임스탬프를 저장합니다.
    try:
        response = say(
            text=f"_ChatGPT가 답변을 생성하고 있습니다. 잠시만 기다려주세요._ \n> 대기시간: {delay_seconds} sec...",
            thread_ts=thread_ts,
            channel=channel_id
        )
        message_ts = response['ts']  # 메세지의 타임스탬프를 저장
        logging.info(f"Waiting message sent successfully (대기시간: {delay_seconds} sec)")
    except Exception as e:
        logging.error("Error sending initial waiting message", exc_info=True)
        return
    
    # 메시지 수정
    while not stop_event.is_set():

        delay_seconds += 5
        stopped = stop_event.wait(5)
        if stopped:
            end_time = time.time()
            elapsed_time_ms = (end_time - start_time) * 1000
            # 마지막 메시지 발송.
            client.chat_update(
                channel=channel_id,
                ts=message_ts,
                text=f"_답변이 완료되었습니다._ \n> 총 소요시간: {elapsed_time_ms:.2f} ms"
            )
            break
        
        try:
            # 5초 간격 메시지를 수정합니다.
            client.chat_update(
                channel=channel_id,
                ts=message_ts,
                text=f"_ChatGPT가 답변을 생성하고 있습니다. 잠시만 기다려주세요._ \n> 대기시간: {delay_seconds} sec..."
            )
        except Exception as e:
            logging.error("Error updating waiting message", exc_info=True)



# def send_waiting_message(say, thread_ts, channel_id, stop_event, initial_delay_seconds):
#     delay_seconds = initial_delay_seconds
#     stopped = stop_event.wait(delay_seconds)
#     if stopped:
#         return
#     while not stop_event.is_set():
#         try:
#             say(text=f"_ChatGPT가 답변을 생성하고 있습니다. 잠시만 기다려주세요._ \n> 대기시간: {delay_seconds} sec...",
#                 thread_ts=thread_ts, channel=channel_id)
#             logging.info(f"Waiting message sent successfully (대기시간: {delay_seconds} sec)")
#         except Exception as e:
#             logging.error("Error sending waiting message", exc_info=True)
#         delay_seconds += 5
#         stopped = stop_event.wait(5)
#         if stopped:
#             break

# 타이머 시작 함수
def start_timer():
    global timer
    timer = threading.Timer(TIMEOUT_INTERVAL, force_shutdown)
    timer.start()
    return timer

# 타이머 리셋 함수
def reset_timer():
    global timer
    if timer is not None:
        timer.cancel()
    return start_timer()

# 강제 종료 함수
def force_shutdown(*args):
    logging.info("Force shutdown by function")
    sys.exit(0)

# 종료 명령 처리 함수
def handle_exit_command(user_name):
    logging.info(f"Force shutdown by user: {user_name}")
    sys.exit(0)