import logging
import threading
import sys

TIMEOUT_INTERVAL = 36000  # 10시간
timer = None

def get_user_name(app, user_id) -> str:
    try:
        user_info = app.client.users_info(user=user_id)
        if user_info["ok"]:
            return user_info["user"]["real_name"]
        logging.error(f"Error fetching user info for user_id {user_id}: {user_info['error']}")
    except Exception as e:
        logging.error(f"Error retrieving user name for user_id {user_id}", exc_info=True)
    return None

def start_timer():
    '''
    타이머를 시작합니다.
    '''
    global timer
    timer = threading.Timer(TIMEOUT_INTERVAL, force_shutdown)
    timer.start()
    return timer

def reset_timer():
    '''
    타이머를 리셋합니다.
    '''
    global timer
    if timer is not None:
        timer.cancel()
    return start_timer()

def force_shutdown(*args):
    '''
    봇을 강제종료합니다.
    '''
    logging.info("Force shutdown by function")
    sys.exit(0)

def handle_exit_command(user_name: str):
    '''
    command를 입력한 user name을 반환합니다.
    '''
    logging.info(f"Force shutdown by user: {user_name}")
    sys.exit(0)