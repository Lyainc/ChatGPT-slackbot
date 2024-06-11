import openai
import threading
import logging
from slack_bolt import App
from src.config.config import openai_api_keys, default_openai_api_key, slack_bot_token, slack_signing_secret
from slack_sdk.errors import SlackApiError

user_conversations = {}
user_conversations_lock = threading.Lock()

app = App(token=slack_bot_token, signing_secret=slack_signing_secret)

def get_openai_response(user_id, thread_ts, model_name):
    try:
        api_key = openai_api_keys.get(user_id)
        
        if api_key:
            openai_client = openai.OpenAI(api_key=api_key)
            masked_api_key = '-'.join(api_key.split('-')[:3])
            logging.info(f"Using OpenAI API Key(Masked): {masked_api_key}...")
            
            with user_conversations_lock:
                messages = user_conversations.get(user_id, {}).get(thread_ts)
                if not messages:
                    raise ValueError("No messages found for the specified thread")
                
                completion = openai_client.chat.completions.create(
                    model=model_name,
                    messages=messages
                )
            return completion.choices[0].message.content.strip()
        else:
            logging.error("Unauthorized user access: No API key found for user", exc_info=True)
            return "Unauthorized user access. Please check your API key."
    except openai.RateLimitError:
        logging.error("Rate limit exceeded:", exc_info=True)
        return "Server rate limit exceeded. Please try again later."
    except Exception as e:
        logging.error("Error generating OpenAI response:", exc_info=True)
        return "현재 서비스가 원활하지 않습니다. 담당자에게 문의해주세요."

def check_openai_and_slack_api():
    """
    OpenAI API 및 Slack API의 유효성을 검사하고 각각의 상태를 반환합니다.
    """
    # OpenAI API 유효성 검사
    openai_status = "OpenAI API is operational."
    try:
        openai_client = openai.OpenAI(api_key=default_openai_api_key)
        models = openai_client.models.list()  # 단순 헬스 체크 요청 (예: 모델 목록 가져오기)
        if "error" in models:
            openai_status = "OpenAI API is not operational."
    except Exception as e:
        logging.error("Error testing OpenAI API", exc_info=True)
        openai_status = "OpenAI API is not operational."

    # Slack API 유효성 검사
    slack_status = "Slack API is operational."
    try:
        auth_response = app.client.auth_test()
        if not auth_response["ok"]:
            slack_status = f"Slack API is not operational: {auth_response['error']}"
    except Exception as e:
        logging.error("Error testing Slack API", exc_info=True)
        slack_status = "Slack API is not operational."

    return slack_status, openai_status

def healthcheck_response():
    """
    Slack과 OpenAI API의 헬스체크를 수행하고 결과를 반환합니다.
    """
    slack_status, openai_status = check_openai_and_slack_api()
    return f"*Health Check Results:*\n- {slack_status}\n- {openai_status}"