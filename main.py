"""사람인 추천 메일 -> Notion 자동 업로드 메인 스크립트.

사용법:
    python main.py            # 정상 실행
    python main.py --debug    # 첫 메일 HTML을 debug_email.html로 저장(파싱 규칙 조정용)
"""
import os
import sys
import json
from dotenv import load_dotenv

from gmail_reader import fetch_saramin_emails
from saramin_parser import parse_jobs
from notion_uploader import add_job_to_notion

load_dotenv()

SEEN_FILE = "seen_jobs.json"  # 이미 업로드한 공고 기록(중복 방지)


def load_seen() -> set:
    if os.path.exists(SEEN_FILE):
        with open(SEEN_FILE, "r", encoding="utf-8") as f:
            return set(json.load(f))
    return set()


def save_seen(seen: set) -> None:
    with open(SEEN_FILE, "w", encoding="utf-8") as f:
        json.dump(sorted(seen), f, ensure_ascii=False, indent=2)


def main() -> None:
    debug = "--debug" in sys.argv

    gmail_address = os.getenv("GMAIL_ADDRESS")
    gmail_password = os.getenv("GMAIL_APP_PASSWORD")
    notion_token = os.getenv("NOTION_TOKEN")
    notion_db = os.getenv("NOTION_DATABASE_ID")
    sender = os.getenv("SARAMIN_SENDER", "saramin.co.kr")
    days_back = int(os.getenv("DAYS_BACK", "7"))

    if not all([gmail_address, gmail_password, notion_token, notion_db]):
        print("[오류] .env 파일에 GMAIL/NOTION 값이 모두 채워졌는지 확인하세요.")
        sys.exit(1)

    print(f"[1/3] Gmail에서 사람인 메일 검색 중 (최근 {days_back}일)...")
    emails = fetch_saramin_emails(gmail_address, gmail_password, sender, days_back)
    print(f"      -> 메일 {len(emails)}개 발견")

    if debug and emails:
        with open("debug_email.html", "w", encoding="utf-8") as f:
            f.write(emails[0]["html"])
        print("      -> debug_email.html 저장됨. 열어보고 파싱 규칙을 조정하세요.")

    print("[2/3] 공고 파싱 중...")
    all_jobs = []
    for em in emails:
        all_jobs.extend(parse_jobs(em["html"]))
    print(f"      -> 공고 링크 {len(all_jobs)}개 추출")

    seen = load_seen()
    new_jobs = []
    for job in all_jobs:
        key = job.get("rec_idx") or job["url"]
        if key not in seen:
            new_jobs.append((key, job))

    print(f"[3/3] Notion 업로드 중 (신규 {len(new_jobs)}개)...")
    uploaded = 0
    for key, job in new_jobs:
        try:
            add_job_to_notion(notion_token, notion_db, job)
            seen.add(key)
            uploaded += 1
            print(f"      + {job['title'][:40]}")
        except Exception as e:
            print(f"      ! 실패: {job['title'][:40]} ({e})")

    save_seen(seen)
    skipped = len(all_jobs) - len(new_jobs)
    print(f"\n완료: {uploaded}개 업로드, {skipped}개는 이미 등록됨.")


if __name__ == "__main__":
    main()
