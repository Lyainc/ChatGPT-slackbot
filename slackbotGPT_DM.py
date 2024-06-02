import logging
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from dotenv import load_dotenv
import os
from openai import OpenAI
from tokenizer import count_token_usage

# 로깅 설정
logging.basicConfig(level=logging.INFO)

# .env 파일에서 환경 변수 로드
load_dotenv()

# 환경 변수에서 Slack 토큰 및 OpenAI API 키 가져오기
slack_app_token = os.environ.get("SLACK_APP_TOKEN")
slack_bot_token = os.environ.get("SLACK_BOT_TOKEN")
slack_signing_secret = os.environ.get("SLACK_SIGNING_KEY")
openai_api_key = os.environ.get("OPEN_AI_API")

if not slack_app_token or not slack_bot_token or not slack_signing_secret or not openai_api_key:
    logging.error("환경 변수가 올바르게 설정되지 않았습니다.")
    exit(1)

# OpenAI 클라이언트 초기화
client = OpenAI(api_key=openai_api_key)

# Slack 앱 초기화
app = App(token=slack_bot_token, signing_secret=slack_signing_secret)

# 봇 토큰 유효성 검증
try:
    auth_response = app.client.auth_test()
    if not auth_response["ok"]:
        logging.error(f"Error during auth_test: {auth_response['error']}")
        exit(1)
    else:
        logging.info("Slack Bot Token is valid")
except Exception as e:
    logging.error("Error testing Slack Bot Token validity")
    logging.error(str(e))
    exit(1)

# 사용자 대화 히스토리를 저장할 딕셔너리
user_conversations = {}

def debug_log(message, event=None):
    if event:
        logging.info(f"{message}: {event}")
    else:
        logging.info(message)

@app.event("message")
def handle_dm(event, say):
    debug_log("Received an event", event)  # Logging the raw event
    
    try:
        # Only process the events that are direct messages
        if event.get("channel_type") != "im":
            debug_log("Event is not a direct message. Ignoring.")
            return
        
        user_message = event["text"]
        user_id = event["user"]
        channel_id = event["channel"]
        thread_ts = event.get("thread_ts") or event["ts"]

        debug_log(f"Received message: {user_message} from user: {user_id} in DM: {channel_id}")
        
        if user_message.startswith("//질문시작"):
            question = user_message.replace("//질문시작", "").strip()
            
            debug_log(f"Extracted question: {question}")
        
            if user_id not in user_conversations:
                user_conversations[user_id] = [
                    {"role": "system", "content": "You are a helpful assistant."}
                ]
            
            # 대화 히스토리에 사용자 메시지 추가
            user_conversations[user_id].append({"role": "user", "content": question})
            debug_log(f"User conversation updated: {user_conversations[user_id]}")
            say(text="질문을 인식했습니다.", thread_ts=thread_ts)
            
            # Get initial response from OpenAI
            model_name = "gpt-4o-2024-05-13"
            answer = get_openai_response(user_id, model_name)
            debug_log(f"Generated OpenAI answer: {answer}")
            say(text=answer, thread_ts=thread_ts)
            
        elif user_message =="//대화종료":
            if thread_ts in user_conversations:
                del user_conversations[thread_ts]
            say(text="대화를 종료합니다.", thread_ts=thread_ts, channel=channel_id)
            return
        
        elif "thread_ts" in event:  # Check if message is in a thread
            if user_id in user_conversations:
                user_conversations[user_id].append({"role": "user", "content": user_message})
                
                # Get response from OpenAI
                model_name = "gpt-4o-2024-05-13"
                answer = get_openai_response(user_id, model_name)
                debug_log(f"Generated OpenAI answer for thread: {answer}")
                say(text=answer, thread_ts=thread_ts)
                debug_log(f"Added user message to conversation: {user_message}")
        
    except Exception as e:
        logging.error("Unexpected error:", exc_info=True)

def get_openai_response(user_id, model_name):
    try:
        completion = client.chat.completions.create(
            model=model_name,
            messages=user_conversations[user_id]
        )
        answer = completion.choices[0].message.content.strip()
        
        # Count token usage
        question_tokens, answer_tokens = count_token_usage(
            user_conversations[user_id][-1]["content"], 
            answer, 
            model_name
        )
        token_usage_message = f"_질문에 사용된 토큰 수: {question_tokens}, 답변에 사용된 토큰 수: {answer_tokens}_"

        # 답변에 token_usage_message 추가 (개행 후 이탤릭체로)
        answer += f"\n\n{token_usage_message}"

        logging.info(f"Generated answer: {answer}")
        return answer
    except Exception as e:
        logging.error("Error generating OpenAI response:", exc_info=True)
        return "문제가 발생했습니다. 다시 시도해 주세요."

if __name__ == "__main__":
    try:
        handler = SocketModeHandler(app, app_token=slack_app_token)
        handler.start()
    except Exception as e:
        logging.error("Error starting Slack app:", exc_info=True)