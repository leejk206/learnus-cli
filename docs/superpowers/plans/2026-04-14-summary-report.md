# LearnUs Summary Report Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** `learnus --summary`가 4개 섹션(들어야 할 강의 / 제출해야 할 과제·설문 / 앞으로의 시험·과제 일정 / 과목별 공지)을 터미널에 출력하고 동시에 `reports/YYYYMMDD.md`로 저장.

**Architecture:** 순수 HTML 파서(video/feedback/quiz 확장/notice 재작성) → `SummaryReport` dataclass (summary.py 빌더) → 터미널 renderer + MD writer 두 개가 같은 데이터 소비. 실제 LearnUs DOM 구조는 이미 탐색되어 셀렉터가 확정됨.

**Tech Stack:** Python 3.11+, requests, beautifulsoup4, lxml, typer, rich, python-dotenv, pytest

---

## File Structure

```
src/learnus/
├── models.py                 [MODIFY] add Video, Feedback, NoticePost; replace Notice
├── crawler.py                [MODIFY] wire new parsers
├── summary.py                [NEW]    SummaryReport + build_summary
├── render.py                 [MODIFY] add render_summary_terminal
├── md_writer.py              [NEW]    render_summary_markdown
├── cli.py                    [MODIFY] add --summary flag
└── parsers/
    ├── _ubstrap.py           [NEW]    parse_ubstrap shared util
    ├── video.py              [NEW]    parse_videos
    ├── feedback.py           [NEW]    parse_feedbacks (uses availabilityinfo)
    ├── quiz.py               [MODIFY] fetch detail page for dates
    └── notice.py             [REWRITE] list ubboard posts + fetch body

tests/
├── fixtures/
│   ├── course_page.html      [MODIFY] add vod ubstrap, feedback availinfo
│   ├── quiz_detail.html      [NEW]    quiz open/close dates
│   ├── feedback_activity.html [NEW]    isolated feedback li
│   ├── ubboard_list.html     [NEW]    board post list table
│   └── notice_post.html      [NEW]    individual post page
├── test_models.py            [MODIFY]
├── test_parse_ubstrap.py     [NEW]
├── test_parse_video.py       [NEW]
├── test_parse_feedback.py    [NEW]
├── test_parse_quiz.py        [MODIFY] detail fetch
├── test_parse_notice.py      [REWRITE]
├── test_summary.py           [NEW]
├── test_md_writer.py         [NEW]
├── test_crawler.py           [MODIFY]
└── test_render.py            [MODIFY] update Notice → NoticePost
```

---

## Task 1: Update Data Models

**Files:**
- Modify: `src/learnus/models.py`
- Modify: `tests/test_models.py`

- [ ] **Step 1: Replace models.py content**

`src/learnus/models.py`:
```python
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Assignment:
    title: str
    due_at: datetime | None
    submitted: bool
    url: str


@dataclass
class Video:
    title: str
    week: int | None
    starts_at: datetime | None
    ends_at: datetime | None
    late_until: datetime | None
    watched: bool
    length: str | None
    url: str


@dataclass
class Feedback:
    title: str
    opens_at: datetime | None
    closes_at: datetime | None
    submitted: bool
    url: str


@dataclass
class Material:
    title: str
    week: int | None
    posted_at: datetime | None
    kind: str
    url: str


@dataclass
class Quiz:
    title: str
    opens_at: datetime | None
    closes_at: datetime | None
    url: str


@dataclass
class NoticePost:
    title: str
    author: str
    posted_at: datetime | None
    body: str
    url: str


@dataclass
class Course:
    id: str
    name: str
    url: str
    assignments: list[Assignment] = field(default_factory=list)
    videos: list[Video] = field(default_factory=list)
    feedbacks: list[Feedback] = field(default_factory=list)
    materials: list[Material] = field(default_factory=list)
    quizzes: list[Quiz] = field(default_factory=list)
    notices: list[NoticePost] = field(default_factory=list)
```

- [ ] **Step 2: Replace tests/test_models.py**

```python
from datetime import datetime
from learnus.models import (
    Assignment, Course, Feedback, Material, NoticePost, Quiz, Video,
)


def test_assignment_defaults():
    a = Assignment(title="HW1", due_at=None, submitted=False, url="http://x")
    assert a.title == "HW1"


def test_video_fields():
    v = Video(title="W1 강의", week=1, starts_at=datetime(2026, 4, 14),
              ends_at=datetime(2026, 4, 20), late_until=datetime(2026, 4, 27),
              watched=False, length="40:25", url="http://x")
    assert v.week == 1
    assert v.watched is False
    assert v.length == "40:25"


def test_feedback_fields():
    f = Feedback(title="설문1", opens_at=datetime(2026, 4, 14),
                 closes_at=datetime(2026, 4, 20), submitted=False, url="http://x")
    assert f.submitted is False


def test_notice_post_fields():
    p = NoticePost(title="중간고사 안내", author="이경호",
                   posted_at=datetime(2026, 3, 27, 15, 52),
                   body="본문 내용", url="http://x")
    assert p.author == "이경호"
    assert p.body == "본문 내용"


def test_material_kind_values():
    m = Material(title="강의1", week=1, posted_at=None, kind="video", url="http://x")
    assert m.kind == "video"


def test_quiz_fields():
    q = Quiz(title="퀴즈1", opens_at=datetime(2026, 4, 14),
             closes_at=datetime(2026, 4, 15), url="http://x")
    assert q.opens_at.day == 14


def test_course_has_all_collections():
    c = Course(id="1", name="자료구조", url="http://x")
    assert c.assignments == []
    assert c.videos == []
    assert c.feedbacks == []
    assert c.materials == []
    assert c.quizzes == []
    assert c.notices == []
```

- [ ] **Step 3: Run tests**

Run: `pytest tests/test_models.py -v`
Expected: 7 passed

- [ ] **Step 4: Commit**

```bash
git add src/learnus/models.py tests/test_models.py
git commit -m "feat(models): add Video, Feedback, NoticePost; replace Notice"
```

Note: This breaks other tests (render, crawler) temporarily. They'll be fixed in their own tasks.

---

## Task 2: ubstrap Shared Parser

**Files:**
- Create: `src/learnus/parsers/_ubstrap.py`
- Test: `tests/test_parse_ubstrap.py`

- [ ] **Step 1: Write failing tests**

`tests/test_parse_ubstrap.py`:
```python
from datetime import datetime
from learnus.parsers._ubstrap import parse_ubstrap


def test_full_with_late():
    text = "2026-04-14 00:00:00 ~ 2026-04-20 23:59:59 (지각 : 2026-04-27 23:59:59)"
    start, end, late = parse_ubstrap(text)
    assert start == datetime(2026, 4, 14, 0, 0, 0)
    assert end == datetime(2026, 4, 20, 23, 59, 59)
    assert late == datetime(2026, 4, 27, 23, 59, 59)


def test_without_late():
    text = "2026-03-03 00:00:00 ~ 2026-03-09 23:59:59"
    start, end, late = parse_ubstrap(text)
    assert start == datetime(2026, 3, 3)
    assert end == datetime(2026, 3, 9, 23, 59, 59)
    assert late is None


def test_empty_returns_all_none():
    assert parse_ubstrap("") == (None, None, None)


def test_malformed_returns_all_none():
    assert parse_ubstrap("언젠가 마감") == (None, None, None)
```

- [ ] **Step 2: Run test to confirm failure**

Run: `pytest tests/test_parse_ubstrap.py -v`
Expected: FAIL with ImportError

- [ ] **Step 3: Implement parser**

`src/learnus/parsers/_ubstrap.py`:
```python
import re
from datetime import datetime

_DATE_RE = re.compile(r"(\d{4})-(\d{2})-(\d{2})\s+(\d{2}):(\d{2}):(\d{2})")
_LATE_RE = re.compile(r"지각\s*:\s*(\d{4})-(\d{2})-(\d{2})\s+(\d{2}):(\d{2}):(\d{2})")


def parse_ubstrap(text: str) -> tuple[datetime | None, datetime | None, datetime | None]:
    """Parse span.text-ubstrap content.

    Examples:
      "2026-04-14 00:00:00 ~ 2026-04-20 23:59:59 (지각 : 2026-04-27 23:59:59)"
      "2026-04-14 00:00:00 ~ 2026-04-20 23:59:59"
    """
    if not text:
        return None, None, None
    dates = _DATE_RE.findall(text)
    if len(dates) < 2:
        return None, None, None
    start = _tuple_to_dt(dates[0])
    end = _tuple_to_dt(dates[1])
    late = None
    late_m = _LATE_RE.search(text)
    if late_m:
        late = _tuple_to_dt(late_m.groups())
    return start, end, late


def _tuple_to_dt(t) -> datetime:
    y, mo, d, h, mi, s = (int(x) for x in t)
    return datetime(y, mo, d, h, mi, s)
```

