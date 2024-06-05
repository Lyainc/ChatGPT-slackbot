import openai
import threading
import logging
from openai import OpenAI

user_conversations = {}
user_conversations_lock = threading.Lock()

from .config import openai_api_keys, default_openai_api_key

def get_openai_api_key(user_id):
    return openai_api_keys.get(user_id, default_openai_api_key)

def get_openai_response(user_id, thread_ts, model_name):
    try:
        api_key = get_openai_api_key(user_id)
        openai_client = OpenAI(api_key=api_key)
        masked_api_key = '-'.join(api_key.split('-')[:3])

        logging.info(f"Using OpenAI API Key(Masked): {masked_api_key}...")
        
        with user_conversations_lock:
            messages = user_conversations[user_id][thread_ts]

        completion = openai_client.chat.completions.create(
            model=model_name,
            messages=messages
        )

        return completion.choices[0].message.content.strip()
    except openai.RateLimitError:
        logging.error("Rate limit exceeded:", exc_info=True)
        return "Server rate limit exceeded. Please try again later."
    except Exception as e:
        logging.error("Error generating OpenAI response:", exc_info=True)
        return "An error occurred. Please try again."