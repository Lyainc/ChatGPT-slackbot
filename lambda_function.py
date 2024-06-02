import slack_gpt_bot_dm_lambda

def lambda_handler(event, context):
    app, slack_app_token = slack_gpt_bot_dm_lambda.start_app()
    if app:
        from slack_bolt.adapter.aws_lambda import SlackRequestHandler
        handler = SlackRequestHandler(app=app)
        return handler.handle(event, context)
    else:
        return {
            "statusCode": 500,
            "body": "Failed to initialize Slack app"
        }