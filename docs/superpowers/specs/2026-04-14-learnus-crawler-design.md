# LearnUs Crawler CLI — Design

**Date:** 2026-04-14
**Status:** Draft — awaiting user review

## Goal

연세대학교 LearnUs (ys.learnus.org, Moodle 기반 LMS) 사이트를 크롤링하여,
현재 수강 중인 모든 강좌의 과제·공지·강의자료·퀴즈 정보를 수집하고
터미널에 보기 좋게 출력하는 수동 실행 CLI 도구를 만든다.

**Scope:** 수집 + 표시만. 알림, 캘린더 동기화, 완료 체크, 자동 실행(cron)은 포함하지 않는다.

## Non-Goals

- 알림 시스템 (이메일/푸시/메신저)
- 외부 캘린더 동기화
- 자동 실행 / 데몬화
- 과제 제출이나 상호작용 기능
- 웹 대시보드

## Constraints

- 로그인은 학번/비밀번호 기반 (2단계 인증 없음)
- 매 실행 시 재로그인 (세션 캐싱 없음)
- `.env`에 자격증명 저장, 코드·로그에 노출 금지
- Python 생태계 사용

## Architecture

```
learnus-cli/
├── .env                  # YONSEI_ID, YONSEI_PW
├── pyproject.toml        # requests, beautifulsoup4, lxml, typer, rich, python-dotenv
├── src/learnus/
│   ├── __init__.py
│   ├── auth.py           # 연세포털 SSO 로그인 → 인증된 requests.Session 반환
│   ├── models.py         # dataclass: Course, Assignment, Notice, Material, Quiz
│   ├── crawler.py        # Session을 받아 강좌 목록과 각 항목 수집
│   ├── parsers/          # HTML → dataclass 순수 함수
│   │   ├── course_list.py
│   │   ├── assignment.py
│   │   ├── notice.py
│   │   ├── material.py
│   │   └── quiz.py
│   ├── render.py         # list[Course] → rich 터미널 출력
│   └── cli.py            # typer 엔트리 (`learnus` 커맨드)
└── tests/
    └── fixtures/         # 캡처한 HTML 스냅샷 (파서 단위 테스트용)
```

### Design Principles

- **`parsers/`는 순수 함수**: HTML 문자열을 받아 dataclass를 반환한다. 네트워크·세션 의존 없음.
  이래야 캡처한 HTML로 독립 테스트가 가능하고, LearnUs HTML이 바뀌면 파서만 국지적으로 고칠 수 있다.
- **`crawler.py`는 조립자 역할**: 인증된 Session으로 URL을 돌며 파서에 HTML을 공급한다.
- **`auth.py`는 Session 생성만 책임**: 성공 시 인증된 `requests.Session` 반환,
  실패 시 원인이 드러나는 예외.
- **의존성 흐름:** `cli → crawler → auth + parsers → models`. `render`는 `cli`에서 직접 호출.

## Auth Module (`auth.py`)

LearnUs 로그인은 연세포털 SSO를 경유하는 다단계 흐름이다.

### Flow

1. `GET https://ys.learnus.org/login.php` → 연세포털 로그인 페이지로 리다이렉트
2. 연세포털 로그인 엔드포인트에 `loginid`, `loginpasswd` POST
3. 응답 리다이렉트/콜백을 따라가면 LearnUs가 `MoodleSession` 쿠키를 내려줌
4. `GET https://ys.learnus.org/`로 대시보드 접근하여 로그인 성공 확인

### Interface

```python
def login(user_id: str, password: str) -> requests.Session:
    """인증된 Session 반환. 실패 시 LoginError 발생."""

class LoginError(Exception):
    """로그인 실패. 메시지에 원인 구분:
    - '자격증명 오류'
    - '네트워크 오류'
    - '예상치 못한 응답' (LearnUs가 HTML을 바꿨을 때)
    """
```

### Implementation Details

- `requests.Session()`으로 리다이렉트/쿠키 자동 처리
- 자격증명은 `.env`에서 로드 (python-dotenv). CLI 인자로는 받지 않음.
- 로그인 성공 판정: 대시보드 HTML에 "로그아웃" 링크나 본인 학번 표시가 있는지 확인.
  HTTP 200만으로는 부족 — 잘못된 비밀번호도 200을 반환한다.
- **세션 캐싱 없음** — 매 실행마다 재로그인.

## Data Models (`models.py`)

```python
@dataclass
class Course:
    id: str              # LearnUs 코스 ID
    name: str            # 예: "자료구조 (001)"
    url: str
    assignments: list[Assignment]
    notices: list[Notice]
    materials: list[Material]
    quizzes: list[Quiz]

@dataclass
class Assignment:
    title: str
    due_at: datetime | None
    submitted: bool
    url: str

@dataclass
class Notice:
    title: str
    posted_at: datetime | None
    url: str

@dataclass
class Material:
    title: str
    week: int | None          # 주차
    posted_at: datetime | None
    kind: str                 # "video" | "file" | "link"
    url: str

@dataclass
class Quiz:
    title: str
    opens_at: datetime | None
    closes_at: datetime | None
    url: str
```

## Crawler Module (`crawler.py`)

