import json
import os
import openai
from slack_bolt import App
from slack_bolt.adapter.aws_lambda import SlackRequestHandler

# 환경 변수에서 Slack 토큰 및 OpenAI API 키 가져오기
slack_bot_token = os.environ["SLACK_BOT_TOKEN"]
slack_signing_secret = os.environ["SLACK_SIGNING_SECRET"]
openai_api_key = os.environ["OPENAI_API_KEY"]

# Slack 앱 초기화
app = App(token=slack_bot_token, signing_secret=slack_signing_secret)
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
    handle_message(user_id, user_message, say, user_states)

# Lambda 핸들러 생성
def lambda_handler(event, context):
    slack_handler = SlackRequestHandler(app)
    return slack_handler.handle(event, context)
