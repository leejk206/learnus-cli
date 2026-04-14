# LearnUs Summary Report — Design

**Date:** 2026-04-14
**Status:** Draft — awaiting user review

## Goal

`learnus --summary` 한 번으로 아래 4개 섹션을 터미널에 출력하고
동시에 동일 내용을 Markdown 파일로 저장하는 확장 기능을 추가한다.

**섹션:**

1. **들어야 할 강의 영상** — 미시청 + 지각 기한 미도래, 남은 기한 순
2. **제출해야 할 과제/설문** — 미제출 + 미래 마감, 남은 기한 순
3. **앞으로의 시험/과제 일정** — 오늘 이후의 모든 과제·퀴즈, 날짜 순
4. **과목별 공지 리스트** — "과목공지게시판"의 실제 게시글 제목 + 작성일 + 전체 본문

## Non-Goals

- 자동 실행 / 알림 / 캘린더 연동
- "비교과" 강좌(폭력예방교육 등) 제외 필터 (현재는 모두 포함)
- 공지 게시판 외 게시판(질의응답, 자료실)
- 과거 일정 표시

## Scope of Changes

**기존 동작 유지:** `learnus`, `learnus --upcoming`, `learnus --course`, `learnus --json`은 그대로.
`--summary`는 단독 모드로 동작한다.

**새 플래그:** `--summary`

**동작 순서:**
1. `login()` + `fetch_all()` — 기존과 동일하게 전체 수집
   (새로 추가된 video/feedback/notice 파서 포함)
2. `build_summary(courses, now)` — `SummaryReport` dataclass 생성
3. `render_summary_terminal(report)` — rich 기반 4섹션 터미널 출력
4. `render_summary_markdown(report)` — MD 문자열 반환
5. `reports/YYYYMMDD.md`에 overwrite 저장 (경로는
   `Path(__file__)` 기반으로 프로젝트 루트 아래)
6. `[INFO] 저장됨: <절대경로>` 출력

## Data Models

**새 모델 (`models.py`에 추가):**

```python
@dataclass
class Video:
    title: str
    week: int | None
    starts_at: datetime | None
    ends_at: datetime | None          # 정상 시청 기한
    late_until: datetime | None       # 지각 시청 기한
    watched: bool
    length: str | None                # "40:25"
    url: str

@dataclass
class Feedback:                       # 설문
    title: str
    opens_at: datetime | None
    closes_at: datetime | None
    submitted: bool
    url: str

@dataclass
class NoticePost:                     # 실제 공지 게시글
    title: str
    author: str
    posted_at: datetime | None
    body: str
    url: str
```

**기존 `Notice` dataclass는 제거하고 `NoticePost`로 대체.**
`Course`에 `videos: list[Video]`, `feedbacks: list[Feedback]` 필드 추가.
`notices: list[NoticePost]`로 타입 교체.

**SummaryReport (`summary.py` 신규):**

```python
@dataclass
class VideoItem:
    course_name: str
    video: Video
    days_left: int                    # (late_until or ends_at) - now

@dataclass
class TaskItem:
    course_name: str
    kind: str                         # "과제" | "퀴즈" | "설문"
    title: str
    due_at: datetime
    url: str
    days_left: int

@dataclass
class SummaryReport:
    generated_at: datetime
    videos_to_watch: list[VideoItem]
    pending_submissions: list[TaskItem]
    upcoming_schedule: list[TaskItem]
    notices_by_course: dict[str, list[NoticePost]]
```

## Parsers

**신규 `parsers/_ubstrap.py`:**
여러 활동 타입이 공유하는 `span.text-ubstrap` 파싱 유틸.

```python
def parse_ubstrap(text: str) -> tuple[datetime | None, datetime | None, datetime | None]:
    """returns (start, end, late_until)

    text 예시:
      "2026-04-14 00:00:00 ~ 2026-04-20 23:59:59 (지각 : 2026-04-27 23:59:59)"
    """
```