```python
def fetch_all(session: requests.Session) -> list[Course]:
    courses = fetch_course_list(session)        # 대시보드에서 수강 강좌 추출
    for course in courses:
        html = session.get(course.url).text     # /course/view.php?id=XXXX
        course.assignments = parse_assignments(html, session)
        course.notices    = parse_notices(html, session)
        course.materials  = parse_materials(html)
        course.quizzes    = parse_quizzes(html)
    return courses
```

- **강좌 페이지 한 장으로 대부분 커버**: Moodle 코스 페이지는 주차별 섹션에
  과제·자료·퀴즈 링크가 모두 렌더링된다. 링크 종류(`mod/assign`, `mod/ubboard`,
  `mod/vod`, `mod/quiz`)로 분기해서 파싱.
- **상세 메타데이터는 추가 요청**: 과제 마감일·제출 여부, 공지 본문·날짜는
  개별 페이지로 GET. 이 경우에만 `session`을 파서에 전달.
- **Rate limiting**: 강좌·항목 루프 사이에 `time.sleep(0.3)` 삽입.

### Parser Responsibilities

- `parse_course_list(html) -> list[Course]` — 메타만, 항목은 비어 있음
- `parse_assignments(html, session) -> list[Assignment]`
- `parse_notices(html, session) -> list[Notice]`
- `parse_materials(html) -> list[Material]`
- `parse_quizzes(html) -> list[Quiz]`

각 파서는 try/except로 감싸 한 영역의 실패가 다른 영역을 오염시키지 않게 한다.

## CLI & Render

### Commands (typer)

```
learnus                       # 모든 강좌의 모든 항목 요약
learnus --upcoming            # 마감/예정인 과제·퀴즈만 정렬해서 flat 출력
learnus --course "자료구조"    # 강좌명 부분일치 필터
learnus --json                # JSON 덤프 (파이프용)
learnus --debug               # 에러 발생 시 traceback + HTML 덤프
```

### 기본 출력 (rich)

```
┏━━ 자료구조 (001) ━━━━━━━━━━━━━━━━━━━━━━━━━━━━
┃ 과제
┃   [ ] HW3: BST 구현           마감 2026-04-20 23:59  (D-6)
┃   [✓] HW2: 연결리스트         제출 완료
┃ 공지
┃   • 중간고사 범위 안내         2026-04-10
┃ 자료
┃   • [video] 7주차 강의 영상    2026-04-12
┃   • [file]  7주차 강의노트.pdf 2026-04-12
┃ 퀴즈
┃   (없음)
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### `--upcoming` 출력

강좌 경계를 무시하고 마감일 순 정렬:

```
D-1  [퀴즈]  알고리즘  | 2주차 퀴즈        마감 2026-04-15 23:59
D-6  [과제]  자료구조  | HW3: BST 구현    마감 2026-04-20 23:59
D-9  [과제]  OS       | Lab2              마감 2026-04-23 23:59
```

### Render Module

- `render.py`는 `list[Course]`를 받아 rich `Console`에 출력. 로직 없이 포매팅만.
- D-day 계산은 render에서 수행. 미래 마감은 `D-N`, 오늘 `D-day`, 지난 건 회색 dim.
- `--json`은 `dataclasses.asdict` + `json.dumps` (datetime은 isoformat).

## Error Handling

**원칙: 부분 실패 허용.** 크롤러는 본질적으로 깨지기 쉽다. "전부 되거나 전부 안 되거나"는 비실용적.

| 실패 지점 | 동작 |
|---|---|
| 로그인 실패 | 즉시 종료, `LoginError`로 원인 명시 |
| 강좌 목록 파싱 실패 | 즉시 종료 — 여기가 깨지면 뒤는 의미 없음 |
| 특정 강좌 GET 실패 | 해당 강좌 skip, 경고 로그, 나머지 계속 |
| 특정 파서 예외 | 해당 영역만 빈 리스트, stderr에 `[WARN] <강좌>/<영역> 파싱 실패: ...`, 다른 영역은 정상 출력 |

- `--debug` 플래그: full traceback 출력 + 실패한 HTML을 `/tmp/learnus-debug-<타임스탬프>.html`에 덤프.
  이 덤프는 그대로 파서 fixture로 승격 가능.

## Testing Strategy

### Unit Tests (핵심)

- 파서 단위 테스트만 자동화 대상.
- `tests/fixtures/`에 실제 LearnUs HTML 스냅샷 저장 (학번·이름 등 민감 정보는 redact).
- pytest로 각 파서 함수에 fixture HTML을 먹여 기대 dataclass 검증.

### Smoke Test (수동)

- auth/crawler는 실제 자격증명으로 `learnus` 한 번 돌려 확인.
- CI에 넣지 않음 — 자격증명 주입 복잡하고 스크래핑 CI는 과하다.

### 구현 순서

파서는 실제 HTML을 보기 전엔 뭘 뽑을지 알 수 없으므로 엄격한 TDD는 부적합.
현실적 순서:

1. auth + crawler의 최소 스켈레톤으로 로그인 + 강좌 한 곳 크롤링
2. `--debug`로 덤프한 HTML을 fixture로 저장
3. fixture 기반으로 파서 테스트 작성 → 파서 구현 → 테스트 통과
4. 나머지 강좌·항목 타입 순차 확장

## Dependencies

- `requests` — HTTP 클라이언트
- `beautifulsoup4` + `lxml` — HTML 파싱
- `typer` — CLI 프레임워크
- `rich` — 터미널 포매팅
- `python-dotenv` — `.env` 로드
- `pytest` (dev) — 파서 테스트
