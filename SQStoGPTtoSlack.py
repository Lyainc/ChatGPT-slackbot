import json
import os
import logging
import requests
from openai import OpenAI
from tokenizer import count_token_usage

# 로깅 설정
logging.basicConfig(level=logging.INFO)

# 환경 변수에서 OpenAI API 키 가져오기
openai_api_key = os.environ.get("OPEN_AI_API")
client = OpenAI(api_key=openai_api_key)

user_conversations = {}

def lambda_handler(event, context):
    for record in event['Records']:
        body = json.loads(record['body'])
        user_id = body['user_id']
        command = body['command']
        text = body['text']
        response_url = body['response_url']
        
        try:
            if user_id not in user_conversations:
                user_conversations[user_id] = [
                    {"role": "system", "content": "You are a helpful assistant."}
                ]

            if command == "/질문시작":
                question = text.strip()
                user_conversations[user_id].append({"role": "user", "content": question})
                answer = get_openai_response(user_id)
                response_message = answer

            elif command == "/대화종료":
                if user_id in user_conversations:
                    del user_conversations[user_id]
                response_message = "대화를 종료합니다."

            requests.post(response_url, json={'text': response_message})
        
        except Exception as e:
            logging.error("Error processing SQS message", exc_info=True)
            requests.post(response_url, json={'text': "문제가 발생했습니다. 다시 시도해 주세요."})

def get_openai_response(user_id):
    try:
        completion = client.chat.completions.create(
            model="gpt-4o-2024-05-13",
            messages=user_conversations[user_id]
        )
        answer = completion.choices[0].message.content.strip()
        
        # Count token usage
        question_tokens, answer_tokens = count_token_usage(
            user_conversations[user_id][-1]["content"], 
            answer, 
            "gpt-4o-2024-05-13"
        )
        token_usage_message = f"_질문에 사용된 토큰 수: {question_tokens}, 답변에 사용된 토큰 수: {answer_tokens}_"

        # 답변에 token_usage_message 추가 (개행 후 이탤릭체로)
        answer += f"\n\n{token_usage_message}"

        logging.info(f"Generated answer: {answer}")
        return answer
    except Exception as e:
        logging.error("Error generating OpenAI response:", exc_info=True)
        return "문제가 발생했습니다. 다시 시도해 주세요."