- [ ] **Step 4: Run tests**

Run: `pytest tests/test_parse_ubstrap.py -v`
Expected: 4 passed

- [ ] **Step 5: Commit**

```bash
git add src/learnus/parsers/_ubstrap.py tests/test_parse_ubstrap.py
git commit -m "feat(parser): add ubstrap shared parser for activity time ranges"
```

---

## Task 3: Video Parser

**Files:**
- Create: `src/learnus/parsers/video.py`
- Test: `tests/test_parse_video.py`
- Modify: `tests/fixtures/course_page.html`

- [ ] **Step 1: Extend course_page.html fixture with real vod structure**

Replace `tests/fixtures/course_page.html`:
```html
<!DOCTYPE html>
<html>
<body>
<ul class="topics">
  <li class="section" data-section="1">
    <h3 class="sectionname">1주차</h3>
    <ul class="section img-text">
      <li class="activity assign modtype_assign" id="module-11111">
        <div class="activityinstance">
          <a href="https://ys.learnus.org/mod/assign/view.php?id=11111">
            <span class="instancename">HW1: 배열 구현<span class="accesshide"> 과제</span></span>
          </a>
        </div>
      </li>
      <li class="activity vod modtype_vod" id="module-22222">
        <div class="activityinstance">
          <a href="https://ys.learnus.org/mod/vod/view.php?id=22222">
            <span class="instancename">1주차 강의 영상<span class="accesshide"> 동영상</span></span>
          </a>
          <span class="displayoptions">
            <span class="text-ubstrap">
              2026-03-03 00:00:00 ~ 2026-03-09 23:59:59
              <span class="text-late">(지각 : 2026-03-16 23:59:59)</span>
            </span>
            <span class="text-info">, 40:25</span>
          </span>
        </div>
        <span class="actions"><span class="autocompletion">
          <img alt="완료함: 1주차 강의 영상" class="icon"/>
        </span></span>
      </li>
      <li class="activity ubfile modtype_ubfile" id="module-33333">
        <div class="activityinstance">
          <a href="https://ys.learnus.org/mod/ubfile/view.php?id=33333">
            <span class="instancename">1주차 강의노트.pdf<span class="accesshide"> 파일</span></span>
          </a>
        </div>
      </li>
    </ul>
  </li>
  <li class="section" data-section="2">
    <h3 class="sectionname">2주차</h3>
    <ul class="section img-text">
      <li class="activity assign modtype_assign" id="module-44444">
        <div class="activityinstance">
          <a href="https://ys.learnus.org/mod/assign/view.php?id=44444">
            <span class="instancename">HW2: 연결리스트<span class="accesshide"> 과제</span></span>
          </a>
        </div>
      </li>
      <li class="activity vod modtype_vod" id="module-55555">
        <div class="activityinstance">
          <a href="https://ys.learnus.org/mod/vod/view.php?id=55555">
            <span class="instancename">2주차 강의 영상<span class="accesshide"> 동영상</span></span>
          </a>
          <span class="displayoptions">
            <span class="text-ubstrap">2026-04-14 00:00:00 ~ 2026-04-20 23:59:59 <span class="text-late">(지각 : 2026-04-27 23:59:59)</span></span>
            <span class="text-info">, 25:10</span>
          </span>
        </div>
        <span class="actions"><span class="autocompletion">
          <img alt="완료하지 못함: 2주차 강의 영상" class="icon"/>
        </span></span>
      </li>
      <li class="activity ubboard modtype_ubboard" id="module-66666">
        <div class="activityinstance">
          <a href="https://ys.learnus.org/mod/ubboard/view.php?id=66666">
            <span class="instancename">과목공지게시판<span class="accesshide"> 공지</span></span>
          </a>
        </div>
      </li>
      <li class="activity quiz modtype_quiz" id="module-77777">
        <div class="activityinstance">
          <a href="https://ys.learnus.org/mod/quiz/view.php?id=77777">
            <span class="instancename">2주차 퀴즈<span class="accesshide"> 퀴즈</span></span>
          </a>
        </div>
      </li>
      <li class="activity feedback modtype_feedback" id="module-88888">
        <div class="availabilityinfo">
          다음 조건 하에서만 이용이 가능합니다:
          <ul>
            <li>시작 일시: <strong>2026년 4월 14일</strong></li>
            <li>종료 일시: <strong>2026년 4월 20일</strong></li>
          </ul>
        </div>
        <div class="activityinstance">
          <a href="https://ys.learnus.org/mod/feedback/view.php?id=88888">
            <span class="instancename">강의 만족도 설문<span class="accesshide"> 설문조사</span></span>
          </a>
        </div>
        <span class="actions"><span class="autocompletion">
          <img alt="완료하지 못함: 강의 만족도 설문" class="icon"/>
        </span></span>
      </li>
    </ul>
  </li>
</ul>
</body>
</html>
```

- [ ] **Step 2: Write failing test**

`tests/test_parse_video.py`:
```python
from datetime import datetime
from pathlib import Path

from learnus.parsers.video import parse_videos

FIX = Path(__file__).parent / "fixtures"


def test_parse_videos_extracts_ubstrap_and_watched():
    html = (FIX / "course_page.html").read_text(encoding="utf-8")
    videos = parse_videos(html)

    assert len(videos) == 2

    w1 = next(v for v in videos if v.week == 1)
    assert w1.title == "1주차 강의 영상"
    assert w1.watched is True
    assert w1.starts_at == datetime(2026, 3, 3)
    assert w1.ends_at == datetime(2026, 3, 9, 23, 59, 59)
    assert w1.late_until == datetime(2026, 3, 16, 23, 59, 59)
    assert w1.length == "40:25"
    assert w1.url == "https://ys.learnus.org/mod/vod/view.php?id=22222"

    w2 = next(v for v in videos if v.week == 2)
    assert w2.watched is False
    assert w2.length == "25:10"


def test_parse_videos_empty():
    assert parse_videos("<html></html>") == []
```

- [ ] **Step 3: Run test to confirm failure**

Run: `pytest tests/test_parse_video.py -v`
Expected: FAIL with ImportError

- [ ] **Step 4: Implement parser**

`src/learnus/parsers/video.py`:
```python
import re

from bs4 import BeautifulSoup

from learnus.models import Video
from learnus.parsers._ubstrap import parse_ubstrap


def parse_videos(course_html: str) -> list[Video]:
    soup = BeautifulSoup(course_html, "lxml")
    results: list[Video] = []
    seen: set[str] = set()
    for section in soup.select("li.section"):
        week = _extract_week(section)
        for li in section.select("li.activity.vod"):
            link = li.select_one("div.activityinstance a")
            if not link:
                continue
            url = (link.get("href") or "").strip()
            if not url or url in seen:
                continue
            seen.add(url)
            name_span = link.select_one("span.instancename")
            if not name_span:
                continue
            accesshide = name_span.select_one("span.accesshide")
            if accesshide:
                accesshide.extract()
            title = name_span.get_text(strip=True)

            ubstrap = li.select_one("span.text-ubstrap")
            start = end = late = None
            if ubstrap:
                start, end, late = parse_ubstrap(ubstrap.get_text(" ", strip=True))

            length = None
            info = li.select_one("span.text-info")
            if info:
                length = info.get_text(strip=True).lstrip(", ").strip() or None

            watched = _watched_from_li(li)

            results.append(Video(
                title=title, week=week,
                starts_at=start, ends_at=end, late_until=late,
                watched=watched, length=length, url=url,
            ))
    return results


def _extract_week(section) -> int | None:
    header = section.select_one("h3.sectionname")
    if not header:
        return None
    m = re.search(r"(\d+)\s*주차", header.get_text(strip=True))
    return int(m.group(1)) if m else None


def _watched_from_li(li) -> bool:
    img = li.select_one("span.autocompletion img")
    if not img:
        return False
    alt = img.get("alt", "") or img.get("title", "")
    return "완료함" in alt
```

- [ ] **Step 5: Run tests**

Run: `pytest tests/test_parse_video.py -v`
Expected: 2 passed

- [ ] **Step 6: Commit**

```bash
git add src/learnus/parsers/video.py tests/test_parse_video.py tests/fixtures/course_page.html
git commit -m "feat(parser): add video parser with ubstrap and watched status"
```