**신규 `parsers/video.py`:**
- 순수 함수 `parse_videos(course_html: str) -> list[Video]`
- `li.activity.vod` 반복, `span.text-ubstrap`으로 기한 파싱
- `span.autocompletion img alt`에서 "완료함" 판별
- `span.text-info`에서 ", 40:25" 같은 러닝타임 추출
- 섹션(`li.section`)의 `h3.sectionname`에서 주차 숫자 추출 (material 파서 로직 재사용)
- 네트워크 요청 없음

**신규 `parsers/feedback.py`:**
- 순수 함수 `parse_feedbacks(course_html: str) -> list[Feedback]`
- `li.activity.feedback` 반복
- `span.text-ubstrap`이 있으면 시작/종료 파싱
- `span.autocompletion img alt`에서 "완료함" 판별

**교체 `parsers/quiz.py`:**
- `li.activity.quiz` 반복
- `span.text-ubstrap`이 있으면 시작/종료 파싱해 `opens_at`/`closes_at` 채움
- 없으면 제목에서 한국어 날짜 패턴(`4월 9일`, `16:05`) 정규식으로 보조 파싱 시도
- 네트워크 요청 없음 (detail 페이지는 사용자가 완료한 상태만 보여주므로 가치 낮음)

**교체 `parsers/notice.py`:**
- `parse_notices(course_html: str, session) -> list[NoticePost]`
- `li.activity.ubboard` 중 `span.instancename` 텍스트에 "공지"를 포함한 항목만 선택
  (보통 "과목공지게시판" 하나)
- 해당 게시판 URL로 `session.get()` → `table.ubboard_table tbody tr`에서 게시글 행 파싱
  - 셀: 번호 / 제목(+링크) / 작성자 / 작성일 / 조회수
- 각 게시글 링크로 `session.get()` → 본문 추출
  - 본문 컨테이너: 스모크 단계에서 실제 셀렉터 확정
    (후보: `div.ubboard-view`, `div.no-overflow`, `div.board_view`)
- 실패한 게시글은 `body=""`로 반환하고 `[WARN]` 로그, 다른 게시글 계속

## Crawler Changes

`crawler.py`의 `fetch_all`에 3개 호출 추가:

```python
def fetch_all(session):
    courses = fetch_course_list(session)
    for course in courses:
        html = session.get(course.url).text
        course.assignments = _safe(parse_assignments, course.name, "과제", html, session)
        course.videos     = _safe_noarg(parse_videos,     course.name, "강의", html)
        course.feedbacks  = _safe_noarg(parse_feedbacks,  course.name, "설문", html)
        course.materials  = _safe_noarg(parse_materials,  course.name, "자료", html)
        course.quizzes    = _safe_noarg(parse_quizzes,    course.name, "퀴즈", html)
        course.notices    = _safe(parse_notices,          course.name, "공지", html, session)
        time.sleep(RATE_LIMIT_SEC)
    return courses
```

공지 파싱에서만 추가 네트워크 사용 (게시판 목록 1회 + 게시글 본문 N회 per course).
기존 rate limiting은 per-course 단위로 유지되며, notice 파서 내부에서도
게시글 fetch 사이에 0.3s sleep 추가.

## Summary Builder (`summary.py`)

