import time

# Session timeout in seconds (e.g., 15 minutes)
SESSION_TIMEOUT = 900
saved_sessions = {}

def initialize_user_state(user_id, user_states):
    """
    Initializes the user state if not already present.
    """
    if user_id not in user_states:
        user_states[user_id] = {
            "previous_question": None,
            "preferences": {},
            "history": [],
            "last_activity": time.time(),
        }

def update_last_activity(user_id, user_states):
    """
    Updates the last activity timestamp for the user.
    """
    user_states[user_id]["last_activity"] = time.time()

def check_session_timeout(user_id, user_states):
    """
    Checks if the session has timed out due to inactivity.
    """
    return time.time() - user_states[user_id]["last_activity"] > SESSION_TIMEOUT

def save_session(session_name, user_id, user_states, say):
    """
    Saves the current session's history and preferences under a given name.
    """
    saved_sessions[session_name] = {
        "history": user_states[user_id]["history"],
        "preferences": user_states[user_id]["preferences"]
    }
    user_states[user_id]["history"] = []
    user_states[user_id]["preferences"] = {}
    say(f"Session saved as '{session_name}'. Current session cleared.")

def load_session(session_name, user_id, user_states, say):
    """
    Loads a saved session's history and preferences.
    """
    if session_name in saved_sessions:
        user_states[user_id]["history"] = saved_sessions[session_name]["history"]
        user_states[user_id]["preferences"] = saved_sessions[session_name]["preferences"]
        say(f"Session '{session_name}' loaded.")
    else:
        say(f"No saved session found with the name '{session_name}'.")