---

## Task 4: Feedback Parser

**Files:**
- Create: `src/learnus/parsers/feedback.py`
- Test: `tests/test_parse_feedback.py`

- [ ] **Step 1: Write failing test**

`tests/test_parse_feedback.py`:
```python
from datetime import datetime
from pathlib import Path

from learnus.parsers.feedback import parse_feedbacks

FIX = Path(__file__).parent / "fixtures"


def test_parse_feedbacks_reads_availability_info():
    html = (FIX / "course_page.html").read_text(encoding="utf-8")
    fbs = parse_feedbacks(html)

    assert len(fbs) == 1
    f = fbs[0]
    assert f.title == "강의 만족도 설문"
    assert f.submitted is False
    assert f.opens_at == datetime(2026, 4, 14)
    assert f.closes_at == datetime(2026, 4, 20)
    assert f.url == "https://ys.learnus.org/mod/feedback/view.php?id=88888"


def test_parse_feedbacks_empty():
    assert parse_feedbacks("<html></html>") == []
```

- [ ] **Step 2: Run test**

Run: `pytest tests/test_parse_feedback.py -v`
Expected: FAIL with ImportError

- [ ] **Step 3: Implement parser**

`src/learnus/parsers/feedback.py`:
```python
import re
from datetime import datetime

from bs4 import BeautifulSoup

from learnus.models import Feedback

_KOREAN_DATE_RE = re.compile(
    r"(\d{4})\s*년\s*(\d{1,2})\s*월\s*(\d{1,2})\s*일"
    r"(?:\s*(\d{1,2})\s*시\s*(\d{1,2})\s*분)?"
)


def parse_feedbacks(course_html: str) -> list[Feedback]:
    soup = BeautifulSoup(course_html, "lxml")
    results: list[Feedback] = []
    seen: set[str] = set()
    for li in soup.select("li.activity.feedback"):
        link = li.select_one("div.activityinstance a")
        if not link:
            continue
        url = (link.get("href") or "").strip()
        if not url or url in seen:
            continue
        seen.add(url)
        name_span = link.select_one("span.instancename")
        if not name_span:
            continue
        accesshide = name_span.select_one("span.accesshide")
        if accesshide:
            accesshide.extract()
        title = name_span.get_text(strip=True)

        opens_at, closes_at = _parse_availability(li)
        submitted = _submitted_from_li(li)

        results.append(Feedback(
            title=title, opens_at=opens_at, closes_at=closes_at,
            submitted=submitted, url=url,
        ))
    return results


def _parse_availability(li) -> tuple[datetime | None, datetime | None]:
    info = li.select_one("div.availabilityinfo")
    if not info:
        return None, None
    text = info.get_text(" ", strip=True)
    opens_at = _extract_labeled_date(text, "시작")
    closes_at = _extract_labeled_date(text, "종료")
    return opens_at, closes_at


def _extract_labeled_date(text: str, label: str) -> datetime | None:
    idx = text.find(f"{label} 일시")
    if idx < 0:
        return None
    segment = text[idx:idx + 120]
    m = _KOREAN_DATE_RE.search(segment)
    if not m:
        return None
    y, mo, d, h, mi = m.groups()
    return datetime(int(y), int(mo), int(d), int(h or 0), int(mi or 0))


def _submitted_from_li(li) -> bool:
    img = li.select_one("span.autocompletion img")
    if not img:
        return False
    alt = img.get("alt", "") or img.get("title", "")
    return "완료함" in alt
```

- [ ] **Step 4: Run tests**

Run: `pytest tests/test_parse_feedback.py -v`
Expected: 2 passed

- [ ] **Step 5: Commit**

```bash
git add src/learnus/parsers/feedback.py tests/test_parse_feedback.py
git commit -m "feat(parser): add feedback parser using availabilityinfo block"
```

---

## Task 5: Quiz Parser with Detail Fetch

**Files:**
- Modify: `src/learnus/parsers/quiz.py`
- Create: `tests/fixtures/quiz_detail.html`
- Modify: `tests/test_parse_quiz.py`

- [ ] **Step 1: Create quiz detail fixture**

`tests/fixtures/quiz_detail.html`:
```html
<!DOCTYPE html>
<html>
<body>
<div class="generalbox quizinfo">
  답안 제출 횟수: 1
  시작일시 : 2026-04-13 00:00
  종료일시 : 2026-04-26 23:59
  시간제한: 10 분
</div>
</body>
</html>
```

- [ ] **Step 2: Replace tests/test_parse_quiz.py**

```python
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock

from learnus.parsers.quiz import parse_quizzes

FIX = Path(__file__).parent / "fixtures"


def test_parse_quizzes_fetches_dates_from_detail():
    html = (FIX / "course_page.html").read_text(encoding="utf-8")
    detail = (FIX / "quiz_detail.html").read_text(encoding="utf-8")

    session = MagicMock()
    session.get.return_value.text = detail

    quizzes = parse_quizzes(html, session)
    assert len(quizzes) == 1
    q = quizzes[0]
    assert q.title == "2주차 퀴즈"
    assert q.url == "https://ys.learnus.org/mod/quiz/view.php?id=77777"
    assert q.opens_at == datetime(2026, 4, 13, 0, 0)
    assert q.closes_at == datetime(2026, 4, 26, 23, 59)


def test_parse_quizzes_empty():
    session = MagicMock()
    assert parse_quizzes("<html></html>", session) == []


def test_parse_quizzes_detail_network_error_keeps_title():
    html = (FIX / "course_page.html").read_text(encoding="utf-8")
    session = MagicMock()
    session.get.side_effect = RuntimeError("network down")
    quizzes = parse_quizzes(html, session)
    assert len(quizzes) == 1
    assert quizzes[0].opens_at is None
    assert quizzes[0].closes_at is None
```

- [ ] **Step 3: Replace src/learnus/parsers/quiz.py**

```python
import re
from datetime import datetime

from bs4 import BeautifulSoup

from learnus.models import Quiz

_OPEN_RE = re.compile(r"시작일시\s*:\s*(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2})")
_CLOSE_RE = re.compile(r"종료일시\s*:\s*(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2})")


def parse_quizzes(course_html: str, session) -> list[Quiz]:
    soup = BeautifulSoup(course_html, "lxml")
    results: list[Quiz] = []
    seen: set[str] = set()
    for li in soup.select("li.activity.quiz"):
        link = li.select_one("div.activityinstance a")
        if not link:
            continue
        url = (link.get("href") or "").strip()
        if not url or url in seen:
            continue
        seen.add(url)
        name_span = link.select_one("span.instancename")
        if not name_span:
            continue
        accesshide = name_span.select_one("span.accesshide")
        if accesshide:
            accesshide.extract()
        title = name_span.get_text(strip=True)

        opens_at, closes_at = _fetch_dates(session, url)
        results.append(Quiz(title=title, opens_at=opens_at, closes_at=closes_at, url=url))
    return results


def _fetch_dates(session, url: str) -> tuple[datetime | None, datetime | None]:
    try:
        resp = session.get(url, timeout=15)
    except Exception:
        return None, None
    soup = BeautifulSoup(resp.text, "lxml")
    for box in soup.select("div.generalbox"):
        text = box.get_text(" ", strip=True)
        opens = _match(_OPEN_RE, text)
        closes = _match(_CLOSE_RE, text)
        if opens or closes:
            return opens, closes
    return None, None


def _match(pattern: re.Pattern, text: str) -> datetime | None:
    m = pattern.search(text)
    if not m:
        return None
    try:
        return datetime.strptime(m.group(1), "%Y-%m-%d %H:%M")
    except ValueError:
        return None
```

- [ ] **Step 4: Run tests**

Run: `pytest tests/test_parse_quiz.py -v`
Expected: 3 passed

- [ ] **Step 5: Commit**

```bash
git add src/learnus/parsers/quiz.py tests/test_parse_quiz.py tests/fixtures/quiz_detail.html
git commit -m "feat(parser): quiz parser fetches open/close dates from detail page"
```

---

## Task 6: Notice Parser Rewrite

**Files:**
- Rewrite: `src/learnus/parsers/notice.py`
- Create: `tests/fixtures/ubboard_list.html`
- Create: `tests/fixtures/notice_post.html`
- Rewrite: `tests/test_parse_notice.py`

- [ ] **Step 1: Create ubboard_list.html fixture**

