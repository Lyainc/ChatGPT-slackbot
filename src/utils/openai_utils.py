import openai
import threading
import logging
from slack_bolt import App
from config.config import *

user_conversations = {}
user_conversations_lock = threading.Lock()

app = App(token=slack_bot_token, signing_secret=slack_signing_secret)

def calculate_token_per_price(question_token: int, answer_token: int, model_name: str) -> float:
    """
    토큰 당 가격을 계산합니다.
    """
    total_price = 0
    try:
        if model_name == "gpt-4o-mini-2024-07-18":
            total_price = question_token * 0.00015 / 1000 + answer_token * 0.0006 / 1000
    except Exception as e:
            logging.error(f"Model is not vaild : {e}", exc_info=True)
            total_price = 0
    return total_price
   
def get_openai_response(user_id: str, thread_ts: str, model_name: str, question: str) -> dict:
    """
    OpenAI API를 사용해 data를 가져옵니다.
    """
    try:
        api_key = openai_api_keys.get(user_id)
        
        if api_key:
            openai_client = openai.OpenAI(api_key=api_key)
            masked_api_key = '-'.join(api_key.split('-')[:3])
            logging.info(f"Using OpenAI API Key(Masked): {masked_api_key}...")
            
            with user_conversations_lock:
                
                messages = user_conversations.setdefault(user_id, {}).setdefault(thread_ts, [])
                logging.info(f"Sending message to API: {messages}...")
                completion = openai_client.chat.completions.create(
                    model=model_name,
                    messages=messages,
                    user=user_id,
                    temperature=1,
                    frequency_penalty=0.1
                )
            
            answer = completion.choices[0].message.content.strip()
            prompt_tokens, completion_tokens = completion.usage.prompt_tokens, completion.usage.completion_tokens
            
            if prompt_tokens + completion_tokens > 5000 and not "카토멘" or "숨고팀" in messages:
                messages.append({"role": "user", "content": "전체 대화 내용을 기존 분량에서 1/3정도로 최대한 상세하게 요약해줘. 중간에 코드가 있다면 모든 코드가 요약에 포함될 필요는 없지만 요약을 위해 반드시 필요하다면 코드 조각은 요약문에 포함해도 좋아"})
                summary_completion = openai_client.chat.completions.create(
                    model=model_name,
                    messages=messages,
                    user=user_id,
                    temperature=1,
                    frequency_penalty=0.1
                )
            
                summary = summary_completion.choices[0].message.content.strip()
                messages.clear()
                messages.append({"role": "system", "content": basic_prompt})
                messages.append({"role": "assistant", "content": summary})
                messages.append({"role": "user", "content": question})
                
            messages.append({"role": "assistant", "content": answer})

            user_conversations[user_id][thread_ts] = messages

            response = {
                "answer": answer,
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens
            }
            
            return response
            
        else:
            logging.error("Unauthorized user access: No API key found for user", exc_info=True)
            return "Unauthorized user access. Please check your API key."
    except openai.RateLimitError:
        logging.error("Rate limit exceeded:", exc_info=True)
        return "Server rate limit exceeded. Please try again later."
    except Exception as e:
        logging.error("Error generating OpenAI response:", exc_info=True)
        return "현재 서비스가 원활하지 않습니다. 담당자에게 문의해주세요."
    
def split_message_into_blocks(message: str, max_length=3000) -> list:
    '''
    반환된 메시지의 길이가 일정 길이 이상인 경우 문맥 단위로 자릅니다.
    '''
    paragraphs = message.split('\n\n')
    blocks = []
    current_block = ""

    for paragraph in paragraphs:
        if len(current_block) + len(paragraph) + 2 <= max_length:
            if current_block:
                current_block += '\n\n' + paragraph
            else:
                current_block = paragraph
        else:
            blocks.append(current_block)
            current_block = paragraph

    if current_block:
        blocks.append(current_block)
    
    return blocks