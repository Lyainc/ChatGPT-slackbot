import os
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from dotenv import load_dotenv
import openai

# .env 파일에서 환경 변수 로드
load_dotenv()

# 환경 변수에서 Slack 토큰 및 OpenAI API 키 가져오기
slack_bot_token = os.environ.get("SLACK_BOT_TOKEN")
slack_signing_secret = os.environ.get("SLACK_SIGNING_KEY")
openai_api_key = os.environ.get("OPEN_AI_API")

# OpenAI 클라이언트 초기화
openai.api_key = openai_api_key

# Slack 앱 초기화
try:
    app = App(token=slack_bot_token, signing_secret=slack_signing_secret)
except Exception as e:
    print("Error initializing Slack app:", e)
    exit()

# 사용자 상태 저장소
user_states = {}

@app.event("app_mention")
def handle_message(event, say):
    try:
        user_message = event["text"]
        user_id = event["user"]
        channel_id = event["channel"]

        # 봇 ID를 가져와서 질문 추출
        bot_id = f"<@{event['user']}>"
        question = user_message.replace(bot_id, "").strip()

        completion = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": question}
            ]
        )
        answer = completion.choices[0].message["content"].strip()

        response = say(text=answer, channel=channel_id, thread_ts=event["ts"], reply_broadcast=False)
        if response["ok"]:
            print("Reply posted successfully.")
        else:
            print(f"Failed to post reply: {response['error']}")

    except Exception as e:
        print("Unexpected error:", e)

# 앱 시작
if __name__ == "__main__":
    try:
        handler = SocketModeHandler(app, slack_bot_token)
        handler.start()
    except Exception as e:
        print("Error starting Slack app:", e)