`tests/fixtures/ubboard_list.html`:
```html
<!DOCTYPE html>
<html>
<body>
<table class="ubboard_table table table-hover">
  <thead>
    <tr><th>번호</th><th>제목</th><th>작성자</th><th>작성일</th><th>조회수</th></tr>
  </thead>
  <tbody>
    <tr>
      <td class="tcenter">2</td>
      <td><a href="https://ys.learnus.org/mod/ubboard/article.php?id=66666&amp;bwid=2131715">중간시험 일정 안내</a></td>
      <td class="tcenter">이경호</td>
      <td class="tcenter">2026-03-27</td>
      <td class="tcenter">127</td>
    </tr>
    <tr>
      <td class="tcenter">1</td>
      <td><a href="https://ys.learnus.org/mod/ubboard/article.php?id=66666&amp;bwid=2131711">수강철회 기간 안내</a></td>
      <td class="tcenter">이경호</td>
      <td class="tcenter">2026-03-27</td>
      <td class="tcenter">50</td>
    </tr>
  </tbody>
</table>
</body>
</html>
```

- [ ] **Step 2: Create notice_post.html fixture**

`tests/fixtures/notice_post.html`:
```html
<!DOCTYPE html>
<html>
<body>
<div class="ubboard_view">
  <div class="well">
    <div class="subject"><h3>중간시험 일정 안내</h3></div>
    <div class="info">
      <div class="writer"><span class="title">작성자</span> : 이경호</div>
      <div class="date"><span class="title">작성일</span> : 2026-03-27 15:52 (수정일: 2026-04-09 10:56)</div>
      <div class="hit"><span class="title">조회수</span> : 128</div>
    </div>
    <div class="content">
      <div class="text_to_html">
        <p>중간시험 일정을 아래와 같이 공지합니다.</p>
        <p>1. 일시: 4월 21일(화) 오후 1시 ~ 2시 40분</p>
        <p>2. 장소: 강의실</p>
      </div>
    </div>
  </div>
</div>
</body>
</html>
```

- [ ] **Step 3: Write failing test**

Replace `tests/test_parse_notice.py`:
```python
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock

from learnus.parsers.notice import parse_notices

FIX = Path(__file__).parent / "fixtures"


def test_parse_notices_lists_posts_and_fetches_body():
    course_html = (FIX / "course_page.html").read_text(encoding="utf-8")
    list_html = (FIX / "ubboard_list.html").read_text(encoding="utf-8")
    post_html = (FIX / "notice_post.html").read_text(encoding="utf-8")

    session = MagicMock()

    def fake_get(url, *args, **kwargs):
        resp = MagicMock()
        if "/mod/ubboard/view.php" in url:
            resp.text = list_html
        elif "/mod/ubboard/article.php" in url:
            resp.text = post_html
        else:
            resp.text = "<html></html>"
        return resp

    session.get.side_effect = fake_get

    posts = parse_notices(course_html, session)

    assert len(posts) == 2
    assert posts[0].title == "중간시험 일정 안내"
    assert posts[0].author == "이경호"
    assert posts[0].posted_at == datetime(2026, 3, 27)
    assert "중간시험 일정을 아래와 같이 공지합니다" in posts[0].body
    assert "url=66666" in posts[0].url.replace("id=", "url=") or "bwid=2131715" in posts[0].url


def test_parse_notices_no_notice_board_returns_empty():
    session = MagicMock()
    # Course page with no ubboard named 공지
    html = "<html><body><ul class='topics'></ul></body></html>"
    assert parse_notices(html, session) == []


def test_parse_notices_continues_on_post_fetch_error():
    course_html = (FIX / "course_page.html").read_text(encoding="utf-8")
    list_html = (FIX / "ubboard_list.html").read_text(encoding="utf-8")

    session = MagicMock()
    call_count = {"n": 0}

    def fake_get(url, *args, **kwargs):
        resp = MagicMock()
        if "/mod/ubboard/view.php" in url:
            resp.text = list_html
            return resp
        if "/mod/ubboard/article.php" in url:
            call_count["n"] += 1
            if call_count["n"] == 1:
                raise RuntimeError("boom")
            resp.text = (FIX / "notice_post.html").read_text(encoding="utf-8")
            return resp
        resp.text = "<html></html>"
        return resp

    session.get.side_effect = fake_get
    posts = parse_notices(course_html, session)
    assert len(posts) == 2
    assert posts[0].body == ""  # failed
    assert posts[1].body != ""  # succeeded
```

- [ ] **Step 4: Run test to confirm failure**

Run: `pytest tests/test_parse_notice.py -v`
Expected: FAIL (tests assert new behavior)

- [ ] **Step 5: Rewrite src/learnus/parsers/notice.py**

```python
import re
import sys
import time
from datetime import datetime

from bs4 import BeautifulSoup

from learnus.models import NoticePost

_POST_GAP = 0.3


def parse_notices(course_html: str, session) -> list[NoticePost]:
    board_url = _find_notice_board_url(course_html)
    if not board_url:
        return []
    try:
        list_html = session.get(board_url, timeout=15).text
    except Exception as e:
        print(f"[WARN] 공지 게시판 GET 실패: {e}", file=sys.stderr)
        return []

    post_rows = _extract_post_rows(list_html)
    results: list[NoticePost] = []
    for title, url, author_fallback, date_fallback in post_rows:
        try:
            resp = session.get(url, timeout=15)
            body_title, author, posted_at, body = _parse_post(resp.text)
        except Exception as e:
            print(f"[WARN] 공지 본문 가져오기 실패 ({title}): {e}", file=sys.stderr)
            results.append(NoticePost(
                title=title, author=author_fallback,
                posted_at=_parse_list_date(date_fallback),
                body="", url=url,
            ))
            time.sleep(_POST_GAP)
            continue
        results.append(NoticePost(
            title=body_title or title,
            author=author or author_fallback,
            posted_at=posted_at or _parse_list_date(date_fallback),
            body=body,
            url=url,
        ))
        time.sleep(_POST_GAP)
    return results


def _find_notice_board_url(course_html: str) -> str | None:
    soup = BeautifulSoup(course_html, "lxml")
    for li in soup.select("li.activity.ubboard"):
        link = li.select_one("div.activityinstance a")
        if not link:
            continue
        name = link.select_one("span.instancename")
        if not name:
            continue
        hide = name.select_one("span.accesshide")
        if hide:
            hide.extract()
        title = name.get_text(strip=True)
        if "공지" in title:
            return (link.get("href") or "").strip() or None
    return None


def _extract_post_rows(list_html: str) -> list[tuple[str, str, str, str]]:
    soup = BeautifulSoup(list_html, "lxml")
    table = soup.find("table", class_="ubboard_table")
    if not table:
        return []
    rows: list[tuple[str, str, str, str]] = []
    tbody = table.find("tbody")
    trs = tbody.find_all("tr") if tbody else table.find_all("tr")[1:]
    for tr in trs:
        tds = tr.find_all("td")
        if len(tds) < 4:
            continue
        a = tds[1].find("a")
        if not a:
            continue
        url = (a.get("href") or "").strip()
        title = a.get_text(strip=True)
        author = tds[2].get_text(strip=True)
        date = tds[3].get_text(strip=True)
        if not url or not title:
            continue
        rows.append((title, url, author, date))
    return rows


def _parse_post(html: str) -> tuple[str, str, datetime | None, str]:
    soup = BeautifulSoup(html, "lxml")
    view = soup.select_one("div.ubboard_view")
    if not view:
        return "", "", None, ""
    title_el = view.select_one("div.subject h3")
    title = title_el.get_text(strip=True) if title_el else ""
    writer_el = view.select_one("div.info div.writer")
    author = ""
    if writer_el:
        text = writer_el.get_text(" ", strip=True)
        author = text.split(":", 1)[-1].strip() if ":" in text else text
    date_el = view.select_one("div.info div.date")
    posted_at = None
    if date_el:
        text = date_el.get_text(" ", strip=True)
        m = re.search(r"(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2})", text)
        if m:
            try:
                posted_at = datetime.strptime(m.group(1), "%Y-%m-%d %H:%M")
            except ValueError:
                posted_at = None
    content_el = view.select_one("div.content div.text_to_html") or view.select_one("div.content")
    body = content_el.get_text("\n", strip=True) if content_el else ""
    return title, author, posted_at, body


def _parse_list_date(text: str) -> datetime | None:
    text = (text or "").strip()
    for fmt in ("%Y-%m-%d %H:%M", "%Y-%m-%d"):
        try:
            return datetime.strptime(text, fmt)
        except ValueError:
            continue
    return None
```

