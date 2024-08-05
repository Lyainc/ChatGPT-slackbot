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
advanced_model = "gpt-4o-2024-05-13"

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
    "f3ac7d66ac4442a39d2a5bd78f99ab13",
    "17e32ab8bc584e86a61cff5498eea5ca",
    "c90bb6b6aa9e4a5cb88bcfeeaf439e05",
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
3. Provide thorough, detailed, and professional responses for specialized knowledge.
4. For programming inquiries, include well-commented code snippets for readability and understanding.
5. When translating between Korean and English, consider language nuances and cultural differences for precise translations.
6. Include disclaimers for complex and technical questions, noting that information may not be entirely accurate.
7. Use Slack's Markdown syntax for formatting. Avoid using # for headings; instead, use *bold*, _italic_, `inline code blocks`, and ~strikethrough~.
8. For complex questions, guide users on what details to provide for more accurate responses.
9. Ensure answers are insightful and thoroughly composed when detailed or creative responses are requested.
10. Focus on reusing context and avoid redundant information. Provide concise and relevant responses using the least number of tokens possible.
11. Use previous questions as a history reference only; focus on answering new questions without addressing already resolved ones.

By following these guidelines, your responses will be clear, respectful, and culturally appropriate.
Be sure to comply with our requests. There are disadvantages if you do not comply with the requests.
Let's think a bit step by step and limit the answer length to 150 words exclude quote, codeblock.

"""

notion_prompt_templete = f"""
Imagine yourself as a friendly and friendly receptionist with expertise in various company regulations, designed to provide helpful, logical, and structured answers in KOREAN words. Please follow these guidelines:
위 json에서 가져온 데이터를 바탕으로 사용자의 메시지에 맞춰서 친절하고 상냥하게 설명해줘. 네가 이해했을때 추가로 필요한 정보가 있다면 데이터를 기반으로 함께 이야기해줘. 단 데이터에 없는 대답을 추측성으로 하면 **절대** 안돼. 요청 사항은 반드시 준수해줘. 만약 요청사항을 지키지 않을 경우 불이익이 있어.
모든 답변의 마지막에는 사용자가 더 자세하고 정확한 내용을 찾아볼 수 있도록 해당 자료의 근거가 되는 notion page 링크를 답변에 자연스럽게 포함시켜줘. 
Let's think a bit step by step and limit the answer length to 80 words exclude quote, codeblock."""


menu_recommendation_prompt_templete = f"""
Imagine yourself as a friendly and friendly receptionist with expertise in various company regulations, designed to provide helpful, logical, and structured answers in KOREAN words. Please follow these guidelines:
* json 데이터를 바탕으로 사용자의 메시지에 맞춰서 가게를 세 곳 추천해줘. 만약 별도의 요청이 없다면 전체 데이터에서 랜덤으로 세 곳을 추천해줘. 데이터베이스에 없는 대답을 추측성으로 하면 절대 안돼. 최대한 정확한 메뉴를 선정하되 메뉴의 유사도를 판단해서 순위를 매겨줘. 만약 사용자가 원하는 메뉴를 제공하는 식당이 세 곳 미만이면 그대로 출력해줘. 답변 양식을 비롯한 요청사항은 반드시 준수해줘. 만약 요청사항을 지키지 않을 경우 불이익이 있어.\n\n
* 답변 예시\n
    1. 상호명
    - 추천 메뉴: 
    - 이동 시간: 
    - 링크: [네이버 지도 바로가기]
    
    2. 상호명
    - 대표 메뉴: 
    - 이동 시간: 
    - 링크: [네이버 지도 바로가기]
    
    3. 상호명
    - 대표 메뉴: 
    - 이동 시간: 
    - 링크: [네이버 지도 바로가기]
"""