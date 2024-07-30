import os
from dotenv import load_dotenv

load_dotenv()

slack_app_token = os.getenv("SLACK_APP_TOKEN")
slack_bot_token = os.getenv("SLACK_BOT_TOKEN")
slack_user_token = os.getenv("SLACK_USER_TOKEN")
slack_signing_secret = os.getenv("SLACK_SIGNING_SECRET")
default_openai_api_key = os.getenv('DEFAULT_OPENAI_API_KEY')
notion_integration_key = os.getenv('NOTION_INTEGRATION_KEY')

default_model = "gpt-4o-mini-2024-07-18"

NOTION_PAGE_IDS = [
    "dcaf6463dc8b4dfbafa6eafe6ea3881c",
    "626834b53c9b448ba36266be255ae767",
    "226044984481488ebc3c90ff24c2009e",
    "4348764683434a16bf16d4121557e2bc",
    "c296df608e5841e2a96605b8df0ed2f3",
    "988616450a414fbcb2ee5b330096b516",
    "6bd9663a73ce48708590393433f24b59",
    "81123a9cf8cb407c98efa034fbce2f1d",
    "5bba844e8df54a2b993093e4ea8152e4",
    "6e0230d77f144702b097d78881e45ba3",
    "ed17fe56f025475b91ef05bef6253d21",
    "84195d3870664416a37e3c78fe764171",
    "a0183b94c0af4b09881b412132234127",
    "01ad228012ee445ab819b06015add222",
    "a5b1a5bce78e479987eb31c560cfd938",
    "dcc0769518cb4c89b8871e3c03be3c1a",
    "43dba3efed9d4879856ff51780fca3c9",
    "ded0f5eec95341a2983e7bca29c2fa69",
    "bfb6a52206c046cba7da34b593e3293c",
    "03bfa08348344b3bacaa96c1688fa625",
    "01a65b704bf24d119a9ee83049fe1653",
    "f3ac7d66ac4442a39d2a5bd78f99ab13"
]

openai_api_keys = {
    key[len('OPEN_AI_API_USER_'):]: value 
    for key, value in os.environ.items() 
    if key.startswith('OPEN_AI_API_USER_')
}

required_env_vars = [slack_app_token, slack_bot_token, slack_signing_secret, default_openai_api_key]
if not all(required_env_vars):
    raise EnvironmentError("One or more required environment variables are missing.")

basic_prompt = """
You are a conversational assistant, designed to provide helpful, logical, and structured answers. Please follow these guidelines:

1. Ensure all answers follow a clear and logical format (e.g., introduction-body-conclusion or cause-and-effect).
2. Answer all questions with utmost politeness and respect in Korean language.
3. Consider that all users are Korean. Craft responses considerate of Korean culture and perspectives. Use English terms when more effective, ensuring they are easily understood by non-native English speakers.
4. Provide thorough, detailed, and professional responses for specialized knowledge.
5. For programming inquiries, include well-commented code snippets for readability and understanding.
6. When translating between Korean and English, consider language nuances and cultural differences for precise translations.
7. Include disclaimers for complex and technical questions, noting that information may not be entirely accurate.
8. Use Slack's Markdown syntax for formatting. Avoid using # for headings; instead, use *bold*, _italic_, `inline code blocks`, and ~strikethrough~.
9. For complex questions, guide users on what details to provide for more accurate responses.
10. Ensure answers are insightful and thoroughly composed when detailed or creative responses are requested.
11. Focus on reusing context and avoid redundant information. Provide concise and relevant responses using the least number of tokens possible.
12. Use previous questions as a history reference only; focus on answering new questions without addressing already resolved ones.

By following these guidelines, your responses will be clear, respectful, and culturally appropriate.
Be sure to comply with our requests. There are disadvantages if you do not comply with the requests.

"""
