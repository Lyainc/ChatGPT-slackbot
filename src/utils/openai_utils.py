import openai
import threading
import logging
import re
from slack_bolt import App
from config.config import slack_bot_token, slack_signing_secret, default_openai_api_key, basic_prompt

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
        elif model_name == "gpt-4o-2024-11-20":
            total_price = question_token * 0.0025 / 1000 + answer_token * 0.01 / 1000
        elif model_name == "o1-preview-2024-09-12":
            total_price = question_token * 0.0150 / 1000 + answer_token * 0.06 / 1000
    except Exception as e:
            logging.error(f"Model is not vaild : {e}", exc_info=True)
            total_price = 0
    return total_price
   
def get_openai_response(user_id: str, thread_ts: str, model_name: str, question: str) -> dict:
    """
    OpenAI API를 사용해 data를 가져옵니다.
    """
    try:
        api_key = default_openai_api_key
        
        if api_key:
            openai_client = openai.OpenAI(api_key=api_key)
            
            with user_conversations_lock:
                messages = user_conversations.setdefault(user_id, {}).setdefault(thread_ts, [])
                logging.info(f"Sending message to API: {messages}...")
                completion = openai_client.chat.completions.create(
                    model=model_name,
                    messages=messages,
                    user=user_id,
                )
            
            answer = completion.choices[0].message.content.strip()
            print(answer)
            prompt_tokens, completion_tokens = completion.usage.prompt_tokens, completion.usage.completion_tokens
            
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

def get_openai_response(user_id: str, thread_ts: str, model_name: str, question: str) -> dict:
    """
    OpenAI API를 사용해 데이터를 가져옵니다.
    """
    try:
        api_key = default_openai_api_key
        
        if api_key:
            openai_client = openai.OpenAI(api_key=api_key)
            
            with user_conversations_lock:
                messages = user_conversations.setdefault(user_id, {}).setdefault(thread_ts, [])
                logging.info(f"Sending message to API: {messages}...")
                completion = openai_client.chat.completions.create(
                    model=model_name,
                    messages=messages,
                    user=user_id,
                )
            
            answer = completion.choices[0].message.content.strip()
            print(answer)
            prompt_tokens = completion.usage.prompt_tokens
            completion_tokens = completion.usage.completion_tokens
            
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
    반환된 메시지의 길이가 일정 길이 이상인 경우 문맥과 코드 블록을 고려하여 자릅니다.
    '''
    import re

    # 코드 블록을 식별하기 위한 정규식 패턴
    code_block_pattern = re.compile(r'```[\s\S]*?```', re.MULTILINE)

    # 현재 위치를 추적하기 위한 변수
    pos = 0
    segments = []

    # 메시지를 순회하며 코드 블록과 텍스트 블록으로 분할
    for match in code_block_pattern.finditer(message):
        start, end = match.span()
        # 코드 블록 이전의 텍스트 추가
        if start > pos:
            segments.append(message[pos:start])
        # 코드 블록 자체 추가
        segments.append(match.group())
        pos = end

    # 마지막 코드 블록 이후의 남은 텍스트 추가
    if pos < len(message):
        segments.append(message[pos:])

    # 블록을 저장할 리스트와 현재 블록 문자열 초기화
    blocks = []
    current_block = ''

    # 세그먼트를 순회하며 블록을 생성
    for segment in segments:
        segment = segment.strip()
        if not segment:
            continue  # 빈 세그먼트는 건너뜀

        if len(segment) > max_length:
            # 세그먼트가 최대 길이보다 길 경우 추가 분할 필요
            if segment.startswith('```') and segment.endswith('```'):
                # 코드 블록인 경우
                code_content = segment[3:-3].strip('\n')
                code_lines = code_content.split('\n')
                code_chunk = ''
                for line in code_lines:
                    if len('```\n' + code_chunk + line + '\n```') <= max_length:
                        code_chunk += line + '\n'
                    else:
                        if code_chunk.strip():
                            blocks.append('```\n' + code_chunk.strip('\n') + '\n```')
                        code_chunk = line + '\n'
                if code_chunk.strip():
                    blocks.append('```\n' + code_chunk.strip('\n') + '\n```')
            else:
                # 텍스트 블록인 경우 문장 단위로 분할
                sentences = re.split('(?<=[.!?]) +', segment)
                for sentence in sentences:
                    if len(current_block + sentence) + 1 <= max_length:
                        current_block += sentence + ' '
                    else:
                        if current_block.strip():
                            blocks.append(current_block.strip())
                        current_block = sentence + ' '
                if current_block.strip():
                    blocks.append(current_block.strip())
                    current_block = ''
        else:
            if len(current_block + segment) + 1 <= max_length:
                current_block += segment + '\n'
            else:
                if current_block.strip():
                    blocks.append(current_block.strip())
                current_block = segment + '\n'

    # 마지막 블록 추가
    if current_block.strip():
        blocks.append(current_block.strip())

    return blocks