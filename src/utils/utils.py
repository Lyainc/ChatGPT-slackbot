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
    
    progress_steps = ["[>_________]", "[_>________]", "[__>_______]", "[___>______]", "[____>_____]", "[_____>____]", "[______>___]", "[_______>__]", "[________>_]", "[_________>]"]
    progress_index = 0

    # 처음으로 메시지를 보낸 후 메시지 타임스탬프를 저장합니다.
    try:
        progress_bar = progress_steps[progress_index]
        response = say(
            text=f":robot_face: {progress_bar} _ChatGPT가 답변을 생성하고 있습니다. 잠시만 기다려주세요._",
            thread_ts=thread_ts,
            channel=channel_id,
            mrkdwn=True, 
            icon_emoji=True,            
        )
        message_ts = response['ts']  # 메시지의 타임스탬프를 저장
        logging.info(f"Initial waiting message sent successfully")
    except Exception as e:
        logging.error("Error sending initial waiting message", exc_info=True)
        return

    # 메시지 수정
    while not stop_event.is_set():
        delay_seconds += 2  # 2초 간격으로 변경
        progress_index = (progress_index + 1) % len(progress_steps)
        stopped = stop_event.wait(2)
        if stopped:
            # 마지막 메시지 발송
            client.chat_update(
                channel=channel_id,
                ts=message_ts,
                text=f":robot_face: [>>>>>>>>>>] _답변이 완료되었습니다._",
            )
            break

        try:
            progress_bar = progress_steps[progress_index]
            # 2초 간격으로 메시지를 수정
            client.chat_update(
                channel=channel_id,
                ts=message_ts,
                text=f":robot_face: {progress_bar} _ChatGPT가 답변을 생성하고 있습니다. 잠시만 기다려주세요._",
            )
        except Exception as e:
            logging.error("Error updating waiting message", exc_info=True)

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