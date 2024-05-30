import openai
from datetime import datetime, timedelta

def display_help():
    """
    Returns the help message with available commands.
    """
    help_message = (
        "Here are the commands you can use:\n"
        "/start [question] - Start a new conversation in a thread.\n"
        "/rewrite - Regenerate answers to the last question.\n"
        "/setpref [PREFERENCE] [VALUE] - Set a user preference (e.g., /setpref preset friendly).\n"
        "/history - Display the conversation history of the current session.\n"
        "/save [exampleName] - Save the current conversation and prompt under a keyword.\n"
        "/load [exampleName] - Load the conversation and prompt saved under a keyword.\n"
        "/download_history - Download the current conversation history.\n"
        "/check_tokens - Check the tokens used in the current month.\n"
        "/help - Display this help message."
    )
    return help_message

def check_tokens_used(api_key):
    """
    Check the tokens used in the current month for the provided OpenAI API key.

    Parameters:
    - api_key (str): The OpenAI API key.

    Returns:
    - str: A message with the tokens used information.
    """
    try:
        # Initialize the OpenAI API key

        # Calculate the start of the current month
        now = datetime.now()
        start_of_month = datetime(now.year, now.month, 1)

        # Retrieve the usage information
        usage = openai.Usage.list(start_date=start_of_month, end_date=now)

        # Calculate the total tokens used in the current month
        total_tokens = sum(item['n_tokens'] for item in usage['data'])

        return f"You have used {total_tokens} tokens so far this month."

    except Exception as e:
        return f"An error occurred while checking the tokens used: {str(e)}"
