import time
import logging
from threading import Thread, Event
from slack_bolt.app import App

def get_user_name(app: App, user_id: str) -> str:
    try:
        user_info = app.client.users_info(user=user_id)
        if user_info["ok"]:
            return user_info["user"]["real_name"]
        logging.error(f"Error fetching user info for user_id {user_id}: {user_info['error']}")
    except Exception as e:
        logging.error(f"Error retrieving user name for user_id {user_id}", exc_info=True)
    return None

def send_waiting_message(say, thread_ts, channel_id, stop_event, delay_seconds):
    while not stop_event.is_set():
        try:
            say(
                text=f"_ChatGPT가 답변을 생성하고 있습니다. 잠시만 기다려주세요._ \n>>> 대기시간: {delay_seconds} sec...",
                thread_ts=thread_ts,
                channel=channel_id
            )
            delay_seconds += 5
            time.sleep(5)  # Wait for 5 seconds before sending the next message
        except Exception as e:
            logging.error("Error sending waiting message", exc_info=True)
            break