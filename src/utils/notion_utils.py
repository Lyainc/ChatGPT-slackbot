import notion_client
import json
from config.config import *

def fetch_notion_data (database_id: str) -> dict:

    app = notion_client.Client(auth=notion_integration_token)
    
    response = app.databases.query(database_id)

    results_list = []

    for result in response['results']:
        time = result['properties']['이동 시간']['rich_text'][0]['text']['content']
        link = result['properties']['링크']['rich_text'][0]['text']['link']['url']
        type = result['properties']['구분']['title'][0]['text']['content']
        name = result['properties']['상호명']['rich_text'][0]['text']['content']
        menu = result['properties']['추천 메뉴']['rich_text'][0]['text']['content']

        result_dict = {
            '상호명': name,
            '구분': type,
            '추천 메뉴': menu,
            '이동 시간': time,
            '링크': link
        }
        
        results_list.append(result_dict)

    json_results = json.dumps(results_list, ensure_ascii=False, indent=4)
    # print(json_results)
    return json_results

