import json
import os
import boto3
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO)

# 환경 변수에서 SQS 큐 URL 가져오기
queue_url = os.environ['SQS_QUEUE_URL']

sqs = boto3.client('sqs')

def lambda_handler(event, context):
    try:
        body = json.loads(event['body'])
        command = body.get('command')
        user_id = body.get('user_id')
        text = body.get('text')
        response_url = body.get('response_url')

        if not command or not user_id or not text or not response_url:
            logging.error("Required fields are missing")
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'Required fields are missing'})
            }

        message = {
            'user_id': user_id,
            'command': command,
            'text': text,
            'response_url': response_url
        }

        sqs.send_message(QueueUrl=queue_url, MessageBody=json.dumps(message))
        
        logging.info("Message sent to SQS")

        return {
            'statusCode': 200,
            'body': json.dumps({'text': 'Your request is being processed.'})
        }
    
    except Exception as e:
        logging.error("Error processing request", exc_info=True)
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'Internal Server Error'})
        }
