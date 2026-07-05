"""추출한 공고를 Notion 데이터베이스에 한 행씩 추가하는 모듈."""
import requests
from datetime import datetime

NOTION_API = "https://api.notion.com/v1/pages"
# 2022-06-28은 단일 데이터소스 DB에서 가장 안정적으로 동작하는 버전입니다.
# (Notion이 2025-09-03부터 '데이터 소스' 개념을 도입했지만, 일반적인
#  단일 DB에서는 아래 database_id 방식이 그대로 호환됩니다.)
NOTION_VERSION = "2022-06-28"


def add_job_to_notion(token: str, database_id: str, job: dict) -> dict:
    """공고 한 건을 Notion DB에 페이지(행)로 추가."""
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Notion-Version": NOTION_VERSION,
    }

    # DB의 속성(컬럼) 이름과 정확히 일치해야 합니다.
    properties = {
        "Title": {
            "title": [{"text": {"content": job["title"][:2000]}}]
        },
        "URL": {"url": job["url"]},
        "AddedAt": {"date": {"start": datetime.now().isoformat()}},
    }
    if job.get("company"):
        properties["Company"] = {
            "rich_text": [{"text": {"content": job["company"][:2000]}}]
        }

    payload = {
        "parent": {"database_id": database_id},
        "properties": properties,
    }

    resp = requests.post(NOTION_API, headers=headers, json=payload, timeout=30)
    if resp.status_code not in (200, 201):
        raise RuntimeError(f"Notion API {resp.status_code}: {resp.text}")
    return resp.json()
