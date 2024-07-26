import logging
import time
import re

from slack_bolt.app import App
from utils.notion_utils import *
from utils.utils import *
from utils.openai_utils import *
from config.config import *

app = App(token=slack_bot_token, signing_secret=slack_signing_secret)

def respond_to_user(user_id: str, user_name: str, thread_ts: str, user_message: str, say, prompt: str):
    '''
    user에게 ChatGPT의 결과물을 반환합니다.
    '''
    model = "gpt-4o-mini-2024-07-18"
    
    with user_conversations_lock:
        if user_id not in user_conversations:
            user_conversations[user_id] = {}
            
        if thread_ts not in user_conversations[user_id]:
            user_conversations[user_id][thread_ts] = [
                {"role": "system", "content": prompt}
            ]
                    
        user_conversations[user_id][thread_ts].append({"role": "user", "content": user_message})

    logging.info(f"Queued message for user: {user_name} (ID: {user_id}) in thread: {thread_ts}")
    logging.info(f"Queue size: {len(user_conversations[user_id][thread_ts])}")
    start_time = time.time()
    
    response = get_openai_response(user_id, thread_ts, model, user_message)
    
    answer = response["answer"]
    prompt_tokens = response["prompt_tokens"]
    completion_tokens = response["completion_tokens"]

    answer = answer.replace("**", "*")
    answer = answer.replace("- ", " - ")
    answer = answer.replace("###", ">")
    answer = re.sub(r'\[(.*?)\]\((.*?)\)', r'<\2|\1>', answer) 

    message_blocks = split_message_into_blocks(answer)
    
    end_time = time.time()
    elapsed_time_ms = (end_time - start_time) * 1000

    expected_price = calculate_token_per_price(prompt_tokens, completion_tokens, model)
    current_time = time.localtime()
    formatted_time = time.strftime("%Y년 %m월 %d일 %H시 %M분 %S초", current_time)

    for block in message_blocks:
        say(
            blocks=[
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": ":soomgo_:  생성된 답변",
                        "emoji": True
                    }
                },
                {
                    "type": "divider"
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": block
                    }
                },
                {
                    "type": "divider"
                },
                {
                    "type": "context",
                    "elements": [
                        {
                            "type": "mrkdwn",
                            "text": f":alarm_clock: _생성 시간(초) : {elapsed_time_ms / 1000:.2f} | {user_name}에 의해 {formatted_time}에 생성됨_"
                        }
                    ]
                },
            ],
        text='fallback text message',
        thread_ts=thread_ts, 
        icon_emoji=True
    )
        
    logging.info(f"Response sent: {answer}")
    logging.info(f"Elapsed time: {elapsed_time_ms:.2f} ms")
    logging.info(f"Prompt Token Count (From API): {prompt_tokens} / Completion Token Count (From API): {completion_tokens} / Expected Price(incl. Prompt Token): $ {expected_price:.4f}")

def read_conversation_history(channel_id: str, thread_ts: str) -> list:
    '''
    thread의 대화 내용을 읽습니다.
    '''
    conversation = app.client.conversations_replies(channel=channel_id, ts=thread_ts)
    messages = conversation.get("messages", [])
    return messages

def recognize_conversation(user_id: str, thread_ts: str, channel_id: str):
    '''
    thread의 대화 내용을 dictionary에 저장합니다.
    '''
    conversation_history = read_conversation_history(channel_id, thread_ts)
    
    try:
        with user_conversations_lock:
        # 대화 딕셔너리 조회 및 생성
            if user_id not in user_conversations:
                user_conversations[user_id] = {}
            
            user_conversations[user_id][thread_ts] = []
            
            for message in conversation_history:
                
                if message["text"].startswith("!대화시작"):
                    message["text"] = message["text"][len("!대화시작"):].strip()
                    
                    user_conversations[user_id][thread_ts].append({
                        "role": "system",
                        "content": basic_prompt
                    })
                    
                    continue
                
                if message["text"].startswith("//대화시작"):
                    message["text"] = message["text"][len("//대화시작"):].strip()
                    
                    user_conversations[user_id][thread_ts].append({
                        "role": "system",
                        "content": basic_prompt
                    })
                    
                    continue
                
                if message["text"].startswith("!숨고"):
                    message["text"] = message["text"][len("!숨고"):].strip()
                    
                    notion_cache = {key: value for key, value in load_summarized_cache().items() if key != "dcaf6463dc8b4dfbafa6eafe6ea3881c"}
                    prompt = f"{notion_cache}\n 위 json에서 가져온 데이터를 바탕으로 사용자의 메시지에 맞춰서 친절하게 설명해줘. 네가 이해했을때 추가로 필요한 정보가 있다면 데이터를 기반으로 함께 이야기해줘. 단 데이터에 없는 대답을 추측성으로 하면 절대 안돼."
                    
                    user_conversations[user_id][thread_ts].append({
                        "role": "system",
                        "content": prompt
                    })
                    
                    continue
                
                if message["text"].startswith("!메뉴추천"):
                    message["text"] = message["text"][len("!메뉴추천"):].strip()
        
                    notion_cache = load_cache()["dcaf6463dc8b4dfbafa6eafe6ea3881c"]
                    prompt = f"{notion_cache}\n 위 json에서 가져온 데이터를 바탕으로 사용자의 메시지에 맞춰서 가게를 세 곳 추천해줘. 만약 별도의 요청이 없다면 전체 데이터에서 랜덤으로 데이터를 추천해줘. 데이터베이스에 없는 대답을 추측성으로 하면 절대 안돼."

                    user_conversations[user_id][thread_ts].append({
                        "role": "system",
                        "content": prompt
                    })
                    
                    continue
                
                if message["text"].startswith(":robot_face:") or message["text"].startswith(":spinner:") or message["text"].startswith("//") or message["text"].startswith("!"):
                    continue
                
                if message["user"] == user_id:
                    role = "user"
                else:
                    role = "assistant"
                
                user_conversations[user_id][thread_ts].append({
                    "role": role,
                    "content": message["blocks"][2]["text"]["text"]
                })
                
            
    except Exception as e:
        logging.error("Unexpected error:", exc_info=True)