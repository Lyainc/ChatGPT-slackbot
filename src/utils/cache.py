import json
import os
import openai
import re
import logging

from config.config import *

CACHE_FILE = 'notion_cache.json'
SUMMARY_CACHE_FILE = 'summary_cache.json'

def load_cache():
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def load_summarized_cache():
    if os.path.exists(SUMMARY_CACHE_FILE):
        with open(SUMMARY_CACHE_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def clean_values(data):
    if isinstance(data, dict):
        return {key: clean_values(value) for key, value in data.items()}
    elif isinstance(data, list):
        return [clean_values(item) for item in data]
    elif isinstance(data, str):
        # Remove newlines and reduce multiple whitespaces to a single space
        data = data.replace('\n', '')
        data = data.replace('**', '')
        data = re.sub(r'\s{2,}', ' ', data)
        return data
    return data

def save_cache(data):
    clean_data = clean_values(data)
    cache_exists = os.path.exists(CACHE_FILE)
    summary_cache_exists = os.path.exists(SUMMARY_CACHE_FILE)

    if cache_exists:
        with open(CACHE_FILE, 'r', encoding='utf-8') as f:
            existing_data = json.load(f)
        if existing_data == clean_data and summary_cache_exists:
            logging.info("Data is already cached. Skipping caching.")
            return
        if existing_data != clean_data:
            logging.info("Data has changed. Updating cache and summary.")
    
    # Update the notion cache
    with open(CACHE_FILE, 'w', encoding='utf-8') as f:
        json.dump(clean_data, f, ensure_ascii=False, indent=4)

    # Update the summary cache
    summarized_data = summary_cache()
    with open(SUMMARY_CACHE_FILE, 'w', encoding='utf-8') as f:
        json.dump(summarized_data, f, ensure_ascii=False, indent=4)
    
def summary_cache():
    notion_cache = load_cache()
    summarized_data = {}

    for key, value in notion_cache.items():
        if key == "dcaf6463dc8b4dfbafa6eafe6ea3881c":
            continue
        summarized_data[key] = summary_to_openai(value)

    existing_summarized_data = load_summarized_cache()
    if existing_summarized_data == summarized_data:
        logging.info("Summarized data is already cached. Skipping caching.")
        return existing_summarized_data
        
    return summarized_data

def summary_to_openai(data):
    
    api_key = default_openai_api_key
    openai_client = openai.OpenAI(api_key=api_key)
    
    messages = [
        {"role": "user", "content": f"{data}\n\n 위의 데이터를 빠지는 내용 없이 bullet point로 요약해줘. 데이터에 URL이 포함되어있다면 놓치지 말고 내용에 반드시 포함해줘."}
    ]
    
    completion = openai_client.chat.completions.create(
        model=default_model,
        messages=messages,
        seed=1
    )
    
    answer = completion.choices[0].message.content.strip()
    answer = clean_values(answer)
    
    return answer