import notion_client
import json
from concurrent.futures import ThreadPoolExecutor
from config.config import notion_integration_key
from utils.cache import load_cache, save_cache

app = notion_client.Client(auth=notion_integration_key)
cached_data = load_cache()

def fetch_notion_page_data(page_id: str) -> str:
    """
    Notion 페이지의 모든 텍스트를 가져옵니다.
    """
    if page_id in cached_data:
        return cached_data[page_id]

    visited_synced_blocks = set()

    def get_text_recursive(block_id: str) -> str:
        children = app.blocks.children.list(block_id=block_id).get("results", [])
        texts = []

        with ThreadPoolExecutor() as executor:
            futures = {executor.submit(process_block, block): block for block in children}
            for future in futures:
                block_text = future.result()
                if block_text:
                    texts.append(block_text)

        return "\n".join(texts)

    def process_block(block: str) -> str:
        block_type = block['type']
        texts = []

        if block_type in ["paragraph", "heading_1", "heading_2", "heading_3", "bulleted_list_item", "numbered_list_item", "to_do", "toggle", "quote", "callout"]:
            rich_texts = block[block_type]['rich_text']
            plain_text = extract_plain_text(rich_texts)
            texts.append(" ".join(plain_text))

        if block.get('has_children', False):
            texts.append(get_text_recursive(block['id']))

        if block_type in ["column_list", "column"]:
            texts.append(get_text_recursive(block['id']))

        return "\n".join(texts)

    def extract_plain_text(rich_texts: str) -> str:
        """
        rich_text에서 유저 멘션, 링크, synced_block의 텍스트를 추출합니다.
        """
        linked_text = []

        for text in rich_texts:
            if 'mention' in text:
                user_mention = text['mention'].get('user', {})
                if user_mention:
                    linked_text.append(user_mention.get('name', ''))
            elif 'synced_block' in text:
                synced_block_id = text['synced_block']['synced_from']['block_id']
                if synced_block_id not in visited_synced_blocks:
                    visited_synced_blocks.add(synced_block_id)
                    linked_text.append(get_text_from_synced_block(synced_block_id))
            elif 'text' in text:
                text_url = text['text'].get('link', {})
                if text_url:
                    url = text_url.get('url', '')
                    if len(url) == 33 and url.startswith("/"):
                        url = f"https://notion.so/soomgo{url}"
                    if len(url) == 66 and url.startswith("/"):
                        url = f"https://notion.so/soomgo{url}"
                    content = text.get('text', {}).get('content', '')
                    linked_text.append(f"[{content}]({url})")
                else:
                    linked_text.append(text.get('text', {}).get('content', ''))

        return linked_text

    def get_text_from_synced_block(synced_block_id: str) -> str:
        """
        rich_text에서 synced_block의 텍스트를 재귀 호출하여 추출합니다.
        """
        synced_block = app.blocks.retrieve(synced_block_id)
        children = synced_block["synced_block"]["children"]
        plain_texts = []

        for child in children:
            if "callout" in child and "rich_text" in child["callout"]:
                plain_texts.extend(extract_plain_text(child["callout"]["rich_text"]))

        return "\n".join(plain_texts)

    data = get_text_recursive(page_id)

    cached_data[page_id] = data
    save_cache(cached_data)

    return data