```python
def build_summary(courses: list[Course], now: datetime) -> SummaryReport:
    videos: list[VideoItem] = []
    for c in courses:
        for v in c.videos:
            if v.watched:
                continue
            deadline = v.late_until or v.ends_at
            if deadline is None or deadline < now:
                continue
            days_left = (deadline.date() - now.date()).days
            videos.append(VideoItem(course_name=c.name, video=v, days_left=days_left))
    videos.sort(key=lambda x: x.video.late_until or x.video.ends_at)

    pending: list[TaskItem] = []
    for c in courses:
        for a in c.assignments:
            if a.submitted or a.due_at is None or a.due_at < now:
                continue
            pending.append(TaskItem(c.name, "과제", a.title, a.due_at, a.url,
                                    (a.due_at.date() - now.date()).days))
        for f in c.feedbacks:
            if f.submitted or f.closes_at is None or f.closes_at < now:
                continue
            pending.append(TaskItem(c.name, "설문", f.title, f.closes_at, f.url,
                                    (f.closes_at.date() - now.date()).days))
    pending.sort(key=lambda x: x.due_at)

    upcoming: list[TaskItem] = []
    for c in courses:
        for a in c.assignments:
            if a.due_at is None or a.due_at < now:
                continue
            upcoming.append(TaskItem(c.name, "과제", a.title, a.due_at, a.url,
                                     (a.due_at.date() - now.date()).days))
        for q in c.quizzes:
            due = q.closes_at or q.opens_at
            if due is None or due < now:
                continue
            upcoming.append(TaskItem(c.name, "퀴즈", q.title, due, q.url,
                                     (due.date() - now.date()).days))
    upcoming.sort(key=lambda x: x.due_at)

    notices_by_course = {c.name: sorted(c.notices,
                                         key=lambda p: p.posted_at or datetime.min,
                                         reverse=True)
                         for c in courses if c.notices}

    return SummaryReport(generated_at=now,
                         videos_to_watch=videos,
                         pending_submissions=pending,
                         upcoming_schedule=upcoming,
                         notices_by_course=notices_by_course)
```

## Renderers

**`render.py`에 추가:**

```python
def render_summary_terminal(report: SummaryReport) -> None:
    _console.rule("[bold]1. 들어야 할 강의 영상 (남은 기한 순)")
    for item in report.videos_to_watch:
        _console.print(_video_line(item))
    _console.rule("[bold]2. 제출해야 할 과제/설문 (남은 기한 순)")
    for item in report.pending_submissions:
        _console.print(_task_line(item))
    _console.rule("[bold]3. 앞으로의 시험/과제 일정")
    for item in report.upcoming_schedule:
        _console.print(_task_line(item))
    _console.rule("[bold]4. 과목별 공지")
    for course_name, posts in report.notices_by_course.items():
        _console.print(f"\n[bold cyan]{course_name}[/]")
        for p in posts:
            _console.print(_notice_block(p))
```

**신규 `md_writer.py`:**

```python
def render_summary_markdown(report: SummaryReport) -> str:
    lines: list[str] = []
    lines.append(f"# LearnUs 요약 · {report.generated_at:%Y-%m-%d %H:%M}")
    lines.append("")
    lines.append("## 1. 들어야 할 강의 영상 (남은 기한 순)")
    lines.append("")
    for item in report.videos_to_watch:
        v = item.video
        deadline = v.late_until or v.ends_at
        lines.append(f"- **D-{item.days_left}** · {item.course_name} · `Week {v.week}` · {v.title} ({v.length or '-'})")
        lines.append(f"  - 정상: {v.ends_at:%Y-%m-%d %H:%M} / 지각: {v.late_until:%Y-%m-%d %H:%M}"
                     if v.late_until else f"  - 마감: {deadline:%Y-%m-%d %H:%M}")
    lines.append("")
    lines.append("## 2. 제출해야 할 과제/설문 (남은 기한 순)")
    # ... (task 리스트)
    lines.append("")
    lines.append("## 3. 앞으로의 시험/과제 일정")
    # ... (task 리스트, 이번에는 날짜 앞에)
    lines.append("")
    lines.append("## 4. 과목별 공지")
    for course_name, posts in report.notices_by_course.items():
        lines.append(f"\n### {course_name}\n")
        for p in posts:
            lines.append(f"#### {p.title}")
            lines.append(f"*{p.author} · {p.posted_at:%Y-%m-%d}*")
            lines.append("")
            lines.append(p.body.strip() or "_(본문 없음)_")
            lines.append("")
            lines.append("---")
            lines.append("")
    return "\n".join(lines)
```

## CLI Changes

`cli.py`에 플래그 추가:

```python
summary: bool = typer.Option(False, "--summary", help="4개 섹션 요약 + MD 파일 저장"),
```

`main()` 분기:

