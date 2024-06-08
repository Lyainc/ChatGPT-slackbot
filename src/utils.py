import logging
import threading
import sys

from slack_bolt import App

# 타이머 인터벌 시간 (초 단위)
TIMEOUT_INTERVAL = 1800  # 30분


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
    # 초기 대기 시간 설정 (첫 메시지 대기 시간)
    delay_seconds = initial_delay_seconds

    # 초기 대기
    logging.info("첫 메시지 전송 전 5초 대기")
    stopped = stop_event.wait(delay_seconds)
    if stopped:
        return  # If stop_event is set during the wait, exit the function

    # 메시지 전송 및 대기 시간 증가
    while not stop_event.is_set():
        try:
            say(
                text=f"_ChatGPT가 답변을 생성하고 있습니다. 잠시만 기다려주세요._ \n>>> 대기시간: {delay_seconds} sec...",
                thread_ts=thread_ts,
                channel=channel_id
            )
            logging.info(f"Waiting message sent successfully (대기시간: {delay_seconds} sec)")
        except Exception as e:
            logging.error("Error sending waiting message", exc_info=True)

        delay_seconds += 5  # Increase delay by 5 seconds for the next iteration

        stopped = stop_event.wait(5)  # 메시지 전송 후 5초 대기
        if stopped:
            break  # If stop_event is set during the wait, exit the loop
        

# 타이머 시작 함수
def start_timer():
    timer = threading.Timer(TIMEOUT_INTERVAL, force_shutdown)
    timer.start()
    return timer

# 타이머 리셋 함수
def reset_timer(timer):
    timer.cancel()
    return start_timer()

# 강제 종료 함수
def force_shutdown(*args):
    logging.info("Force shutdown by function")
    sys.exit(0)

# 종료 명령어 함수
def handle_exit_command(user_name):
    logging.info(f"Force shutdown by user: {user_name}")
    sys.exit(0)