- [ ] **Step 6: Run tests**

Run: `pytest tests/test_parse_notice.py -v`
Expected: 3 passed

- [ ] **Step 7: Commit**

```bash
git add src/learnus/parsers/notice.py tests/test_parse_notice.py tests/fixtures/ubboard_list.html tests/fixtures/notice_post.html
git commit -m "feat(parser): rewrite notice parser to list ubboard posts and fetch bodies"
```

---

## Task 7: Wire New Parsers Into Crawler

**Files:**
- Modify: `src/learnus/crawler.py`
- Modify: `tests/test_crawler.py`

- [ ] **Step 1: Update tests/test_crawler.py**

```python
from pathlib import Path
from unittest.mock import MagicMock

from learnus.crawler import fetch_all

FIX = Path(__file__).parent / "fixtures"


def test_fetch_all_populates_courses_with_items():
    dashboard = (FIX / "dashboard.html").read_text(encoding="utf-8")
    course_page = (FIX / "course_page.html").read_text(encoding="utf-8")
    assignment_detail = (FIX / "assignment_detail.html").read_text(encoding="utf-8")
    quiz_detail = (FIX / "quiz_detail.html").read_text(encoding="utf-8")
    ubboard_list = (FIX / "ubboard_list.html").read_text(encoding="utf-8")
    notice_post = (FIX / "notice_post.html").read_text(encoding="utf-8")

    session = MagicMock()

    def fake_get(url, *args, **kwargs):
        resp = MagicMock()
        if url.endswith("ys.learnus.org/") or url.endswith("ys.learnus.org"):
            resp.text = dashboard
        elif "/course/view.php" in url:
            resp.text = course_page
        elif "/mod/assign/view.php" in url:
            resp.text = assignment_detail
        elif "/mod/quiz/view.php" in url:
            resp.text = quiz_detail
        elif "/mod/ubboard/view.php" in url:
            resp.text = ubboard_list
        elif "/mod/ubboard/article.php" in url:
            resp.text = notice_post
        else:
            resp.text = "<html></html>"
        return resp

    session.get.side_effect = fake_get

    courses = fetch_all(session)

    assert len(courses) == 2
    first = courses[0]
    assert len(first.assignments) == 2
    assert len(first.videos) == 2
    assert len(first.feedbacks) == 1
    assert len(first.quizzes) == 1
    assert len(first.notices) == 2
    assert len(first.materials) == 2


def test_fetch_all_continues_on_course_page_error():
    dashboard = (FIX / "dashboard.html").read_text(encoding="utf-8")

    session = MagicMock()
    calls = {"n": 0}

    def fake_get(url, *args, **kwargs):
        resp = MagicMock()
        if "/course/view.php?id=12345" in url:
            raise RuntimeError("boom")
        calls["n"] += 1
        resp.text = dashboard if calls["n"] == 1 else "<html></html>"
        return resp

    session.get.side_effect = fake_get
    courses = fetch_all(session)
    assert len(courses) == 2
    assert courses[0].assignments == []
```

- [ ] **Step 2: Update src/learnus/crawler.py**

```python
import sys
import time

import requests

from learnus.auth import LEARNUS_BASE
from learnus.models import Course
from learnus.parsers.assignment import parse_assignments
from learnus.parsers.course_list import parse_course_list
from learnus.parsers.feedback import parse_feedbacks
from learnus.parsers.material import parse_materials
from learnus.parsers.notice import parse_notices
from learnus.parsers.quiz import parse_quizzes
from learnus.parsers.video import parse_videos

RATE_LIMIT_SEC = 0.3


def fetch_course_list(session: requests.Session) -> list[Course]:
    resp = session.get(LEARNUS_BASE + "/")
    return parse_course_list(resp.text)


def fetch_all(session: requests.Session) -> list[Course]:
    courses = fetch_course_list(session)
    for course in courses:
        try:
            resp = session.get(course.url)
            html = resp.text
        except Exception as e:
            print(f"[WARN] {course.name}: 강좌 페이지 요청 실패: {e}", file=sys.stderr)
            continue

        course.assignments = _safe(parse_assignments, course.name, "과제", html, session)
        course.videos     = _safe_noarg(parse_videos,     course.name, "강의", html)
        course.feedbacks  = _safe_noarg(parse_feedbacks,  course.name, "설문", html)
        course.materials  = _safe_noarg(parse_materials,  course.name, "자료", html)
        course.quizzes    = _safe(parse_quizzes,          course.name, "퀴즈", html, session)
        course.notices    = _safe(parse_notices,          course.name, "공지", html, session)

        time.sleep(RATE_LIMIT_SEC)
    return courses


def _safe(fn, course_name: str, area: str, html: str, session):
    try:
        return fn(html, session)
    except Exception as e:
        print(f"[WARN] {course_name}/{area} 파싱 실패: {e}", file=sys.stderr)
        return []


def _safe_noarg(fn, course_name: str, area: str, html: str):
    try:
        return fn(html)
    except Exception as e:
        print(f"[WARN] {course_name}/{area} 파싱 실패: {e}", file=sys.stderr)
        return []
```

- [ ] **Step 3: Run tests**

Run: `pytest tests/test_crawler.py -v`
Expected: 2 passed

- [ ] **Step 4: Commit**

```bash
git add src/learnus/crawler.py tests/test_crawler.py
git commit -m "feat(crawler): wire video, feedback, quiz (with session), notice (new)"
```

---

## Task 8: Update render.py for New Notice Type

**Files:**
- Modify: `src/learnus/render.py`
- Modify: `tests/test_render.py`

기존 `_append_notices`는 `Notice.title`, `Notice.posted_at`에 의존. 새 `NoticePost`도 같은 필드를 갖고 있어 동작하지만, `test_render.py`의 import를 업데이트해야 함.

- [ ] **Step 1: Update tests/test_render.py**

```python
import json
from datetime import datetime

from learnus.models import Assignment, Course, NoticePost
from learnus.render import render_courses, render_upcoming, render_json


def _sample_courses():
    c1 = Course(
        id="1", name="자료구조", url="http://x",
        assignments=[
            Assignment(title="HW3", due_at=datetime(2026, 4, 20, 23, 59), submitted=False, url="http://x/1"),
            Assignment(title="HW2", due_at=datetime(2026, 4, 10, 23, 59), submitted=True, url="http://x/2"),
        ],
        notices=[NoticePost(title="중간고사 범위", author="홍길동",
                            posted_at=datetime(2026, 4, 10), body="본문", url="http://x/3")],
    )
    c2 = Course(
        id="2", name="운영체제", url="http://y",
        assignments=[
            Assignment(title="Lab2", due_at=datetime(2026, 4, 23, 23, 59), submitted=False, url="http://y/1"),
        ],
    )
    return [c1, c2]


def test_render_courses_contains_course_names(capsys):
    render_courses(_sample_courses())
    out = capsys.readouterr().out
    assert "자료구조" in out
    assert "운영체제" in out
    assert "HW3" in out
    assert "중간고사 범위" in out


def test_render_upcoming_sorts_by_due_date(capsys):
    render_upcoming(_sample_courses(), now=datetime(2026, 4, 14))
    out = capsys.readouterr().out
    hw3_idx = out.index("HW3")
    lab2_idx = out.index("Lab2")
    assert hw3_idx < lab2_idx


def test_render_upcoming_excludes_submitted(capsys):
    render_upcoming(_sample_courses(), now=datetime(2026, 4, 14))
    out = capsys.readouterr().out
    assert "HW2" not in out


def test_render_json_produces_valid_json(capsys):
    render_json(_sample_courses())
    out = capsys.readouterr().out
    data = json.loads(out)
    assert len(data) == 2
    assert data[0]["name"] == "자료구조"
    assert data[0]["assignments"][0]["title"] == "HW3"
    assert data[0]["assignments"][0]["due_at"] == "2026-04-20T23:59:00"
```

- [ ] **Step 2: Run tests**

Run: `pytest tests/test_render.py -v`
Expected: 4 passed (render.py itself is unchanged — only fields that exist in both Notice and NoticePost are used)

- [ ] **Step 3: Commit**

```bash
git add tests/test_render.py
git commit -m "test(render): update notice sample to NoticePost"
```

---

## Task 9: Summary Builder

**Files:**
- Create: `src/learnus/summary.py`
- Test: `tests/test_summary.py`

- [ ] **Step 1: Write failing test**

