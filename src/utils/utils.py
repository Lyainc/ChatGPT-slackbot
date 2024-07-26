import openai
import logging
import threading
import sys
import requests

from slack_bolt import App
from config.config import *

TIMEOUT_INTERVAL = 36000  # 10시간
timer = None

app = App(token=slack_bot_token, signing_secret=slack_signing_secret)

def get_user_name(app, user_id) -> str:
    try:
        user_info = app.client.users_info(user=user_id)
        if user_info["ok"]:
            return user_info["user"]["real_name"]
        logging.error(f"Error fetching user info for user_id {user_id}: {user_info['error']}")
    except Exception as e:
        logging.error(f"Error retrieving user name for user_id {user_id}", exc_info=True)
    return None

def validate_bot_token() -> str:
    """
    Slack Bot 토큰의 유효성을 검사합니다.
    """
    try:
        auth_response = app.client.auth_test()
        if not auth_response["ok"]:
            logging.error(f"Error during auth_test: {auth_response['error']}")
            exit(1)
        logging.info("Slack Bot Token is valid")
        return "Slack Bot Token is valid"
    except Exception as e:
        logging.error("Error testing Slack Bot Token validity", exc_info=True)
        return "Error testing Slack Bot Token validity"
    
def check_openai_api() -> str:
    """
    OpenAI API의 유효성을 검사하고 상태를 반환합니다.
    """
    
    openai_status = "OpenAI API is operational."
    try:
        openai_client = openai.OpenAI(api_key=default_openai_api_key)
        models = openai_client.models.list()
        if "error" in models:
            openai_status = "OpenAI API is not operational."
        else:
            logging.info("Healthcheck: OpenAI API is operational")
    except Exception as e:
        logging.error("Healthcheck: Error testing OpenAI API", exc_info=True)
        openai_status = "OpenAI API is not operational."

    return openai_status

def check_slack_api() -> str:
    """
    Slack API의 유효성을 검사하고 상태를 반환합니다.
    """

    slack_status = "Slack API is operational."
    try:
        auth_response = app.client.auth_test()
        if not auth_response["ok"]:
            slack_status = f"Slack API is not operational: {auth_response['error']}"
        else:
            logging.info(f"Healthcheck: Slack API is operational")
    except Exception as e:
        logging.error("Healthcheck: Error testing Slack API", exc_info=True)
        slack_status = "Slack API is not operational."

    return slack_status

def check_notion_api() -> str:
    """
    Notion API의 유효성을 검사하고 상태를 반환합니다.
    """

    notion_status = "Notion API is operational."
    url = "https://api.notion.com/v1/pages/00387c791e4243a19dba4258ee09a1e1"
    headers = {
        "Authorization": f"Bearer {notion_integration_token}", 
        "Notion-Version": "2022-06-28",  
        "Content-Type": "application/json"
    }

    try:
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            notion_status = f"Notion API is not operational: {response.json().get('message', 'Unknown error')}"
        else:
            logging.info("Healthcheck: Notion API is operational")
    except Exception as e:
        logging.error("Healthcheck: Error testing Notion API", exc_info=True)
        notion_status = "Notion API is not operational."

    return notion_status

def healthcheck_response() -> str:
    """
    Slack과 OpenAI, Notion API의 헬스체크를 수행하고 결과를 반환합니다.
    """
    slack_bot_token_status = validate_bot_token()
    openai_status = check_openai_api()
    slack_status = check_slack_api()
    notion_status = check_notion_api()
    
    return f"*Health Check Results:*\n- {slack_bot_token_status}\n- {openai_status}\n- {slack_status}\n- {notion_status}"

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