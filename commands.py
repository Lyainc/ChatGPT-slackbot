from openai import OpenAI

client = OpenAI()
from utils import display_help, check_tokens_used
from state_management import save_session, load_session
# from file_utils import generate_history_file
from datetime import datetime

def handle_message(user_id, user_message, say, user_states, event):
    """
    Handles the user message and executes the appropriate commands.
    """
    # Get the thread timestamp
    thread_ts = event.get("thread_ts", event["ts"])

    # Handle /start command
    if user_message.startswith("/start "):
        question = user_message[len("/start "):].strip()
        handle_start_command(user_id, question, say, user_states, thread_ts)
        return

    # Handle /rewrite command
    if user_message.lower() == "/rewrite":
        previous_question = user_states[user_id]["previous_question"]
        if previous_question:
            user_message = previous_question
        else:
            say("There's no previous question to rewrite.", thread_ts=thread_ts)
            return

    # Handle /history command
    if user_message.lower() == "/history":
        history = user_states[user_id]["history"]
        if history:
            history_message = "Conversation history:\n" + "\n".join(history)
            say(history_message, thread_ts=thread_ts)
        else:
            say("No history available for this session.", thread_ts=thread_ts)
        return

    # Handle /setpref command
    if user_message.startswith("/setpref "):
        try:
            preference, value = user_message[len("/setpref "):].split(" ", 1)
            user_states[user_id]["preferences"][preference] = value
            say(f"Preference '{preference}' set to '{value}'.", thread_ts=thread_ts)
        except ValueError:
            say("Failed to set preference. Use /setpref [PREFERENCE] [VALUE].", thread_ts=thread_ts)
        return

    # Handle /save command
    if user_message.startswith("/save "):
        session_name = user_message[len("/save "):].strip()
        save_session(session_name, user_id, user_states, say, thread_ts)
        return

    # Handle /load command
    if user_message.startswith("/load "):
        session_name = user_message[len("/load "):].strip()
        load_session(session_name, user_id, user_states, say, thread_ts)
        return

    # Handle /download_history command
    # if user_message.lower() == "/download_history":
    #     file_path = generate_history_file(user_id, user_states)
    #     say(f"Download your conversation history here: {file_path}", thread_ts=thread_ts)
    #     return

    # Handle /check_tokens command
    if user_message.lower() == "/check_tokens":
        api_key = openai.api_key
        tokens_message = check_tokens_used(api_key)
        say(tokens_message, thread_ts=thread_ts)
        return

    # Handle /help command
    if user_message.lower() == "/help":
        say(display_help(), thread_ts=thread_ts)
        return

    # Combine preset with user message
    preset_prompt = user_states[user_id]["preferences"].get("preset", "")
    final_prompt = f"{preset_prompt}\n{user_message}" if preset_prompt else user_message

    try:
        # Call OpenAI's ChatCompletion endpoint to get a response
        response = client.chat.completions.create(model="gpt-4",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": final_prompt}
        ])

        # Extract the response text from the API response
        bot_reply = response.choices[0].message.content
        say(bot_reply, thread_ts=thread_ts)

        # Save the question and response to user state
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        user_states[user_id]["previous_question"] = user_message
        user_states[user_id]["history"].append(f"[{timestamp}] User: {user_message}")
        user_states[user_id]["history"].append(f"[{timestamp}] Bot: {bot_reply}")

    except Exception as e:
        say(f"Sorry, I couldn't process your request. Error: {str(e)}", thread_ts=thread_ts)

def handle_start_command(user_id, question, say, user_states, thread_ts):
    """
    Handles the /start command to begin a conversation in a thread.
    """
    # Combine preset with user message
    preset_prompt = user_states[user_id]["preferences"].get("preset", "")
    final_prompt = f"{preset_prompt}\n{question}" if preset_prompt else question

    try:
        # Call OpenAI's ChatCompletion endpoint to get a response
        response = client.chat.completions.create(model="gpt-4",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": final_prompt}
        ])

        # Extract the response text from the API response
        bot_reply = response.choices[0].message.content
        say(bot_reply, thread_ts=thread_ts)

        # Save the question and response to user state
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        user_states[user_id]["previous_question"] = question
        user_states[user_id]["history"].append(f"[{timestamp}] User: {question}")
        user_states[user_id]["history"].append(f"[{timestamp}] Bot: {bot_reply}")

    except Exception as e:
        say(f"Sorry, I couldn't process your request. Error: {str(e)}", thread_ts=thread_ts)
