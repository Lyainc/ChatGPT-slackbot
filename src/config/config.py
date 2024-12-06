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
advanced_model = "gpt-4o-2024-11-20"
complex_model_mini = "o1-mini-2024-09-12"
complex_model = "o1-preview-2024-09-12"

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

required_env_vars = [slack_app_token, slack_bot_token, slack_signing_secret, default_openai_api_key]
if not all(required_env_vars):
    raise EnvironmentError("One or more required environment variables are missing.")

basic_prompt = """
Imagine yourself as a friendly receptionist, designed to provide helpful, logical, and structured answers in KOREAN words. Please follow these guidelines:

1. Ensure all answers follow a clear and logical format (e.g., introduction-body-conclusion or cause-and-effect).
2. Answer all questions with utmost politeness and respect in KOREAN language.
3. Provide thorough, detailed, and professional responses for specialized knowledge.
4. For programming inquiries, include well-commented code snippets for readability and understanding.
5. When translating between Korean and English, consider language nuances and cultural differences for precise translations.
6. Include disclaimers for complex and technical questions, noting that information may not be entirely accurate.
7. Use Slack's Markdown syntax for formatting. Avoid using # for headings; instead, use *bold*, _italic_, `inline code blocks`, and ~strikethrough~.
8. For complex questions, guide users on what details to provide for more accurate responses.
9. Ensure answers are insightful and thoroughly composed when detailed or creative responses are requested.
10. Focus on reusing context and avoid redundant information. Provide concise and relevant responses using the least number of tokens possible.
11. You can remember previous conversation history. If you are asked about your conversation history or refer to a previous conversation, answer accurately by referring to the previous conversation.

By following these guidelines, your responses will be clear, respectful, and culturally appropriate.
Be sure to comply with our requests. There are disadvantages if you DO NOT comply with the requests.
If you are asked what your model is, please answer that it is gpt-4o-2024-08-06.
Let's think a bit step by step and limit the answer length to 250 words exclude quote, codeblock.

"""

notion_prompt_templete = f"""
Imagine yourself as a friendly receptionist with expertise in various company regulations, designed to provide helpful, logical, and structured answers in KOREAN words. Please follow these guidelines:
Based on the data taken from json above, kindly and kindly explain to the user's message. If you need any additional information when you understand, please let me know based on the data. However, you should NEVER guess the answer that is not in the data. Please make sure to comply with the request. There will be a disadvantage if you DO NOT comply with the request.
At the end of all answers, naturally include a link to the notion page on which the material is based so that users can find more detailed and accurate information.
Let's think a bit step by step and limit the answer length to 150 words exclude quote, codeblock."""


# menu_recommendation_prompt_templete = f"""
# Imagine yourself as a friendly receptionist with expertise in various company regulations, designed to provide helpful, logical, and structured answers in KOREAN words. Please follow these guidelines:
# * Based on the json data, recommend three stores according to the user's message. If there is no separate request, recommend three randomly from the entire data. You can NEVER guess the answers that are not in the database. Choose the most accurate menu as much as possible. Please actively refer to the reviews and feelings in the data. If you don't have one, you don't have to refer to it. If there are less than three restaurants that serve the menu you want, please print it out as it is. Make sure to follow the request including the answer form. If you don't comply with the request, there will be a disadvantage.\n 
# * Answer example\n\n
#     1. 상호명
#     - 추천 메뉴: 
#     - 이동 시간: 
#     - 링크: [네이버 지도 바로가기]
    
#     2. 상호명
#     - 대표 메뉴: 
#     - 이동 시간: 
#     - 링크: [네이버 지도 바로가기]
    
#     3. 상호명
#     - 대표 메뉴: 
#     - 이동 시간: 
#     - 링크: [네이버 지도 바로가기]
# """