`tests/test_summary.py`:
```python
from datetime import datetime

from learnus.models import (
    Assignment, Course, Feedback, NoticePost, Quiz, Video,
)
from learnus.summary import SummaryReport, build_summary


NOW = datetime(2026, 4, 14, 10, 0, 0)


def _sample_courses():
    return [
        Course(
            id="1", name="자료구조", url="http://x",
            assignments=[
                Assignment(title="HW3", due_at=datetime(2026, 4, 20, 23, 59),
                           submitted=False, url="http://x/a1"),
                Assignment(title="HW2", due_at=datetime(2026, 4, 10, 23, 59),
                           submitted=True, url="http://x/a2"),
                Assignment(title="HW1", due_at=datetime(2026, 4, 8),
                           submitted=True, url="http://x/a3"),
            ],
            videos=[
                Video(title="W2 강의", week=2,
                      starts_at=datetime(2026, 3, 10), ends_at=datetime(2026, 3, 16, 23, 59, 59),
                      late_until=datetime(2026, 3, 23, 23, 59, 59),
                      watched=False, length="40:25", url="http://x/v1"),
                Video(title="W6 강의", week=6,
                      starts_at=datetime(2026, 4, 14), ends_at=datetime(2026, 4, 20, 23, 59, 59),
                      late_until=datetime(2026, 4, 27, 23, 59, 59),
                      watched=False, length="25:10", url="http://x/v2"),
                Video(title="W1 강의", week=1,
                      starts_at=datetime(2026, 3, 3), ends_at=datetime(2026, 3, 9, 23, 59, 59),
                      late_until=None, watched=True, length="30:00", url="http://x/v3"),
            ],
            feedbacks=[
                Feedback(title="중간 설문", opens_at=datetime(2026, 4, 14),
                         closes_at=datetime(2026, 4, 20), submitted=False, url="http://x/f1"),
            ],
            quizzes=[
                Quiz(title="Q5", opens_at=datetime(2026, 4, 15, 16, 5),
                     closes_at=datetime(2026, 4, 15, 16, 15), url="http://x/q1"),
            ],
            notices=[
                NoticePost(title="공지A", author="교수", posted_at=datetime(2026, 4, 10),
                           body="내용", url="http://x/n1"),
                NoticePost(title="공지B", author="교수", posted_at=datetime(2026, 4, 12),
                           body="내용2", url="http://x/n2"),
            ],
        ),
    ]


def test_videos_to_watch_filters_watched_and_expired():
    report = build_summary(_sample_courses(), now=NOW)
    titles = [item.video.title for item in report.videos_to_watch]
    assert "W6 강의" in titles            # upcoming
    assert "W1 강의" not in titles        # watched
    assert "W2 강의" not in titles        # late_until already passed


def test_videos_sorted_by_deadline():
    courses = _sample_courses()
    courses[0].videos.append(Video(
        title="W7 강의", week=7, starts_at=datetime(2026, 4, 21),
        ends_at=datetime(2026, 4, 27, 23, 59, 59),
        late_until=datetime(2026, 5, 4, 23, 59, 59),
        watched=False, length="20:00", url="http://x/v4",
    ))
    report = build_summary(courses, now=NOW)
    order = [item.video.title for item in report.videos_to_watch]
    assert order == ["W6 강의", "W7 강의"]


def test_pending_submissions_includes_assignment_and_feedback():
    report = build_summary(_sample_courses(), now=NOW)
    kinds = [i.kind for i in report.pending_submissions]
    titles = [i.title for i in report.pending_submissions]
    assert "과제" in kinds
    assert "설문" in kinds
    assert "HW3" in titles
    assert "중간 설문" in titles
    assert "HW2" not in titles  # submitted


def test_upcoming_schedule_includes_quiz_and_future_assignments():
    report = build_summary(_sample_courses(), now=NOW)
    titles = [i.title for i in report.upcoming_schedule]
    kinds = [i.kind for i in report.upcoming_schedule]
    assert "Q5" in titles
    assert "HW3" in titles
    assert "HW1" not in titles  # past
    assert "퀴즈" in kinds
    assert "과제" in kinds


def test_notices_by_course_sorted_latest_first():
    report = build_summary(_sample_courses(), now=NOW)
    posts = report.notices_by_course["자료구조"]
    assert [p.title for p in posts] == ["공지B", "공지A"]


def test_empty_courses_produces_empty_report():
    report = build_summary([], now=NOW)
    assert isinstance(report, SummaryReport)
    assert report.videos_to_watch == []
    assert report.pending_submissions == []
    assert report.upcoming_schedule == []
    assert report.notices_by_course == {}
```

- [ ] **Step 2: Run test**

Run: `pytest tests/test_summary.py -v`
Expected: FAIL with ImportError

- [ ] **Step 3: Implement src/learnus/summary.py**

```python
from dataclasses import dataclass, field
from datetime import datetime

from learnus.models import Course, NoticePost, Video


@dataclass
class VideoItem:
    course_name: str
    video: Video
    days_left: int


@dataclass
class TaskItem:
    course_name: str
    kind: str          # "과제" | "퀴즈" | "설문"
    title: str
    due_at: datetime
    url: str
    days_left: int


@dataclass
class SummaryReport:
    generated_at: datetime
    videos_to_watch: list[VideoItem] = field(default_factory=list)
    pending_submissions: list[TaskItem] = field(default_factory=list)
    upcoming_schedule: list[TaskItem] = field(default_factory=list)
    notices_by_course: dict[str, list[NoticePost]] = field(default_factory=dict)


def build_summary(courses: list[Course], now: datetime) -> SummaryReport:
    report = SummaryReport(generated_at=now)

    for c in courses:
        for v in c.videos:
            if v.watched:
                continue
            deadline = v.late_until or v.ends_at
            if deadline is None or deadline < now:
                continue
            report.videos_to_watch.append(VideoItem(
                course_name=c.name, video=v,
                days_left=(deadline.date() - now.date()).days,
            ))
    report.videos_to_watch.sort(
        key=lambda x: (x.video.late_until or x.video.ends_at or datetime.max)
    )

    for c in courses:
        for a in c.assignments:
            if a.submitted or a.due_at is None or a.due_at < now:
                continue
            report.pending_submissions.append(TaskItem(
                course_name=c.name, kind="과제", title=a.title,
                due_at=a.due_at, url=a.url,
                days_left=(a.due_at.date() - now.date()).days,
            ))
        for f in c.feedbacks:
            if f.submitted or f.closes_at is None or f.closes_at < now:
                continue
            report.pending_submissions.append(TaskItem(
                course_name=c.name, kind="설문", title=f.title,
                due_at=f.closes_at, url=f.url,
                days_left=(f.closes_at.date() - now.date()).days,
            ))
    report.pending_submissions.sort(key=lambda x: x.due_at)

    for c in courses:
        for a in c.assignments:
            if a.due_at is None or a.due_at < now:
                continue
            report.upcoming_schedule.append(TaskItem(
                course_name=c.name, kind="과제", title=a.title,
                due_at=a.due_at, url=a.url,
                days_left=(a.due_at.date() - now.date()).days,
            ))
        for q in c.quizzes:
            due = q.closes_at or q.opens_at
            if due is None or due < now:
                continue
            report.upcoming_schedule.append(TaskItem(
                course_name=c.name, kind="퀴즈", title=q.title,
                due_at=due, url=q.url,
                days_left=(due.date() - now.date()).days,
            ))
    report.upcoming_schedule.sort(key=lambda x: x.due_at)

    for c in courses:
        if not c.notices:
            continue
        report.notices_by_course[c.name] = sorted(
            c.notices,
            key=lambda p: p.posted_at or datetime.min,
            reverse=True,
        )

    return report
```

- [ ] **Step 4: Run tests**

Run: `pytest tests/test_summary.py -v`
Expected: 6 passed

- [ ] **Step 5: Commit**

```bash
git add src/learnus/summary.py tests/test_summary.py
git commit -m "feat(summary): add SummaryReport builder with 4 section filters"
```

---

## Task 10: Markdown Writer

**Files:**
- Create: `src/learnus/md_writer.py`
- Test: `tests/test_md_writer.py`

- [ ] **Step 1: Write failing test**

