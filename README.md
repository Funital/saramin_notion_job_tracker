# 사람인 추천 메일 → Notion 자동 업로드

Gmail로 오는 사람인 공고 추천 메일을 파싱해서 Notion 데이터베이스에 자동으로 쌓아주는 스크립트입니다. 전부 무료 도구만 사용합니다.

## 동작 구조

```
Gmail(IMAP) → 사람인 메일 수집 → HTML 파싱(공고 추출) → Notion API로 행 추가
```

- `gmail_reader.py` : Gmail에서 사람인 메일 가져오기
- `saramin_parser.py` : 메일 HTML에서 공고(제목/링크/회사) 추출
- `notion_uploader.py` : Notion DB에 한 행씩 추가
- `main.py` : 위 3개를 묶어 실행 + 중복 방지
- `seen_jobs.json` : 이미 올린 공고 기록 (실행하면 자동 생성)

---

## 실행 순서

### 0. VSCode에서 프로젝트 열기
이 폴더(`saramin-to-notion`)를 VSCode로 엽니다. Python 확장(Microsoft)도 설치되어 있으면 좋습니다.

### 1. 파이썬 가상환경 + 라이브러리 설치
VSCode 터미널(``Ctrl+` ``)에서:

```bash
# 가상환경 생성 & 활성화
python -m venv venv

# Windows
venv\Scripts\activate
# macOS / Linux
source venv/bin/activate

# 라이브러리 설치
pip install -r requirements.txt
```

### 2. Gmail 앱 비밀번호 발급
일반 비밀번호로는 IMAP 접속이 안 됩니다. **앱 비밀번호**가 필요합니다.

1. 구글 계정 → 보안 → **2단계 인증**을 먼저 켭니다. (필수)
2. https://myaccount.google.com/apppasswords 접속
3. 앱 이름(예: `saramin-notion`)을 입력하고 생성
4. 표시되는 **16자리 비밀번호**를 복사 (공백 없이)

> Gmail의 IMAP은 기본적으로 켜져 있습니다. 혹시 안 되면 Gmail 설정 → "전달 및 POP/IMAP"에서 IMAP 사용을 확인하세요.

### 3. Notion 준비
**(a) 통합(Integration) 생성**
1. https://www.notion.so/my-integrations → "New integration"
2. 이름 입력 후 생성 → **Internal Integration Token** 복사 (`ntn_...`)

**(b) 데이터베이스 생성**
Notion에서 새 데이터베이스(표)를 만들고 아래 **속성(컬럼)** 을 정확한 이름으로 추가합니다:

| 속성 이름 | 타입 |
|-----------|------|
| `Title`   | 제목(Title) — 기본 제공 |
| `Company` | 텍스트(Text) |
| `URL`     | URL |
| `AddedAt` | 날짜(Date) |

> 속성 이름은 코드와 **대소문자까지 정확히** 일치해야 합니다. 이름을 바꾸려면 `notion_uploader.py`의 `properties`도 함께 수정하세요.

**(c) 통합 연결**
데이터베이스 페이지 우상단 `•••` → "연결(Connections)" → 방금 만든 통합을 선택해 권한을 부여합니다. (이걸 안 하면 403 오류가 납니다.)

**(d) 데이터베이스 ID 복사**
DB를 브라우저에서 열고 URL을 봅니다:
```
https://www.notion.so/워크스페이스/[32자리ID]?v=...
              여기 32자리가 DATABASE_ID
```

### 4. .env 파일 작성
`.env.example`을 복사해 `.env`로 이름을 바꾸고 값을 채웁니다:

```bash
# Windows
copy .env.example .env
# macOS / Linux
cp .env.example .env
```

그리고 `GMAIL_ADDRESS`, `GMAIL_APP_PASSWORD`, `NOTION_TOKEN`, `NOTION_DATABASE_ID`를 입력합니다.

### 5. (한 번만) 파싱 규칙 점검 — 디버그 실행
사람인 메일 HTML 구조는 시점마다 다를 수 있어서, 처음 한 번은 디버그로 확인하는 걸 권장합니다:

```bash
python main.py --debug
```

생성된 `debug_email.html`을 VSCode에서 열어, 공고 링크가 제대로 잡히는지 확인합니다. 공고가 0개로 나오거나 이상하면 `saramin_parser.py`의 `_looks_like_job_link`, `_guess_company` 규칙을 실제 구조에 맞게 조정하세요.

### 6. 정상 실행

```bash
python main.py
```

성공하면 Notion DB에 공고가 행으로 추가됩니다. 같은 공고는 `seen_jobs.json` 덕분에 다시 올라가지 않습니다.

---

## 자동화(주기 실행)

매번 직접 돌리지 않으려면 스케줄러에 등록하세요.

**Windows (작업 스케줄러)**
- "기본 작업 만들기" → 트리거: 매일/매시간 → 동작: 프로그램 시작
- 프로그램: `venv\Scripts\python.exe` (전체 경로)
- 인수: `main.py`
- 시작 위치: 이 프로젝트 폴더 경로

**macOS / Linux (cron)**
```bash
crontab -e
# 매시간 정각 실행 예시 (경로는 본인 환경에 맞게)
0 * * * * cd /path/to/saramin-to-notion && ./venv/bin/python main.py >> run.log 2>&1
```

---

## 문제 해결

- **Gmail 로그인 실패** → 앱 비밀번호(16자리)를 썼는지, 2단계 인증이 켜져 있는지 확인.
- **Notion 403** → 데이터베이스에 통합을 "연결"했는지 확인.
- **Notion 400 (property 오류)** → DB 속성 이름이 `Title/Company/URL/AddedAt`과 정확히 일치하는지 확인.
- **공고 0개** → `--debug`로 HTML을 보고 `saramin_parser.py` 규칙 조정.
