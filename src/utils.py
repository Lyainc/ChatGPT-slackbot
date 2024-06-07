import sys
import time
import logging
from slack_bolt.async_app import AsyncApp
import asyncio

async def get_user_name(app: AsyncApp, user_id: str) -> str:
    try:
        user_info = await app.client.users_info(user=user_id)
        if user_info["ok"]:
            return user_info["user"]["real_name"]
        logging.error(f"Error fetching user info for user_id {user_id}: {user_info['error']}")
    except Exception as e:
        logging.error(f"Error retrieving user name for user_id {user_id}", exc_info=True)
    return None

async def send_waiting_message(say, thread_ts, channel_id, stop_event, delay_seconds=0):
    while not stop_event.is_set():
        delay_seconds += 5  # Increase delay by 5 seconds each loop
        await asyncio.sleep(5)
        if not stop_event.is_set():
            try:
                await say(text=f"_ChatGPT가 답변을 생성하고 있습니다. 잠시만 기다려주세요._ \n>>> 대기시간: {delay_seconds} sec...", thread_ts=thread_ts, channel=channel_id)
            except Exception as e:
                logging.error("Error sending waiting message", exc_info=True)                

# def safe_shutdown(user_name, user_id, start_time, stop_event):
#     # Log 정보 출력
#     logging.info(f"Session ended by user: {user_name} (ID: {user_id})")
    
#     # 실행 시간 계산 및 출력
#     if start_time:
#         total_runtime = time.time() - start_time
#         logging.info(f"Total session runtime: {total_runtime:.2f} seconds")
#     else:
#         logging.warning("Start time not initialized; session might not have started properly.")
    
#     # 스탑 이벤트 설정
#     if stop_event:
#         stop_event.set()
#     else:
#         logging.error("Stop event is not defined; there might be issues stopping waiting threads")
    
#     # 남아있는 스레드를 종료
#     current_thread = threading.current_thread()
#     for thread in threading.enumerate():
#         if thread is not current_thread:
#             thread.join()

#     logging.info("All threads have been successfully joined. Exiting the process with sys.exit(0)")
#     sys.exit(0)