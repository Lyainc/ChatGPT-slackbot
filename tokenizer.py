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