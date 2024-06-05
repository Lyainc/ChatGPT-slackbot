import sys
import time
import logging
from slack_bolt import App
from datetime
import threading


def get_user_name(app: App, user_id: str) -> str:
    try:
        user_info = app.client.users_info(user=user_id)
        if user_info["ok"]:
            return user_info["user"]["real_name"]
        logging.error(f"Error fetching user info for user_id {user_id}: {user_info['error']}")
    except Exception as e:
        logging.error(f"Error retrieving user name for user_id {user_id}", exc_info=True)
    return None

def send_waiting_message(say, thread_ts, channel_id, stop_event, delay_seconds=0):
    while not stop_event.is_set():
        delay_seconds += 5  # Increase delay by 5 seconds each loop
        stop_event.wait(5)
        if not stop_event.is_set():
            try:
                say(text=f"*[INFO: ChatGPT가 답변을 생성하고 있습니다. 잠시만 기다려주세요.]* \n_>>> 대기시간: {delay_seconds} sec..._", thread_ts=thread_ts, channel=channel_id)
            except Exception as e:
                logging.error("Error sending waiting message", exc_info=True)
                
def safe_shutdown(user_name, user_id, start_time, stop_event):
    # 로그 정보를 출력하는 포맷 수정
    logging.info(f"Session ended by user: {user_name} (ID: {user_id})")

    if start_time:
        total_runtime = time.time() - start_time
        logging.info(f"Total session runtime: {total_runtime:.2f} seconds")
    else:
        logging.warning("Start time not initialized; session might not have started properly.")

    # Set the stop event to make sure any waiting thread is notified
    stop_event.set()

    # Join any remaining threads to ensure clean exit
    current_thread = threading.current_thread()
    for thread in threading.enumerate():
        if thread is not current_thread:
            thread.join()

    logging.info("All threads have been successfully joined. Exiting the process with sys.exit(0)")
    sys.exit(0)