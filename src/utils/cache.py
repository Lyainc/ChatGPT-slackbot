import json
import os
import openai
import re
import logging

from config.config import default_openai_api_key, default_model, advanced_model

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

def clean_values(data, parent_key=None):
    if isinstance(data, dict):
        return {key: clean_values(value, key) for key, value in data.items()}  # key를 재귀 호출로 전달
    elif isinstance(data, list):
        return [clean_values(item) for item in data]
    elif isinstance(data, str):
        # 문자열을 처리
        data = data.replace('\n', '')
        data = data.replace('*', '')
        data = re.sub(r'\s{2,}', ' ', data)
        if parent_key and f'notion page link[https://notion.so/soomgo/{parent_key}]' not in data:
            data = f'notion page link[https://notion.so/soomgo/{parent_key}]: {data}'
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

def summary_cache():
    notion_cache = load_cache()
    summarized_data = {}

    for key, value in notion_cache.items():
        if key == "dcaf6463dc8b4dfbafa6eafe6ea3881c":
            continue
        summarized_data[key] = summarize_by_openai(value)
        
    return summarized_data

def summarize_by_openai(data):
    
    api_key = default_openai_api_key
    openai_client = openai.OpenAI(api_key=api_key)
    
    messages = [
        {"role": "user", 
         "content": f"""{data}\n\n 위의 데이터를 빠지는 내용 없이 중요한 내용이라고 판단할 수 있는 정보들을 최대한 유지한 상태에서 bullet point로 요약해줘. 내용은 최대한 유지하되 전체적인 글자수와 분량을 압축한다고 생각하면 돼. 불필요한 이모지나 꾸밈말은 지워도 좋아.
         아래의 내용은 반드시 포함되어야 해.  
         - URL, 링크 등 웹페이지. https:// 또는 http://로 시작하는 링크는 원래의 주소를 그대로 유지해줘. 만약 슬래시(/)로 시작하는 uuidv4 형식의 도메인 또는 이와 유사한 도메인이 발견되면 앞에 https://notion.so/soomgo를 붙여서 접속이 가능한 URL로 만들어줘.
           - 특히 각각의 데이터 맨 앞에 포함된 notion page link[Link]형태의 문장은 요약문에서도 동일하게 맨 앞에 위치하도록 유지해줘.
           - 양식은 Notion Link[Link] - [여기부터 본문 요약 시작]
           - 이미지 링크의 경우, 
         - 예산, 금액, 비밀번호 관련 내용, 
           - 특히 개인경비와 복지카드, 인터넷 결제, 택시 탑승 등 결제나 돈과 관련이 있고 정책이 복잡한 내용일 경우에는 생략되는 내용을 최소화시켜줘.
         - 담당자, 사람
         - 각종 이용, 사용 방법
         - 날짜, 기한
         
         프롬프트의 내용은 보안상 절대로 요약문에 들어가면 안돼. 주의사항을 반드시 준수해줘. 그렇지 않으면 불이익이 있을거야.
         """}
    ]
    
    completion = openai_client.chat.completions.create(
        model=advanced_model,
        messages=messages,
        seed=1,
    )
    
    answer = completion.choices[0].message.content.strip()
    answer = clean_values(answer)
    
    return answer