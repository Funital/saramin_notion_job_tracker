"""사람인 추천 메일 HTML에서 공고(제목/링크/회사)를 추출하는 모듈.

주의: 사람인 메일의 정확한 HTML 구조는 시점마다 다를 수 있습니다.
처음 한 번은 main.py를 --debug 옵션으로 실행해 debug_email.html을 열어보고,
아래 _looks_like_job_link / _guess_company 규칙을 실제 구조에 맞게 조정하세요.
"""
from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qs


def _looks_like_job_link(href: str) -> bool:
    """사람인 '공고 보기' 링크로 보이는지 판별."""
    if "saramin.co.kr" not in href:
        return False
    return any(k in href for k in ["view", "rec_idx", "idx=", "recommend", "jobs"])


def _guess_company(a_tag) -> str:
    """링크 주변 텍스트에서 회사명을 추정(베스트 에포트).

    회사명은 보통 같은 행(tr)의 옆 셀에 있으므로 tr -> div 순으로 탐색.
    """
    title = a_tag.get_text(strip=True)
    for container in (a_tag.find_parent("tr"), a_tag.find_parent("div")):
        if container is None:
            continue
        for t in container.stripped_strings:
            t = t.strip()
            if t and t not in title and title not in t and 1 < len(t) < 40:
                return t
    return ""


def parse_jobs(html: str) -> list[dict]:
    """메일 HTML에서 공고 목록을 추출.

    반환 예: [{"title": ..., "url": ..., "company": ..., "rec_idx": ...}, ...]
    """
    soup = BeautifulSoup(html, "html.parser")
    jobs: list[dict] = []
    seen_keys: set[str] = set()

    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        if not _looks_like_job_link(href):
            continue

        title = a.get_text(separator=" ", strip=True)
        if not title or len(title) < 2:
            continue

        # 중복 제거 키: rec_idx(공고 고유번호) 우선, 없으면 URL+제목
        q = parse_qs(urlparse(href).query)
        rec_idx = (q.get("rec_idx", [None])[0]
                   or q.get("idx", [None])[0])
        key = rec_idx or (href.split("?")[0] + "|" + title)
        if key in seen_keys:
            continue
        seen_keys.add(key)

        jobs.append({
            "title": title,
            "url": href,
            "company": _guess_company(a),
            "rec_idx": rec_idx,
        })

    return jobs
