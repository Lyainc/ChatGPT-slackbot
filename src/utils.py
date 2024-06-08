import logging
from slack_bolt import App

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
    initial_delay_done = False  # 첫 메시지 전송 전 대기 완료 여부 체크

    while not stop_event.is_set():
        if not initial_delay_done:
            stop_event.wait(5)  # 첫 메시지 전송 전 5초 대기
            initial_delay_done = True

        delay_seconds += 5  # Increase delay by 5 seconds each loop
        if not stop_event.is_set():
            try:
                say(text=f"_ChatGPT가 답변을 생성하고 있습니다. 잠시만 기다려주세요._ \n>>> 대기시간: {delay_seconds} sec...", thread_ts=thread_ts, channel=channel_id)
            except Exception as e:
                logging.error("Error sending waiting message", exc_info=True)

        stop_event.wait(5)  # 메세지 전송 후 5초 대기