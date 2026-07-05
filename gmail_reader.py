"""Gmail에서 사람인 발신 메일을 IMAP으로 가져오는 모듈."""
import imaplib
import email
from email.header import decode_header
from datetime import datetime, timedelta


def _decode(value: str) -> str:
    """메일 헤더(제목 등)의 인코딩을 풀어서 문자열로 반환."""
    if not value:
        return ""
    out = ""
    for text, enc in decode_header(value):
        if isinstance(text, bytes):
            out += text.decode(enc or "utf-8", errors="replace")
        else:
            out += text
    return out


def _get_html_body(msg) -> str:
    """메일 본문 중 text/html 파트를 우선 추출. 없으면 text/plain."""
    if msg.is_multipart():
        # 1순위: HTML 파트
        for part in msg.walk():
            ctype = part.get_content_type()
            disp = str(part.get("Content-Disposition") or "")
            if ctype == "text/html" and "attachment" not in disp:
                payload = part.get_payload(decode=True)
                if payload:
                    charset = part.get_content_charset() or "utf-8"
                    return payload.decode(charset, errors="replace")
        # 2순위: 텍스트 파트
        for part in msg.walk():
            if part.get_content_type() == "text/plain":
                payload = part.get_payload(decode=True)
                if payload:
                    charset = part.get_content_charset() or "utf-8"
                    return payload.decode(charset, errors="replace")
    else:
        payload = msg.get_payload(decode=True)
        if payload:
            charset = msg.get_content_charset() or "utf-8"
            return payload.decode(charset, errors="replace")
    return ""


def fetch_saramin_emails(address: str, app_password: str,
                         sender: str = "saramin.co.kr",
                         days_back: int = 7) -> list[dict]:
    """사람인 발신 메일들을 [{subject, html}, ...] 형태로 반환."""
    mail = imaplib.IMAP4_SSL("imap.gmail.com", 993)
    mail.login(address, app_password)
    mail.select("INBOX")

    # IMAP 날짜 형식: 01-Jun-2026
    since = (datetime.now() - timedelta(days=days_back)).strftime("%d-%b-%Y")
    status, data = mail.search(None, "FROM", sender, "SINCE", since)

    emails: list[dict] = []
    if status == "OK" and data and data[0]:
        for num in data[0].split():
            status, msg_data = mail.fetch(num, "(RFC822)")
            if status != "OK" or not msg_data or not msg_data[0]:
                continue
            msg = email.message_from_bytes(msg_data[0][1])
            emails.append({
                "subject": _decode(msg.get("Subject")),
                "html": _get_html_body(msg),
            })

    mail.close()
    mail.logout()
    return emails
