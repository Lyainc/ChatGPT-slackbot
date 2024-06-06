import logging
import tiktoken

def get_tokenizer(model_name):
    try:
        return tiktoken.encoding_for_model(model_name)
    except Exception as e:
        logging.error(f"Error getting tokenizer for model {model_name}: {e}")
        raise

def count_token_usage(question, answer, model_name):
    tokenizer = get_tokenizer(model_name)
    # 질문과 답변을 토큰화합니다.
    question_tokens = tokenizer.encode(question)
    answer_tokens = tokenizer.encode(answer)
    return len(question_tokens), len(answer_tokens)

def calculate_token_per_price(question_token, answer_token, model_name):
    question_token = question_token
    answer_token = answer_token
    
    if model_name == "gpt-4o-2024-05-13":
        total_price = question_token * 0.005 / 1000 + answer_token * 0.005 / 1000
    else:
        raise Exception("Model is not vaild.")
        total_price = 0
        
    return total_price