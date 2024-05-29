import os
import openai
from state_management import initialize_user_state, update_last_activity, check_session_timeout
from commands import handle_message
from slack_bolt import App
from dotenv import load_dotenv
from slack_bolt.request import BoltRequest
from slack_bolt.response import BoltResponse
from pyngrok import ngrok

load_dotenv()
# from slack_bolt.adapter.aws_lambda import SlackRequestHandler
# 환경 변수에서 Slack 토큰 및 OpenAI API 키 가져오기
slack_bot_token = os.environ.get("SLACK_BOT_TOKEN")
slack_signing_secret = os.environ.get("SLACK_SIGNING_KEY")
openai_api_key = os.environ.get("OPEN_AI_API")

# Slack 앱 초기화
try:
    app = App(token=slack_bot_token, signing_secret=slack_signing_secret)
except Exception as e:
    print("Error initializing Slack app:", e)
    exit()
    
# ngrok으로 터널링하여 로컬 웹 서버 공개
ngrok_tunnel = ngrok.connect(8000)  # 웹 서버 포트(예: 3000)에 맞게 수정

# Slack 앱의 이벤트 구독 URL 업데이트
app.base_url = ngrok_tunnel.public_url

openai.api_key = openai_api_key


# 사용자 상태 저장소
user_states = {}

@app.message("")
def message_handler(message, say):
    user_id = message['user']
    user_message = message['text'].strip()
    
    # Initialize user state if not present
    initialize_user_state(user_id, user_states)
    update_last_activity(user_id, user_states)

    # Check session timeout
    if check_session_timeout(user_id, user_states):
        say("Session timed out due to inactivity. Starting a new session.")
        user_states.pop(user_id, None)
        return

    # Handle the user message
    try:
        handle_message(user_id, user_message, say, user_states)
    except Exception as e:
        print("Error handling message:", e)

# Challenge 요청 처리
@app.middleware
def handle_challenge_request(req: BoltRequest, resp: BoltResponse, next):
    if req.payload.get("type") == "url_verification":
        challenge = req.payload["challenge"]
        return resp(challenge)
    next()

if __name__ == "__main__":
    try:
        app.start(port=8000)  # Slack 앱 시작
    except Exception as e:
        print("Error starting Slack app:", e)

# # Lambda 핸들러 생성
# def lambda_handler(event, context):
#     slack_handler = SlackRequestHandler(app)
#     return slack_handler.handle(event, context)