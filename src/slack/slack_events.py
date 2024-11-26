import logging
import time
import re
from slack_bolt.app import App
from typing import Any
from utils.openai_utils import split_message_into_blocks, calculate_token_per_price, get_openai_response, user_conversations, user_conversations_lock
from config.config import slack_bot_token, slack_signing_secret, slack_user_token, advanced_model

app = App(token=slack_bot_token, signing_secret=slack_signing_secret)
user_app = App(token=slack_user_token, signing_secret=slack_signing_secret)

def respond_to_user(user_id: str, user_name: str, thread_ts: str, user_message: str, say, prompt: str, model) -> None:
    '''
    user에게 ChatGPT의 결과물을 반환합니다.
    '''
    
    with user_conversations_lock:
        if user_id not in user_conversations:
            user_conversations[user_id] = {}
        
        if thread_ts not in user_conversations[user_id]:
                user_conversations[user_id][thread_ts] = [
                {"role": "system", "content": prompt}
            ]
        
        user_conversations[user_id][thread_ts][0]["content"] = prompt
        user_conversations[user_id][thread_ts][0]["role"] = "system"
            
        user_conversations[user_id][thread_ts].append(
            {"role": "user", "content": user_message}
            )

    logging.info(f"Queued message for user: {user_name} (ID: {user_id}) in thread: {thread_ts}")
    logging.info(f"Queue size: {len(user_conversations[user_id][thread_ts])}")
    
    start_time = time.time()
    response = get_openai_response(user_id, thread_ts, model, user_message)
  
    answer = response["answer"]
    prompt_tokens = response["prompt_tokens"]
    completion_tokens = response["completion_tokens"]

    answer = answer.replace("- ", " - ")
    answer = answer.replace("###", ">")
    answer = re.sub(r'\[(.*?)\]\((.*?)\)', r'<\2|\1>', answer) 

    message_blocks = split_message_into_blocks(answer)
    
    end_time = time.time()
    elapsed_time_ms = (end_time - start_time) * 1000
    
    expected_price = calculate_token_per_price(prompt_tokens, completion_tokens, advanced_model)
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
                    "type": "context",
                    "elements": [
                        {
                            "type": "mrkdwn",
                            "text": f":warning: ChatGPT를 통한 답변은 실제 내용과 다르거나 부정확할 수 있어 100% 사실을 담보하지 않습니다. 중요한 내용이라면 반드시 별도의 방법을 사용해 사실 관계를 확인해주세요."
                        }
                    ]
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
        text=block,
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

def recognize_conversation(event: dict[str, Any]) -> None:
    '''
    thread의 대화 내용을 dictionary에 저장합니다.
    '''
    user_message = event["text"]
    user_id = event["user"]
    channel_id = event["channel"]
    thread_ts = event.get("thread_ts") or event["ts"]
    channel_type = event.get("channel_type")

    conversation_history = read_conversation_history(channel_id, thread_ts)
    
    def append_user_message(role: str, content: str) -> None:
        user_conversations[user_id][thread_ts].append({
            "role": role,
            "content": content
        })

    try:
        with user_conversations_lock:
        # 대화 딕셔너리 조회 및 생성
            if user_id not in user_conversations:
                user_conversations[user_id] = {}
            
            user_conversations[user_id][thread_ts] = []
            user_conversations[user_id][thread_ts].append({
                "role": "user",
                "content": user_message
            })
            
            for conversation_message in conversation_history:
                
                if (conversation_message["text"].startswith(":robot_face:") or 
                    conversation_message["text"].startswith(":spinner:") or 
                    ("<@U076EJQTPNC>" not in conversation_message["text"] and channel_type in ["channel", "group"])
                    ):
                    continue
                
                if conversation_message["user"] == "U076EJQTPNC" and conversation_message["blocks"]:
                    for block in conversation_message["blocks"]:
                        if block.get("type") == "section":
                            section_text = block["text"].get("text")
                            append_user_message("assistant", section_text)   
                    continue

                if (conversation_message["user"] != "U076EJQTPNC" and "<@U076EJQTPNC>" in conversation_message["text"]) or channel_type in ["im", "mpim"]:
                    conversation_message["text"] = conversation_message["text"].replace("<@U076EJQTPNC>", "")
                    append_user_message("user", conversation_message["text"])
              
    except Exception as e:
        logging.error("Unexpected error:", exc_info=True)

def delete_thread_messages(channel_id, thread_ts) -> None:
    '''
    thread의 대화 내용을 삭제합니다.
    '''
    try:
        # 스레드 메시지 히스토리 가져오기
        result = app.client.conversations_replies(channel=channel_id, ts=thread_ts)
        thread_messages = result["messages"]

        # 각 스레드 메시지 삭제
        for thread_message in reversed(thread_messages):
            ts = thread_message["ts"]
            user = thread_message["user"]
            text_summary = thread_message.get("text", "")[:30]  # 메시지 앞 30자 요약

            # 스레드 메시지 삭제 전에 로그 출력
            logging.info(f"Deleting thread message: {text_summary}")

            try:
                if user == "U076EJQTPNC":
                    # 봇이 만든 메시지 삭제
                    app.client.chat_delete(channel=channel_id, ts=ts)
                else:
                    # 사용자가 만든 메시지 삭제
                    user_app.client.chat_delete(channel=channel_id, ts=ts)
                logging.info(f"Deleted thread message with ts: {ts}")
            except Exception as e:
                logging.error(f"Error deleting thread message: {e.response['error']}")
                
            time.sleep(0.5)

    except Exception as e:
        logging.error(f"Error fetching thread history: {e.response['error']}")