`tests/test_md_writer.py`:
```python
from datetime import datetime

from learnus.md_writer import render_summary_markdown
from learnus.models import Assignment, Course, Feedback, NoticePost, Quiz, Video
from learnus.summary import build_summary

NOW = datetime(2026, 4, 14, 10, 0, 0)


def _courses():
    return [
        Course(
            id="1", name="자료구조", url="http://x",
            assignments=[
                Assignment(title="HW3", due_at=datetime(2026, 4, 20, 23, 59),
                           submitted=False, url="http://x/a1"),
            ],
            videos=[
                Video(title="W6 강의", week=6,
                      starts_at=datetime(2026, 4, 14), ends_at=datetime(2026, 4, 20, 23, 59, 59),
                      late_until=datetime(2026, 4, 27, 23, 59, 59),
                      watched=False, length="25:10", url="http://x/v1"),
            ],
            feedbacks=[
                Feedback(title="설문", opens_at=datetime(2026, 4, 14),
                         closes_at=datetime(2026, 4, 20), submitted=False, url="http://x/f1"),
            ],
            quizzes=[
                Quiz(title="Q5", opens_at=datetime(2026, 4, 15, 16, 5),
                     closes_at=datetime(2026, 4, 15, 16, 15), url="http://x/q1"),
            ],
            notices=[
                NoticePost(title="공지A", author="교수",
                           posted_at=datetime(2026, 4, 10, 9, 0),
                           body="본문 한 줄\n두 번째 줄", url="http://x/n1"),
            ],
        )
    ]


def test_markdown_has_all_sections():
    md = render_summary_markdown(build_summary(_courses(), now=NOW))
    assert "# LearnUs 요약" in md
    assert "## 1. 들어야 할 강의 영상" in md
    assert "## 2. 제출해야 할 과제/설문" in md
    assert "## 3. 앞으로의 시험/과제 일정" in md
    assert "## 4. 과목별 공지" in md


def test_markdown_contains_items_and_body():
    md = render_summary_markdown(build_summary(_courses(), now=NOW))
    assert "W6 강의" in md
    assert "25:10" in md
    assert "HW3" in md
    assert "Q5" in md
    assert "설문" in md
    assert "공지A" in md
    assert "본문 한 줄" in md
    assert "두 번째 줄" in md


def test_markdown_days_left_formatted():
    md = render_summary_markdown(build_summary(_courses(), now=NOW))
    # HW3 due 2026-04-20 from NOW 2026-04-14 → D-6
    assert "D-6" in md
```

- [ ] **Step 2: Run test**

Run: `pytest tests/test_md_writer.py -v`
Expected: FAIL with ImportError

- [ ] **Step 3: Implement src/learnus/md_writer.py**

```python
from datetime import datetime

from learnus.summary import SummaryReport, TaskItem, VideoItem


def render_summary_markdown(report: SummaryReport) -> str:
    lines: list[str] = []
    lines.append(f"# LearnUs 요약 · {report.generated_at:%Y-%m-%d %H:%M}")
    lines.append("")

    lines.append("## 1. 들어야 할 강의 영상 (남은 기한 순)")
    lines.append("")
    if not report.videos_to_watch:
        lines.append("_없음_")
    else:
        for item in report.videos_to_watch:
            lines.extend(_video_lines(item))
    lines.append("")

    lines.append("## 2. 제출해야 할 과제/설문 (남은 기한 순)")
    lines.append("")
    if not report.pending_submissions:
        lines.append("_없음_")
    else:
        for item in report.pending_submissions:
            lines.append(_task_line_with_dday(item))
    lines.append("")

    lines.append("## 3. 앞으로의 시험/과제 일정")
    lines.append("")
    if not report.upcoming_schedule:
        lines.append("_없음_")
    else:
        for item in report.upcoming_schedule:
            lines.append(_task_line_with_date(item))
    lines.append("")

    lines.append("## 4. 과목별 공지")
    lines.append("")
    if not report.notices_by_course:
        lines.append("_없음_")
    else:
        for course_name, posts in report.notices_by_course.items():
            lines.append(f"### {course_name}")
            lines.append("")
            for p in posts:
                lines.append(f"#### {p.title}")
                date_str = f"{p.posted_at:%Y-%m-%d}" if p.posted_at else "날짜 미상"
                lines.append(f"*{p.author} · {date_str}*")
                lines.append("")
                body = p.body.strip() if p.body else ""
                lines.append(body or "_(본문 없음)_")
                lines.append("")
                lines.append("---")
                lines.append("")
    return "\n".join(lines)


def _video_lines(item: VideoItem) -> list[str]:
    v = item.video
    week = f"Week {v.week}" if v.week is not None else "주차 미상"
    length = v.length or "-"
    dday = _format_dday(item.days_left)
    head = f"- **{dday}** · {item.course_name} · `{week}` · {v.title} ({length})"
    lines = [head]
    if v.late_until and v.ends_at:
        lines.append(
            f"  - 정상: {v.ends_at:%Y-%m-%d %H:%M} / 지각: {v.late_until:%Y-%m-%d %H:%M}"
        )
    elif v.ends_at:
        lines.append(f"  - 마감: {v.ends_at:%Y-%m-%d %H:%M}")
    elif v.late_until:
        lines.append(f"  - 지각 마감: {v.late_until:%Y-%m-%d %H:%M}")
    return lines


def _task_line_with_dday(item: TaskItem) -> str:
    dday = _format_dday(item.days_left)
    return (
        f"- **{dday}** · [{item.kind}] {item.course_name} · {item.title} · "
        f"마감 {item.due_at:%Y-%m-%d %H:%M}"
    )


def _task_line_with_date(item: TaskItem) -> str:
    return (
        f"- **{item.due_at:%Y-%m-%d %H:%M}** · [{item.kind}] {item.course_name} · {item.title}"
    )


def _format_dday(days_left: int) -> str:
    if days_left > 0:
        return f"D-{days_left}"
    if days_left == 0:
        return "D-day"
    return f"D+{-days_left}"
```

- [ ] **Step 4: Run tests**

Run: `pytest tests/test_md_writer.py -v`
Expected: 3 passed

- [ ] **Step 5: Commit**

```bash
git add src/learnus/md_writer.py tests/test_md_writer.py
git commit -m "feat(md): add markdown writer for summary report"
```

---

## Task 11: Terminal Summary Renderer + CLI Flag

**Files:**
- Modify: `src/learnus/render.py`
- Modify: `src/learnus/cli.py`
- Modify: `tests/test_cli.py`

- [ ] **Step 1: Add render_summary_terminal to render.py**

Append to `src/learnus/render.py`:
```python
from learnus.summary import SummaryReport, TaskItem, VideoItem


def render_summary_terminal(report: SummaryReport) -> None:
    _console.rule("[bold]1. 들어야 할 강의 영상 (남은 기한 순)")
    if not report.videos_to_watch:
        _console.print("[dim](없음)[/]")
    for item in report.videos_to_watch:
        _console.print(_format_video_line(item))

    _console.rule("[bold]2. 제출해야 할 과제/설문 (남은 기한 순)")
    if not report.pending_submissions:
        _console.print("[dim](없음)[/]")
    for item in report.pending_submissions:
        _console.print(_format_task_line_dday(item))

    _console.rule("[bold]3. 앞으로의 시험/과제 일정")
    if not report.upcoming_schedule:
        _console.print("[dim](없음)[/]")
    for item in report.upcoming_schedule:
        _console.print(_format_task_line_date(item))

    _console.rule("[bold]4. 과목별 공지")
    if not report.notices_by_course:
        _console.print("[dim](없음)[/]")
    for course_name, posts in report.notices_by_course.items():
        _console.print(f"\n[bold cyan]{course_name}[/]")
        for p in posts:
            date_str = f"{p.posted_at:%Y-%m-%d}" if p.posted_at else "날짜 미상"
            _console.print(f"  • [bold]{p.title}[/]  [dim]({p.author} · {date_str})[/]")
            body = (p.body or "").strip()
            if body:
                for line in body.split("\n"):
                    _console.print(f"      {line}")
            _console.print()


def _format_video_line(item: VideoItem) -> str:
    v = item.video
    dday = _format_dday_compact(item.days_left)
    week = f"W{v.week}" if v.week is not None else "W?"
    length = v.length or "-"
    deadline = v.late_until or v.ends_at
    deadline_str = f"{deadline:%Y-%m-%d %H:%M}" if deadline else "-"
    return f"{dday}  [{week}] {item.course_name}  | {v.title} ({length})  ~{deadline_str}"


def _format_task_line_dday(item: TaskItem) -> str:
    dday = _format_dday_compact(item.days_left)
    return (
        f"{dday}  [{item.kind}]  {item.course_name}  | {item.title}  "
        f"마감 {item.due_at:%Y-%m-%d %H:%M}"
    )


def _format_task_line_date(item: TaskItem) -> str:
    return (
        f"{item.due_at:%Y-%m-%d %H:%M}  [{item.kind}]  {item.course_name}  | {item.title}"
    )


def _format_dday_compact(days_left: int) -> str:
    if days_left > 0:
        return f"D-{days_left}"
    if days_left == 0:
        return "D-day"
    return f"D+{-days_left}"
```