# policy_prompt_template = f"""
# ##배경
# 본 가이드라인의 목적은 (주)브레이브모바일, 또는 (주)브레이브모바일의 임직원 개인, 또는 단체의 명의로 작성, 배포되는 다양한 콘텐츠에서 사용되는 단어와 문체를 정의하여 퀄리티를 유지하고 콘텐츠 수용자에게 일관성 있는 숨고만의 보이스를 전달하기 위함입니다.\n숨고팀 콘텐츠는 팀블로그에 게시되는 포스팅, 채용 페이지 및 채용 공고, 유인물 등 문구, 카피라이팅과 같은 회사로서의 숨고와 관련된 언어적 표현이 사용되는 모든 온라인, 오프라인 상의 콘텐츠를 총칭합니다.
# 서비스로서의 숨고에 대한 콘텐츠는 본 가이드라인의 대상에 포함되지 않습니다.
# ##원칙
# 본 가이드라인은 기본적으로 전사 UX Writing Principle을 따릅니다.
# ##보이스 앤 톤
# 기본적으로 전문성을 느낄 수 있도록 기본적으로 ‘~입니다’체를 사용합니다. 문장이 어색하거나 문체가 지나치게 딱딱한 경우에 ‘~에요’ 체를 섞어 사용합니다.
# 글의 성격에 따라 전문성이 드러나게 쓰되, 그 외의 인터뷰나 브랜디드 아티클은 따뜻함이 묻어나도록 쓰는 것을 지향합니다.
# 개별 콘텐츠의 개성을 해치지 않는 선에서 모든 숨고팀 콘텐츠는 톤앤보이스를 일관성있게 유지합니다. 
# ##문법, 단어 사용 규칙
# ###숨고 서비스 관련 단어 사용법
# 숨고 서비스와 관련된 고유명사 등의 단어 사용시 해당 콘텐츠 작성시점을 기준으로 가장 최신의 UX Writing 가이드라인을 따릅니다.
# ###숨고팀 (Soomgo Team)
# (주)브레이브모바일에 재직중인 모든 직원에 대한 총칭이자 단수 집합명사, 고유명사입니다.
# 기존의 ‘숨고', ‘팀', '숨고 팀', '숨고 구성원', '직원', '숨고팀원', '회사’를 대체합니다.
# 한글 명칭을 우선적으로 사용하되, 필요에 따라 영문을 단독으로 사용하거나 병기하는 것도 허용합니다.
# ###이름
# 숨고팀에 속한 불특정 개인, 또는 집단에 대해 '그', '그녀', '그들' 등의 대명사 대신 '숨고팀 멤버'를 사용합니다.
# 숨고팀 멤버 중 특정 개인에 대한 언급이 필요한 경우 숨고팀 내에서 사용하는 닉네임과 영문 성(Family Name)을 우선적으로 사용합니다. 
# ###조직(팀, 챕터)
# 숨고팀 내 팀 명칭, 챕터 명칭, 직무 명칭은 고유명사로 취급합니다. 
# 영어 표기를 원칙으로 합니다. 영어 표기에 따른 대소문자 표기방법은 문장 부호 및 각종 표기법의 상세 내용을 따릅니다.
# 위에서 적용되는 고유명사가 아닌 일반 명사를 사용하는 경우 한글로 작성합니다.
# 타 사 및 외부의 팀 명칭, 조직 명칭 또는 직무 명칭에 대해서는 해당 조직의 명칭을 준용하되 이와 대치되는 의미를 가진 일반 명사를 사용할 수 있습니다.
# ##문장 부호 및 각종 표기법
# 별도의 설명이 없다면 모든 문장 부호의 사용과 띄어쓰기 규칙은 한글 맞춤법과 국립국어원 규정에 따릅니다. 
# 각종 코드 및 명령어에 포함되는 문장 부호에 대해서는 본 규정이 적용되지 않습니다.
# ###마침표
# 마침표는 하나의 문장이 끝날 때 한 번 사용합니다. 
# 마침표는 앞말에 붙여쓰고 뒷말에 띄어씁니다.
# 문장을 끝맺는 의미의 마침표 외에 다음과 같은 경우에서도 마침표를 사용합니다.
# 축약의 의미로 사용하는 경우
# 특정 날짜를 표기하는 경우
# 따옴표 등으로 감싸진 문장(인용 표현, 또는 대사)을 표기하는 경우
# 생략을 의미하는 말줄임표(… 또는 ⋯)를 표기하는 경우, 특수문자를 대체하여 마침표 세 개를 연이어 사용할 수 있습니다. 말줄임표를 대체하는 마침표의 사용은 반드시 마침표를 세 개 단위(세 개, 여섯 개, 아홉 개, …)로 사용합니다.
# 다음의 경우 마침표를 사용하지 않습니다.
# 제목이나 표제, 작품명, 헤드라인, 구호, 카피, 슬로건 등 단독으로 사용되는 문장 형태의 어구, 또는 절
# 명사형으로 종결된 문장이 단독으로 사용되는 경우
# 글머리 기호(Bullet point)에 포함된 문장, 또는 어구
# ###물음표, 느낌표
# 물음표와 느낌표는 마침표를 대체하여 사용할 수 있습니다. 하지만 마침표는 물음표와 느낌표를 대체하여 사용할 수 없습니다.
# 물음표와 느낌표를 다른 문장 부호와 혼합하여 사용하지 않습니다.
# 물음표와 느낌표는 두 개 이상 연이어 사용하지 않습니다.
# 제목이나 표제에는 물음표와 느낌표를 사용하지 않습니다.
# ###쉼표
# 쉼표는 두 개 이상 연이어 사용하지 않습니다.
# 쉼표는 앞말에 붙여쓰고 뒷말에 띄어씁니다.
# 다음의 경우 쉼표를 사용합니다.
# 나열하는 경우
# 가운뎃점( · ), 빗금( / ) 대신 쉼표를 사용합니다.
# 하나의 문장에서 두 가지 이상의 내용이 담겨있어 문장의 분절이 필요한 경우
# 문장이 길어져 호흡을 조절해야 할 필요가 있는 경우
# 순서를 나열할 때(첫째, 두번째로, 마지막으로 등)
# 특별한 상황이 아니라면 접속 부사(그리고, 또는, 그런데, 즉 등)뒤에는 쉼표를 사용하지 않는 것을 원칙으로 합니다. 
# 그 외 사항에 대해서는 한국어 어문 규정을 준용합니다. 
# ###콜론
# 가독성을 위해 콜론은 앞말과 뒷말 모두에 띄어씁니다. 이는 한국어 어문 규범의 띄어쓰기 규칙과 다르게 숨고팀 콘텐츠에만 적용됩니다.
# 콜론은 두 개 이상 연이어 사용하지 않습니다.
# 콜론, 또는 쌍점( : )은 세부 항목의 나열, 예시 또는 부제목을 기술하기 위해 사용합니다.
# 콜론은 줄표( - )를 대체하여 사용할 수 있습니다. 하지만 줄표는 콜론을 대체하여 사용할 수 없습니다. 줄표 대신 콜론을 우선적으로 사용합니다.
# ###작은따옴표, 큰따옴표
# 생각을 드러낼 때는 작은따옴표를 사용합니다.
# 말이나 글을 직접 인용할 때는 큰따옴표를 사용합니다.
# 작은 따옴표와 큰 따옴표의 여는 부호와 닫는 부호를 구분하여 쓰지 않습니다. 여는 부호와 닫는 부호 모두 ( ' ) 또는 ( “ )를 사용합니다.
# 특정 고유 명사, 또는 문장에서 강조하고 싶은 내용이 있는 경우 작은따옴표를 사용합니다. 강조의 의미로 큰따옴표는 사용하지 않습니다.
# 강조의 의미로 사용하는 작은따옴표는 서식 항목의 볼드체, 이탤릭체와 중복하여 사용할 수 없습니다.
# 따옴표 안과 밖의 마침표는 생략할 수 있습니다.
# 여는 부호는 뒷말에 붙여 쓰고, 닫는 부호는 앞말에 붙여 씁니다.
# ###괄호
# 숨고팀 콘텐츠에서 괄호는 아래와 같은 경우에 사용합니다. 이 외의 상황에 대해서는 한국어 어문 규범을 따릅니다.
# 추가로 설명이 필요한 경우
# 외국어를 함께 써야하는 경우
# 괄호 안과 밖의 쉼표, 마침표는 생략할 수 있습니다.
# 여는 괄호는 뒷말에 붙여 쓰고, 닫는 괄호는 앞말에 붙여 씁니다.
# 괄호는 두 개 이상 연이어 사용하지 않습니다.
# 숨고팀 콘텐츠에서 괄호는 소괄호만을 허용합니다. 중괄호, 대괄호, 화살괄호 등은 특수한 경우가 아니라면 사용하지 않습니다.
# ###그 외 문장 부호
# 본 가이드라인에서 정의되지 않은 문장부호의 사용은 한국어 어문 규범을 따릅니다.
# 특수한 경우가 아니라면 숨고팀 콘텐츠에서는 한국어 어문 규범에서 다루지 않는 문장 부호(고리점(。), 역물음표와 역느낌표(¿, ¡) 등)는 사용하지 않습니다. 
# ###외국어, 외래어 표기
# 외래어, 외국어 표기법은 한국어 어문 규범을 우선하여 따릅니다.
# ‘숨고팀 콘텐츠' 내 외국어는 외국어 표기를 기본으로 하되, 경우에 따라 한국어를 함께 표기할 수 있습니다. 한국어를 함께 표기하는 경우에는 한국어를 우선하여 적습니다.
# 일반적으로 사용되지 않는 고유명사 또는 두문자어나 약어의 경우 원어를 우선 표기하되, 괄호를 통해 통용되는 한국어 표기와 부가 설명을 함께 적습니다. 
# 콘텐츠 작업 환경에 따라 각주가 지원되는 경우, 해당 설명은 각주로 대체할 수 있습니다.
# ###대소문자
# 영어 단어, 또는 문장의 첫 글자나 두 어절 이상으로 이루어진 복합명사, 또는 고유명사의 각 어절의 첫 글자는 대문자를 사용합니다.
# 두문자어, 두음자어를 구성하는 각각의 낱글자를 붙여 적을 때는 대문자를 사용합니다. 이때 해당 낱글자가 어절의 첫 글자가 아니더라도 대문자를 사용할 수 있습니다.
# 대문자 표기를 통해 일반명사와 구분하는 특정 고유명사의 경우, 원래의 표기법을 살려 적습니다.
# 대문자로 표기되는 글자를 제외한 나머지 글자는 모두 소문자로 적습니다.
# ###축약 및 생략
# 다음의 경우 작은따옴표와 괄호 등을 사용하여 단어를 축약, 또는 생략할 수 있습니다.
# 특정 개념이나 고유명사를 하나의 콘텐츠에서 여러 번 사용하는 경우
# 단어가 길고 복잡해 가독성이 낮은 경우
# ###두문자어, 두음자어, 약어, 축약어
# 축약 및 생략이 이루어지지 않은 원어 표기 및 이에 대한 설명은 해당 단어가 맨 처음 사용된 곳에서만 이루어집니다. 
# 처음 사용된 이후 해당 단어는 축약 및 생략된 형태로만 사용합니다.
# 축약 및 생략은 로마자 표기, 외국어, 외래어 표기 항목의 부가 설명과 함께 사용할 수 있습니다.
# ###그 외
# 타 사, 또는 타 사의 서비스를 직접적으로 언급하는 대신 해당 회사, 또는 서비스를 설명하는 문구로 대체하여 사용합니다. 
# 콘텐츠의 내용 상 특정 서비스에 대한 언급이 반드시 필요한 경우 해당 서비스의 원 표기법을 준수하여 사용합니다. 
# ##서식
# ###볼드체, 이탤릭체
# 볼드체와 이탤릭체의 사용은 선택사항으로 콘텐츠 작업자의 취향에 맞게 사용할 수 있습니다.
# 특정 단어, 또는 문장을 강조하고 싶을 때 볼드체를 사용합니다.
# 외래어가 아닌 외국어(영어, 라틴어, 스페인어, 독일어 등)나 특정 작품의 제목 등을 강조하고 싶을 때 이탤릭체를 사용합니다.
# 볼드체와 이탤릭체를 사용하는 경우 강조의 의미로 사용하는 작은따옴표는 사용하지 않습니다.
# 하나의 콘텐츠 안에서 볼드체와 이탤릭체를 사용하는 부분은 최대 10개를 넘지 않도록 합니다. 볼드체와 이탤릭체가 지나치게 많은 경우 가독성이 떨어지고 강조의 효과가 줄어드는 것을 방지하기 위함입니다.
# ###제목(Heading)
# 제목(Heading, 헤딩) 기능이 지원되는 콘텐츠 작업 환경에서는 제목 기능을 사용해 콘텐츠를 체계적으로 구성합니다.
# 콘텐츠 작업 환경에 따라 제공되는 제목별 폰트 사이즈, 서식 등을 임의로 변경하지 않습니다. 모든 제목에는 볼드체, 이탤릭체를 사용하지 않습니다.
# 제목 기능과 폰트 사이즈 조절 기능이 함께 제공되는 콘텐츠 작업 환경에서는 제목을 통해서만 폰트 사이즈를 조절합니다.
# H1은 사용하지 않습니다.
# 가능한 H5 이하의 제목은 사용하지 않습니다.
# ###개행
# 문장, 또는 문단의 의미가 달라지거나 콘텐츠의 가독성을 높여야하는 경우 콘텐츠 작업자는 임의로 개행을 할 수 있습니다.
# 개행 후 첫 문장의 들여쓰기는 생략합니다. 
# 콘텐츠 작업 환경에 따라 가독성을 위해 문단과 문단 사이 개행은 최대 2회까지 허용합니다. 따라서 문단과 문단 사이에 비어있는 한 줄을 둘 수 있습니다.
# ###글머리 기호(Bullet Point)
# 콘텐츠 내용에 따라 글머리 기호를 사용할 수 있습니다. 글머리 기호는 순서가 없는 글머리 기호(unordered list)와 순서가 있는 글머리 기호(ordered list)를 사용할 수 있습니다.
# 글머리 기호 안의 내용은 문장, 또는 명사형으로 종결되는 구를 사용합니다.
# 콘텐츠 작업 환경에서 글머리기호 기능이 제공되는 경우, 해당 기능을 사용하여 작업합니다. 
# 작업 환경에서 글머리 기호 기능이 제공되지 않는 경우,  •  또는 1. 과 같은 글머리 기호를 의미하는 부호를 직접 사용할 수 있습니다. 이 경우 항목의 위계를 명확하게 확인할 수 있도록 일관된 규칙으로 들여쓰기합니다.
# 순서가 있는 글머리 기호와 순서가 없는 글머리 기호를 서로 섞어서 사용하지 않습니다.
# 글머리 기호 앞에 붙는 부호, 또는 숫자체계는 개별 콘텐츠 작업 환경에 따릅니다. 
# 정해진 양식이 없는 경우는 각각의 글머리 기호의 모양을 다르게 하여 각 기호를 구분합니다.
# 가독성을 위해 모든 글머리 기호는 세 단계를 넘기지 않습니다.
# ###이미지 및 캡션, 각주
# 캡션은 이미지 하단 중앙에 위치하도록 구성합니다. 
# 각주는 각주가 필요한 단어 뒤에 *(별표, 애스터리스크)를 붙인 뒤 해당 단어가 나오는 단락의 맨 아래에 적습니다.
# 각주와 캡션은 본문과 구분되는 글자색과 글자 크기를 사용합니다. 
# 캡션 삽입은 선택사항입니다. 
# ###코드 및 인용
# 코드 및 인용은 에디터 내 서식을 사용합니다. 에디터 내 서식이 별도로 마련되지 않은 경우 반드시 필요한 경우가 아니라면 되도록 사용을 지양합니다.
# 문장 내 코드블럭(Inline codeblock)은 강조의 의미로 사용할 수 있습니다. 단 굵은 글씨와 함께 사용하지 않습니다.
# 일반 코드 블럭은 강조의 의미로 사용하지 않고 코드를 나타내는데만 사용합니다.
# 인용은 다른 사람의 말을 직접 인용하거나 여러 줄의 문장을 강조하는 의미로 사용합니다. 단, 큰따옴표 또는 다른 서식(굵은 글씨, 기울임체 등)과 함께 사용하지 않습니다.
# ###태그
# 태그는 콘텐츠 작업자가 임의로 부여합니다.
# 태그는 10개 이하로 사용합니다.
# 태그가 영어인 경우에는 외국어, 외래어 표기를 준수하며 영어 소문자만 사용합니다.
# 태그에는 -(하이픈)을 제외한 특수문자를 사용할 수 없습니다.
# ##그 외 주의사항
# 가이드라인 상세 항목의 추가, 수정, 삭제 등의 편집이 이루어진 경우, 숨고팀 콘텐츠 담당자는 기준 일자를 해당 편집이 발생한 시점으로 수정합니다. 
# 본 가이드라인의 기준 일자 이전의 숨고팀 콘텐츠에 대해서는 편집된 가이드라인을 소급하여 적용하지 않습니다.

# Imagine yourself as a friendly receptionist with expertise in various company regulations, designed to provide helpful, logical, and structured answers in KOREAN words. Please follow these guidelines:
# Based on the data taken from data above, kindly and kindly explain to the user's message. If you need any additional information when you understand, please let me know based on the data. However, you should NEVER guess the answer that is not in the data. Please make sure to comply with the request. There will be a disadvantage if you DO NOT comply with the request.
# If your data includes examples, please include them in your answer. However, if the examples are incorrect or there are no examples, you should NEVER include guessing examples in your answer.
# Let's think a bit step by step and limit the answer length to 200 words exclude quote, codeblock.
# """