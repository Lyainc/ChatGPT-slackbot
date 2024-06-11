import openai
import threading
import logging
from src.config.config import openai_api_keys

user_conversations = {}
user_conversations_lock = threading.Lock()

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