- [ ] **Step 2: Update src/learnus/cli.py**

Replace full content:
```python
import os
import sys
import traceback
from datetime import datetime
from pathlib import Path

import typer
from dotenv import load_dotenv

from learnus.auth import LoginError, login
from learnus.crawler import fetch_all
from learnus.md_writer import render_summary_markdown
from learnus.render import (
    render_courses,
    render_json,
    render_summary_terminal,
    render_upcoming,
)
from learnus.summary import build_summary

app = typer.Typer(add_completion=False, help="LearnUs crawler CLI")


@app.command()
def main(
    upcoming: bool = typer.Option(False, "--upcoming", help="마감 예정 과제/퀴즈만 flat 출력"),
    course: str = typer.Option("", "--course", help="강좌명 부분일치 필터"),
    json_output: bool = typer.Option(False, "--json", help="JSON 덤프"),
    summary: bool = typer.Option(False, "--summary", help="4섹션 요약 + MD 저장"),
    debug: bool = typer.Option(False, "--debug", help="에러 시 traceback"),
) -> None:
    load_dotenv()
    user_id = os.getenv("YONSEI_ID", "")
    password = os.getenv("YONSEI_PW", "")

    if not user_id or not password:
        typer.echo("[ERROR] YONSEI_ID / YONSEI_PW가 .env에 없습니다.", err=True)
        raise typer.Exit(code=2)

    try:
        session = login(user_id, password)
    except LoginError as e:
        typer.echo(f"[ERROR] 로그인 실패: {e}", err=True)
        if debug:
            traceback.print_exc()
        raise typer.Exit(code=1)

    try:
        courses = fetch_all(session)
    except Exception as e:
        typer.echo(f"[ERROR] 크롤링 실패: {e}", err=True)
        if debug:
            traceback.print_exc()
        raise typer.Exit(code=1)

    if summary:
        now = datetime.now()
        report = build_summary(courses, now)
        render_summary_terminal(report)
        md = render_summary_markdown(report)
        out_dir = _reports_dir()
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / f"{now:%Y%m%d}.md"
        try:
            out_path.write_text(md, encoding="utf-8")
        except OSError as e:
            typer.echo(f"[ERROR] MD 저장 실패: {e}", err=True)
            raise typer.Exit(code=1)
        typer.echo(f"[INFO] 저장됨: {out_path}", err=True)
        return

    if course:
        courses = [c for c in courses if course in c.name]

    if json_output:
        render_json(courses)
    elif upcoming:
        render_upcoming(courses)
    else:
        render_courses(courses)


def _reports_dir() -> Path:
    return Path(__file__).resolve().parents[2] / "reports"


if __name__ == "__main__":
    app()
```

- [ ] **Step 3: Update tests/test_cli.py**

```python
import json
from pathlib import Path
from unittest.mock import patch

from typer.testing import CliRunner

from learnus.cli import app
from learnus.models import Assignment, Course

runner = CliRunner()


def _fake_courses():
    return [
        Course(
            id="1", name="자료구조", url="http://x",
            assignments=[Assignment(title="HW1", due_at=None, submitted=False, url="http://x/1")],
        )
    ]


def test_cli_default_runs():
    with patch("learnus.cli.login") as m_login, \
         patch("learnus.cli.fetch_all", return_value=_fake_courses()):
        m_login.return_value = object()
        result = runner.invoke(app, [], env={"YONSEI_ID": "x", "YONSEI_PW": "y"})
    assert result.exit_code == 0
    assert "자료구조" in result.stdout


def test_cli_json_flag_outputs_json():
    with patch("learnus.cli.login") as m_login, \
         patch("learnus.cli.fetch_all", return_value=_fake_courses()):
        m_login.return_value = object()
        result = runner.invoke(app, ["--json"], env={"YONSEI_ID": "x", "YONSEI_PW": "y"})
    assert result.exit_code == 0
    data = json.loads(result.stdout)
    assert data[0]["name"] == "자료구조"


def test_cli_course_filter_narrows_output():
    with patch("learnus.cli.login") as m_login, \
         patch("learnus.cli.fetch_all", return_value=_fake_courses()):
        m_login.return_value = object()
        result = runner.invoke(app, ["--course", "없는과목"],
                                env={"YONSEI_ID": "x", "YONSEI_PW": "y"})
    assert result.exit_code == 0
    assert "자료구조" not in result.stdout


def test_cli_missing_credentials_exits_nonzero():
    result = runner.invoke(app, [], env={"YONSEI_ID": "", "YONSEI_PW": ""})
    assert result.exit_code != 0


def test_cli_summary_writes_md_file(tmp_path, monkeypatch):
    monkeypatch.setattr("learnus.cli._reports_dir", lambda: tmp_path)
    with patch("learnus.cli.login") as m_login, \
         patch("learnus.cli.fetch_all", return_value=_fake_courses()):
        m_login.return_value = object()
        result = runner.invoke(app, ["--summary"],
                                env={"YONSEI_ID": "x", "YONSEI_PW": "y"})
    assert result.exit_code == 0
    md_files = list(tmp_path.glob("*.md"))
    assert len(md_files) == 1
    content = md_files[0].read_text(encoding="utf-8")
    assert "# LearnUs 요약" in content
    assert "## 1. 들어야 할 강의 영상" in content
```

- [ ] **Step 4: Run tests**

Run: `pytest tests/test_cli.py -v`
Expected: 5 passed

- [ ] **Step 5: Run full suite**

Run: `pytest -v`
Expected: all tests pass

- [ ] **Step 6: Commit**

```bash
git add src/learnus/render.py src/learnus/cli.py tests/test_cli.py
git commit -m "feat(cli): add --summary flag with terminal render and MD save"
```

---

## Task 12: Smoke Test with Real Credentials

이 태스크는 실제 LearnUs 계정으로 `--summary` 동작을 검증한다.

**Files:**
- Potentially modify: `src/learnus/parsers/*.py`, fixtures

- [ ] **Step 1: Run `learnus --summary`**

Run: `cd /home/student/projects/learnus-cli && learnus --summary`

Expected:
- 터미널에 4섹션이 rich 포맷으로 출력
- `reports/YYYYMMDD.md` 파일 생성
- `[INFO] 저장됨: ...` 메시지

- [ ] **Step 2: Inspect generated MD**

Run: `cat reports/$(date +%Y%m%d).md | head -60`
Expected: 4개 섹션 헤더 존재, 실제 데이터 포함

- [ ] **Step 3: Diagnose failures**

만약 어떤 섹션이 비어 있다면:

1. **강의 영상 섹션 빔** → 강좌 페이지 HTML 캡처 후 실제 `span.text-ubstrap` 구조 비교. 파서의 셀렉터 조정.
2. **설문 섹션 빔** → `div.availabilityinfo` 구조 비교. 한국어 날짜 정규식 조정.
3. **퀴즈 날짜가 비어 있음** → `div.generalbox` 셀렉터 또는 `시작일시 :` 텍스트 패턴 조정.
4. **공지 섹션 빔** → `div.ubboard_view` 구조 비교. `div.subject h3`, `div.info div.writer`, `div.content div.text_to_html` 셀렉터 조정.

셀렉터 수정 후 해당 fixture도 실제 구조로 업데이트하고 단위 테스트 재실행.

- [ ] **Step 4: Re-run and verify**

Run: `learnus --summary && cat reports/$(date +%Y%m%d).md`
Expected: 모든 섹션이 의미 있는 데이터로 채워짐

- [ ] **Step 5: Commit any selector fixes**

```bash
git add src/learnus/parsers/ tests/fixtures/
git commit -m "fix: align parsers with real LearnUs HTML after smoke test"
```

(변경 없으면 생략)

---

## Done Criteria

- `pytest -v` 전체 통과 (모든 기존·신규 테스트)
- `learnus --summary` 실행 시:
  1. 터미널에 4개 섹션 출력
  2. `reports/YYYYMMDD.md`에 동일 내용 저장
  3. `[INFO] 저장됨: <절대경로>` 메시지
- 동일 일자 재실행 시 `reports/YYYYMMDD.md`가 overwrite
- 기존 플래그(`learnus`, `--upcoming`, `--course`, `--json`) 동작 유지
- 부분 실패(공지 게시판 장애 등) 발생해도 나머지 섹션은 정상 출력