```python
if summary:
    from learnus.summary import build_summary
    from learnus.md_writer import render_summary_markdown
    report = build_summary(courses, datetime.now())
    render_summary_terminal(report)
    md = render_summary_markdown(report)
    out_path = _resolve_reports_dir() / f"{datetime.now():%Y%m%d}.md"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(md, encoding="utf-8")
    typer.echo(f"[INFO] 저장됨: {out_path}", err=True)
    return
```

`_resolve_reports_dir()`: `Path(__file__).resolve().parents[2] / "reports"`
(즉 `src/learnus/cli.py`의 `parents[0]=src/learnus`, `parents[1]=src`,
`parents[2]=프로젝트 루트`)

`--summary`가 주어지면 `--upcoming`, `--course`, `--json`은 무시 (단독 모드).

## Error Handling

**부분 실패 허용 원칙 유지:**

| 실패 지점 | 동작 |
|---|---|
| 공지 게시판 GET 실패 | 해당 강좌 `notices=[]`, 경고, 나머지 섹션 정상 |
| 게시글 본문 GET 실패 | 해당 post는 `body=""`, 경고, 제목/날짜는 남김 |
| VOD/Feedback/Quiz ubstrap 파싱 실패 | 기한 필드는 None, 제목/URL은 남김 |
| MD 저장 실패 (권한/디스크) | 터미널 출력은 성공했으므로 `[ERROR]` 경고 후 exit code 1 |

## Testing Strategy

**새 단위 테스트 파일:**
- `tests/test_parse_ubstrap.py` — 여러 포맷(지각 있음/없음/시간만/연월일만) 각각에 대한 파싱 검증
- `tests/test_parse_video.py` — video 파서 + fixture
- `tests/test_parse_feedback.py` — feedback 파서 + fixture
- `tests/test_parse_notice.py` — **재작성**: ubboard 게시판 페이지 + 게시글 상세 fixture 두 개를 MagicMock session으로 먹임
- `tests/test_summary_builder.py` — Course 리스트에서 SummaryReport 기대값 검증 (4섹션 각각의 필터/정렬/경계)
- `tests/test_md_writer.py` — 스냅샷 방식: 고정 입력 → 기대 문자열 `startswith`/`contains` 검증

**기존 테스트 수정:**
- `tests/test_parse_quiz.py` — text-ubstrap 기반으로 확장
- `tests/test_crawler.py` — 새 파서들 호출 추가
- `tests/test_models.py` — Video, Feedback, NoticePost 추가
- `tests/test_render.py` — 기존 render_courses가 새 Course 필드 구조에 대응하는지 확인

**새 fixture:**
- `tests/fixtures/course_page.html` — 기존 HTML에 vod의 text-ubstrap, feedback, ubstrap 있는 퀴즈 추가 보강
- `tests/fixtures/ubboard_list.html` — 게시판 목록
- `tests/fixtures/notice_post.html` — 개별 게시글 본문

**스모크 체크 (Task 12 확장):**
- `learnus --summary` 실행해 4개 섹션 모두 뜨는지 확인
- `reports/20260414.md` 파일이 생성되고 내용이 기대대로인지 확인
- 공지 본문 파싱이 실제 구조에 맞는지 확인 (셀렉터 조정)

## Dependencies

추가 의존성 없음. 기존 `requests`, `beautifulsoup4`, `lxml`, `typer`, `rich`,
`python-dotenv`, `cryptography`만 사용.

## Done Criteria

- `learnus --summary` 단독 실행 시:
  1. 터미널에 4개 섹션이 rich 포맷으로 출력됨
  2. `reports/YYYYMMDD.md` 파일이 생성되고 4개 섹션을 모두 포함
  3. `[INFO] 저장됨: <path>` 메시지가 stderr로 출력
- 동일 날짜에 재실행 시 MD 파일이 overwrite됨
- 부분 실패(한 강좌 공지 게시판 장애 등)가 발생해도 나머지 섹션은 정상 출력
- 전체 `pytest -v` 통과
- 기존 플래그(`learnus`, `--upcoming`, `--course`, `--json`) 동작 유지
