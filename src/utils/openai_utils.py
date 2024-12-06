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
                    temperature=1,
                    frequency_penalty=0.1
                )
            
            answer = completion.choices[0].message.content.strip()
            prompt_tokens, completion_tokens = completion.usage.prompt_tokens, completion.usage.completion_tokens
            
            if prompt_tokens + completion_tokens > 5000 and not "카토멘" or "숨고팀" in messages:
                messages.append({
                    "role": "user", 
                    "content": """전체 대화 내용을 기존 분량에서 1/3정도로 최대한 상세하게 요약해줘. 
                    중간에 코드가 있다면 모든 코드가 요약에 포함될 필요는 없지만 요약을 위해 반드시 필요하다면 코드 조각은 요약문에 포함해도 좋아"""
                    })
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
    
# def split_message_into_blocks(message: str, max_length=3000) -> list:
#     '''
#     반환된 메시지의 길이가 일정 길이 이상인 경우 문맥 단위로 자릅니다.
#     '''
#     paragraphs = message.split('\n\n')
#     blocks = []
#     current_block = ""

#     for paragraph in paragraphs:
#         if len(current_block) + len(paragraph) + 2 <= max_length:
#             if current_block:
#                 current_block += '\n\n' + paragraph
#             else:
#                 current_block = paragraph
#         else:
#             blocks.append(current_block)
#             current_block = paragraph

#     if current_block:
#         blocks.append(current_block)
    
#     return blocks

def split_message_into_blocks(message: str, max_length=3000) -> list:
    '''
    긴 텍스트를 슬랙 메시지 형태로 가독성을 높여 문맥 및 줄 단위로 자릅니다.
    '''
    # 멀티라인 코드 블록 추출 (정규식으로 감쌈)
    
    code_block_pattern = re.compile(r'```.*?```', re.DOTALL)
    code_blocks = code_block_pattern.findall(message)
                                    
    # 임시 코드 블록 대체 문자열 삽입
    placeholders = []
    for i, code_block in enumerate(code_blocks):
        placeholder = f"<CODE_BLOCK_{i}>"
        placeholders.append(placeholder)
        message = message.replace(code_block, placeholder)

    # 문단 단위로 기본 텍스트 분리
    paragraphs = message.split('\n\n')
    blocks = []
    current_block = ""

    for paragraph in paragraphs:
        # 현재 단락이 멀티라인 코드 블록 placeholder인지 확인
        if any(placeholder in paragraph for placeholder in placeholders):
            # 코드 블록 자체가 너무 길다면 그대로 추가
            if len(paragraph) > max_length:
                blocks.append(paragraph)  # 하나의 독립적인 블록으로 간주
                continue

            # 현재 블록이 차 있으면 저장하고 새 블록 시작
            if current_block:
                blocks.append(current_block)
                current_block = ""

            blocks.append(paragraph)  # 코드 블록은 항상 독립적인 블록
            continue

        # 현재 단락을 추가하며 길이 체크
        if len(current_block) + len(paragraph) + 2 <= max_length:
            if current_block:
                current_block += "\n\n" + paragraph
            else:
                current_block = paragraph
        else:
            blocks.append(current_block)
            current_block = paragraph

    # 마지막 블록 추가
    if current_block:
        blocks.append(current_block)

    # Placeholder를 실제 코드 블록으로 복원
    for i, code_block in enumerate(code_blocks):
        blocks = [block.replace(f"<CODE_BLOCK_{i}>", code_block) for block in blocks]

    return blocks