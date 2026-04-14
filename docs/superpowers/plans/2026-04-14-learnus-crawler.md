# LearnUs Crawler CLI Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 연세대 LearnUs(Moodle 기반 LMS) 수강 강좌의 과제·공지·자료·퀴즈를 수집해 터미널에 출력하는 수동 실행 Python CLI.

**Architecture:** 4-layer 분리 — `auth`(SSO 로그인 → 인증된 Session), `parsers/`(HTML → dataclass 순수 함수), `crawler`(Session + 파서 조립자), `render`/`cli`(출력 + 엔트리). 파서는 네트워크 의존 없이 fixture HTML로 단위 테스트.

**Tech Stack:** Python 3.11+, requests, beautifulsoup4, lxml, typer, rich, python-dotenv, pytest

---

## Important Note on Parser Fixtures

LearnUs는 Moodle 기반이며 표준 Moodle HTML 구조를 따른다. 이 플랜의 파서 태스크는 표준 Moodle DOM 구조에 기반한 **합성 fixture HTML**로 TDD를 수행한다. 실제 LearnUs HTML이 미세하게 다를 경우 **Task 12(스모크 테스트)** 에서 실제 HTML을 캡처해 fixture를 갱신하고 파서 셀렉터를 조정한다.

이 전략의 목적은 다음과 같다:
- 파서 코드를 먼저 TDD로 작성해두고, 실제 HTML 차이는 작은 셀렉터 수정만으로 흡수한다.
- 로그인 전엔 실제 HTML에 접근할 수 없는데, 로그인은 스모크 단계에서만 수행한다.

---

## File Structure

```
learnus-cli/
├── pyproject.toml
├── .env.example
├── .gitignore
├── src/learnus/
│   ├── __init__.py
│   ├── models.py            # 데이터클래스
│   ├── auth.py              # SSO 로그인 → Session
│   ├── crawler.py           # fetch_course_list, fetch_all
│   ├── render.py            # rich 출력, JSON 덤프
│   ├── cli.py               # typer 엔트리
│   └── parsers/
│       ├── __init__.py
│       ├── course_list.py
│       ├── assignment.py
│       ├── notice.py
│       ├── material.py
│       └── quiz.py
└── tests/
    ├── __init__.py
    ├── fixtures/
    │   ├── dashboard.html
    │   ├── course_page.html
    │   ├── assignment_detail.html
    │   └── notice_detail.html
    ├── test_models.py
    ├── test_parse_course_list.py
    ├── test_parse_assignment.py
    ├── test_parse_notice.py
    ├── test_parse_material.py
    ├── test_parse_quiz.py
    └── test_render.py
```

---

## Task 1: Project Scaffolding

**Files:**
- Create: `pyproject.toml`
- Create: `.env.example`
- Create: `.gitignore`
- Create: `src/learnus/__init__.py`
- Create: `src/learnus/parsers/__init__.py`
- Create: `tests/__init__.py`

- [ ] **Step 1: Create `pyproject.toml`**

```toml
[project]
name = "learnus-cli"
version = "0.1.0"
description = "LearnUs crawler CLI for Yonsei University"
requires-python = ">=3.11"
dependencies = [
    "requests>=2.31",
    "beautifulsoup4>=4.12",
    "lxml>=5.0",
    "typer>=0.12",
    "rich>=13.7",
    "python-dotenv>=1.0",
]

[project.optional-dependencies]
dev = ["pytest>=8.0"]

[project.scripts]
learnus = "learnus.cli:app"

[build-system]
requires = ["setuptools>=68"]
build-backend = "setuptools.build_meta"

[tool.setuptools.packages.find]
where = ["src"]
```

- [ ] **Step 2: Create `.env.example`**

```
YONSEI_ID=your_student_id
YONSEI_PW=your_password
```

- [ ] **Step 3: Create `.gitignore`**

```
.env
__pycache__/
*.pyc
.pytest_cache/
*.egg-info/
build/
dist/
.venv/
venv/
/tmp/
```

- [ ] **Step 4: Create empty package init files**

`src/learnus/__init__.py`:
```python
```

`src/learnus/parsers/__init__.py`:
```python
```

`tests/__init__.py`:
```python
```

- [ ] **Step 5: Install in editable mode**

Run: `pip install -e ".[dev]"`
Expected: Installation succeeds, `learnus` command is registered (though it won't work yet — module has no `app`).

- [ ] **Step 6: Commit**

```bash
git add pyproject.toml .env.example .gitignore src/ tests/
git commit -m "chore: scaffold learnus-cli project"
```

---

## Task 2: Data Models

**Files:**
- Create: `src/learnus/models.py`
- Test: `tests/test_models.py`

- [ ] **Step 1: Write failing test**

`tests/test_models.py`:
```python
from datetime import datetime
from learnus.models import Course, Assignment, Notice, Material, Quiz


def test_assignment_defaults():
    a = Assignment(title="HW1", due_at=None, submitted=False, url="http://x")
    assert a.title == "HW1"
    assert a.submitted is False


def test_course_empty_lists():
    c = Course(id="1", name="자료구조", url="http://x",
               assignments=[], notices=[], materials=[], quizzes=[])
    assert c.assignments == []


def test_material_kind_values():
    m = Material(title="강의1", week=1, posted_at=None, kind="video", url="http://x")
    assert m.kind == "video"


def test_quiz_fields():
    q = Quiz(title="퀴즈1", opens_at=datetime(2026, 4, 14),
             closes_at=datetime(2026, 4, 15), url="http://x")
    assert q.opens_at.day == 14
```

- [ ] **Step 2: Run test to confirm it fails**

Run: `pytest tests/test_models.py -v`
Expected: FAIL with `ImportError: cannot import name 'Course' from 'learnus.models'`

- [ ] **Step 3: Implement `models.py`**

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
class Notice:
    title: str
    posted_at: datetime | None
    url: str


@dataclass
class Material:
    title: str
    week: int | None
    posted_at: datetime | None
    kind: str  # "video" | "file" | "link"
    url: str


@dataclass
class Quiz:
    title: str
    opens_at: datetime | None
    closes_at: datetime | None
    url: str


@dataclass
class Course:
    id: str
    name: str
    url: str
    assignments: list[Assignment] = field(default_factory=list)
    notices: list[Notice] = field(default_factory=list)
    materials: list[Material] = field(default_factory=list)
    quizzes: list[Quiz] = field(default_factory=list)
```

- [ ] **Step 4: Run tests to confirm they pass**

Run: `pytest tests/test_models.py -v`
Expected: 4 passed

- [ ] **Step 5: Commit**

```bash
git add src/learnus/models.py tests/test_models.py
git commit -m "feat: add data models for courses and items"
```

---

## Task 3: Course List Parser

**Files:**
- Create: `tests/fixtures/dashboard.html`
- Create: `src/learnus/parsers/course_list.py`
- Test: `tests/test_parse_course_list.py`

- [ ] **Step 1: Create synthetic fixture based on standard Moodle dashboard markup**

`tests/fixtures/dashboard.html`:
```html
<!DOCTYPE html>
<html>
<body>
<div id="page-content">
  <div class="coursebox" data-courseid="12345">
    <div class="info">
      <h3 class="coursename">
        <a href="https://ys.learnus.org/course/view.php?id=12345">자료구조 (001)</a>
      </h3>
    </div>
  </div>
  <div class="coursebox" data-courseid="67890">
    <div class="info">
      <h3 class="coursename">
        <a href="https://ys.learnus.org/course/view.php?id=67890">운영체제 (002)</a>
      </h3>
    </div>
  </div>
</div>
<a href="/login/logout.php">로그아웃</a>
</body>
</html>
```

- [ ] **Step 2: Write failing test**

`tests/test_parse_course_list.py`:
```python
from pathlib import Path
from learnus.parsers.course_list import parse_course_list

FIXTURE = Path(__file__).parent / "fixtures" / "dashboard.html"


def test_parse_course_list_returns_courses():
    html = FIXTURE.read_text(encoding="utf-8")
    courses = parse_course_list(html)
    assert len(courses) == 2
    assert courses[0].id == "12345"
    assert courses[0].name == "자료구조 (001)"
    assert courses[0].url == "https://ys.learnus.org/course/view.php?id=12345"
    assert courses[1].id == "67890"
    assert courses[1].name == "운영체제 (002)"


def test_parse_course_list_empty_when_no_courses():
    courses = parse_course_list("<html><body></body></html>")
    assert courses == []
```

- [ ] **Step 3: Run test to confirm it fails**

Run: `pytest tests/test_parse_course_list.py -v`
Expected: FAIL with ImportError

- [ ] **Step 4: Implement parser**

`src/learnus/parsers/course_list.py`:
```python
from bs4 import BeautifulSoup

from learnus.models import Course


def parse_course_list(html: str) -> list[Course]:
    soup = BeautifulSoup(html, "lxml")
    courses: list[Course] = []
    for box in soup.select("div.coursebox"):
        course_id = box.get("data-courseid", "").strip()
        link = box.select_one("h3.coursename a")
        if not link or not course_id:
            continue
        name = link.get_text(strip=True)
        url = link.get("href", "").strip()
        courses.append(Course(id=course_id, name=name, url=url))
    return courses
```

- [ ] **Step 5: Run tests to confirm they pass**

Run: `pytest tests/test_parse_course_list.py -v`
Expected: 2 passed

- [ ] **Step 6: Commit**

```bash
git add tests/fixtures/dashboard.html tests/test_parse_course_list.py src/learnus/parsers/course_list.py
git commit -m "feat: add course list parser"
```

---

## Task 4: Assignment Parser

**Files:**
- Create: `tests/fixtures/course_page.html`
- Create: `tests/fixtures/assignment_detail.html`
- Create: `src/learnus/parsers/assignment.py`
- Test: `tests/test_parse_assignment.py`

- [ ] **Step 1: Create synthetic course page fixture (shared across parsers)**

`tests/fixtures/course_page.html`:
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
        </div>
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
      <li class="activity ubboard modtype_ubboard" id="module-55555">
        <div class="activityinstance">
          <a href="https://ys.learnus.org/mod/ubboard/view.php?id=55555">
            <span class="instancename">중간고사 범위 안내<span class="accesshide"> 공지</span></span>
          </a>
        </div>
      </li>
      <li class="activity quiz modtype_quiz" id="module-66666">
        <div class="activityinstance">
          <a href="https://ys.learnus.org/mod/quiz/view.php?id=66666">
            <span class="instancename">2주차 퀴즈<span class="accesshide"> 퀴즈</span></span>
          </a>
        </div>
      </li>
    </ul>
  </li>
</ul>
</body>
</html>
```

- [ ] **Step 2: Create assignment detail fixture**

`tests/fixtures/assignment_detail.html`:
```html
<!DOCTYPE html>
<html>
<body>
<div class="submissionstatustable">
  <table>
    <tr>
      <th>종료 일시</th>
      <td>2026-04-20 23:59</td>
    </tr>
    <tr>
      <th>제출 여부</th>
      <td>제출 완료</td>
    </tr>
  </table>
</div>
</body>
</html>
```

- [ ] **Step 3: Write failing test**

`tests/test_parse_assignment.py`:
```python
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock

from learnus.parsers.assignment import parse_assignments

FIX = Path(__file__).parent / "fixtures"


def test_parse_assignments_from_course_page():
    html = (FIX / "course_page.html").read_text(encoding="utf-8")
    detail_html = (FIX / "assignment_detail.html").read_text(encoding="utf-8")

    session = MagicMock()
    session.get.return_value.text = detail_html

    assignments = parse_assignments(html, session)

    assert len(assignments) == 2
    titles = [a.title for a in assignments]
    assert "HW1: 배열 구현" in titles
    assert "HW2: 연결리스트" in titles
    assert assignments[0].url == "https://ys.learnus.org/mod/assign/view.php?id=11111"
    assert assignments[0].due_at == datetime(2026, 4, 20, 23, 59)
    assert assignments[0].submitted is True


def test_parse_assignments_empty_when_none():
    session = MagicMock()
    result = parse_assignments("<html><body><ul class='topics'></ul></body></html>", session)
    assert result == []
```

- [ ] **Step 4: Run test to confirm it fails**

Run: `pytest tests/test_parse_assignment.py -v`
Expected: FAIL with ImportError

- [ ] **Step 5: Implement parser**

`src/learnus/parsers/assignment.py`:
```python
from datetime import datetime

from bs4 import BeautifulSoup

from learnus.models import Assignment


def parse_assignments(course_html: str, session) -> list[Assignment]:
    soup = BeautifulSoup(course_html, "lxml")
    results: list[Assignment] = []
    for li in soup.select("li.activity.assign"):
        link = li.select_one("div.activityinstance a")
        if not link:
            continue
        url = link.get("href", "").strip()
        name_span = link.select_one("span.instancename")
        if not name_span:
            continue
        accesshide = name_span.select_one("span.accesshide")
        if accesshide:
            accesshide.extract()
        title = name_span.get_text(strip=True)

        due_at, submitted = _fetch_detail(session, url)
        results.append(Assignment(title=title, due_at=due_at, submitted=submitted, url=url))
    return results


def _fetch_detail(session, url: str) -> tuple[datetime | None, bool]:
    resp = session.get(url)
    soup = BeautifulSoup(resp.text, "lxml")
    due_at: datetime | None = None
    submitted = False
    for row in soup.select("div.submissionstatustable table tr"):
        th = row.find("th")
        td = row.find("td")
        if not th or not td:
            continue
        label = th.get_text(strip=True)
        value = td.get_text(strip=True)
        if "종료" in label:
            due_at = _parse_datetime(value)
        elif "제출" in label:
            submitted = "완료" in value
    return due_at, submitted


def _parse_datetime(text: str) -> datetime | None:
    for fmt in ("%Y-%m-%d %H:%M", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(text, fmt)
        except ValueError:
            continue
    return None
```

- [ ] **Step 6: Run tests to confirm they pass**

Run: `pytest tests/test_parse_assignment.py -v`
Expected: 2 passed

- [ ] **Step 7: Commit**

```bash
git add tests/fixtures/course_page.html tests/fixtures/assignment_detail.html tests/test_parse_assignment.py src/learnus/parsers/assignment.py
git commit -m "feat: add assignment parser with detail fetch"
```

---

## Task 5: Notice Parser

**Files:**
- Create: `tests/fixtures/notice_detail.html`
- Create: `src/learnus/parsers/notice.py`
- Test: `tests/test_parse_notice.py`

- [ ] **Step 1: Create notice detail fixture**

`tests/fixtures/notice_detail.html`:
```html
<!DOCTYPE html>
<html>
<body>
<div class="ubboard-view">
  <table>
    <tr>
      <th>작성일</th>
      <td>2026-04-10 09:30</td>
    </tr>
  </table>
</div>
</body>
</html>
```

- [ ] **Step 2: Write failing test**

`tests/test_parse_notice.py`:
```python
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock

from learnus.parsers.notice import parse_notices

FIX = Path(__file__).parent / "fixtures"


def test_parse_notices_from_course_page():
    html = (FIX / "course_page.html").read_text(encoding="utf-8")
    detail_html = (FIX / "notice_detail.html").read_text(encoding="utf-8")

    session = MagicMock()
    session.get.return_value.text = detail_html

    notices = parse_notices(html, session)

    assert len(notices) == 1
    assert notices[0].title == "중간고사 범위 안내"
    assert notices[0].url == "https://ys.learnus.org/mod/ubboard/view.php?id=55555"
    assert notices[0].posted_at == datetime(2026, 4, 10, 9, 30)


def test_parse_notices_empty_when_none():
    session = MagicMock()
    assert parse_notices("<html></html>", session) == []
```

- [ ] **Step 3: Run test to confirm it fails**

Run: `pytest tests/test_parse_notice.py -v`
Expected: FAIL with ImportError

- [ ] **Step 4: Implement parser**

`src/learnus/parsers/notice.py`:
```python
from datetime import datetime

from bs4 import BeautifulSoup

from learnus.models import Notice


def parse_notices(course_html: str, session) -> list[Notice]:
    soup = BeautifulSoup(course_html, "lxml")
    results: list[Notice] = []
    for li in soup.select("li.activity.ubboard"):
        link = li.select_one("div.activityinstance a")
        if not link:
            continue
        url = link.get("href", "").strip()
        name_span = link.select_one("span.instancename")
        if not name_span:
            continue
        accesshide = name_span.select_one("span.accesshide")
        if accesshide:
            accesshide.extract()
        title = name_span.get_text(strip=True)

        posted_at = _fetch_posted_at(session, url)
        results.append(Notice(title=title, posted_at=posted_at, url=url))
    return results


def _fetch_posted_at(session, url: str) -> datetime | None:
    resp = session.get(url)
    soup = BeautifulSoup(resp.text, "lxml")
    for row in soup.select("div.ubboard-view table tr"):
        th = row.find("th")
        td = row.find("td")
        if not th or not td:
            continue
        if "작성일" in th.get_text(strip=True):
            return _parse_datetime(td.get_text(strip=True))
    return None


def _parse_datetime(text: str) -> datetime | None:
    for fmt in ("%Y-%m-%d %H:%M", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(text, fmt)
        except ValueError:
            continue
    return None
```

- [ ] **Step 5: Run tests to confirm they pass**

Run: `pytest tests/test_parse_notice.py -v`
Expected: 2 passed

- [ ] **Step 6: Commit**

```bash
git add tests/fixtures/notice_detail.html tests/test_parse_notice.py src/learnus/parsers/notice.py
git commit -m "feat: add notice parser with detail fetch"
```

---

## Task 6: Material Parser

**Files:**
- Create: `src/learnus/parsers/material.py`
- Test: `tests/test_parse_material.py`

- [ ] **Step 1: Write failing test**

`tests/test_parse_material.py`:
```python
from pathlib import Path

from learnus.parsers.material import parse_materials

FIX = Path(__file__).parent / "fixtures"


def test_parse_materials_separates_video_and_file():
    html = (FIX / "course_page.html").read_text(encoding="utf-8")
    materials = parse_materials(html)

    kinds = {m.kind for m in materials}
    assert kinds == {"video", "file"}

    video = next(m for m in materials if m.kind == "video")
    assert video.title == "1주차 강의 영상"
    assert video.week == 1

    file = next(m for m in materials if m.kind == "file")
    assert file.title == "1주차 강의노트.pdf"
    assert file.week == 1


def test_parse_materials_empty_when_none():
    assert parse_materials("<html></html>") == []
```

- [ ] **Step 2: Run test to confirm it fails**

Run: `pytest tests/test_parse_material.py -v`
Expected: FAIL with ImportError

- [ ] **Step 3: Implement parser**

`src/learnus/parsers/material.py`:
```python
import re

from bs4 import BeautifulSoup

from learnus.models import Material

_KIND_MAP = {
    "vod": "video",
    "ubfile": "file",
    "url": "link",
    "resource": "file",
}


def parse_materials(course_html: str) -> list[Material]:
    soup = BeautifulSoup(course_html, "lxml")
    results: list[Material] = []
    for section in soup.select("li.section"):
        week = _extract_week(section)
        for li in section.select("li.activity"):
            kind = _detect_kind(li)
            if kind is None:
                continue
            link = li.select_one("div.activityinstance a")
            if not link:
                continue
            name_span = link.select_one("span.instancename")
            if not name_span:
                continue
            accesshide = name_span.select_one("span.accesshide")
            if accesshide:
                accesshide.extract()
            title = name_span.get_text(strip=True)
            url = link.get("href", "").strip()
            results.append(Material(
                title=title,
                week=week,
                posted_at=None,
                kind=kind,
                url=url,
            ))
    return results


def _extract_week(section) -> int | None:
    header = section.select_one("h3.sectionname")
    if not header:
        return None
    text = header.get_text(strip=True)
    m = re.search(r"(\d+)\s*주차", text)
    return int(m.group(1)) if m else None


def _detect_kind(li) -> str | None:
    classes = li.get("class", [])
    for cls in classes:
        if cls in _KIND_MAP:
            return _KIND_MAP[cls]
    return None
```

- [ ] **Step 4: Run tests to confirm they pass**

Run: `pytest tests/test_parse_material.py -v`
Expected: 2 passed

- [ ] **Step 5: Commit**

```bash
git add tests/test_parse_material.py src/learnus/parsers/material.py
git commit -m "feat: add material parser for videos and files"
```

---

## Task 7: Quiz Parser

**Files:**
- Create: `src/learnus/parsers/quiz.py`
- Test: `tests/test_parse_quiz.py`

- [ ] **Step 1: Write failing test**

`tests/test_parse_quiz.py`:
```python
from pathlib import Path

from learnus.parsers.quiz import parse_quizzes

FIX = Path(__file__).parent / "fixtures"


def test_parse_quizzes_from_course_page():
    html = (FIX / "course_page.html").read_text(encoding="utf-8")
    quizzes = parse_quizzes(html)
    assert len(quizzes) == 1
    assert quizzes[0].title == "2주차 퀴즈"
    assert quizzes[0].url == "https://ys.learnus.org/mod/quiz/view.php?id=66666"


def test_parse_quizzes_empty_when_none():
    assert parse_quizzes("<html></html>") == []
```

- [ ] **Step 2: Run test to confirm it fails**

Run: `pytest tests/test_parse_quiz.py -v`
Expected: FAIL with ImportError

- [ ] **Step 3: Implement parser**

`src/learnus/parsers/quiz.py`:
```python
from bs4 import BeautifulSoup

from learnus.models import Quiz


def parse_quizzes(course_html: str) -> list[Quiz]:
    soup = BeautifulSoup(course_html, "lxml")
    results: list[Quiz] = []
    for li in soup.select("li.activity.quiz"):
        link = li.select_one("div.activityinstance a")
        if not link:
            continue
        url = link.get("href", "").strip()
        name_span = link.select_one("span.instancename")
        if not name_span:
            continue
        accesshide = name_span.select_one("span.accesshide")
        if accesshide:
            accesshide.extract()
        title = name_span.get_text(strip=True)
        results.append(Quiz(title=title, opens_at=None, closes_at=None, url=url))
    return results
```

Note: 퀴즈의 `opens_at`/`closes_at`은 상세 페이지에서 추출해야 하지만, 실제 HTML 구조를 스모크 단계에서 확인한 후 Task 12에서 보강한다. 지금은 기본값 `None`으로 둔다.

- [ ] **Step 4: Run tests to confirm they pass**

Run: `pytest tests/test_parse_quiz.py -v`
Expected: 2 passed

- [ ] **Step 5: Commit**

```bash
git add tests/test_parse_quiz.py src/learnus/parsers/quiz.py
git commit -m "feat: add quiz parser (dates populated later)"
```

---

## Task 8: Auth Module (SSO Login)

**Files:**
- Create: `src/learnus/auth.py`
- Test: `tests/test_auth.py`

이 태스크는 실제 네트워크가 필요하므로 자동화된 단위 테스트는 예외 타입 검증에 한정한다. 실제 로그인 동작은 Task 12 스모크 테스트에서 검증한다.

- [ ] **Step 1: Write failing test (exception type only)**

`tests/test_auth.py`:
```python
import pytest

from learnus.auth import LoginError, login


def test_login_error_is_exception():
    assert issubclass(LoginError, Exception)


def test_login_raises_on_empty_credentials():
    with pytest.raises(LoginError):
        login("", "")
```

- [ ] **Step 2: Run test to confirm it fails**

Run: `pytest tests/test_auth.py -v`
Expected: FAIL with ImportError

- [ ] **Step 3: Implement `auth.py`**

`src/learnus/auth.py`:
```python
import requests
from bs4 import BeautifulSoup

LEARNUS_BASE = "https://ys.learnus.org"
LOGIN_URL = f"{LEARNUS_BASE}/login.php"
SSO_LOGIN_URL = f"{LEARNUS_BASE}/passni/sso/coursemosLogin.php"


class LoginError(Exception):
    """로그인 실패. 메시지에 원인 포함:
    - '자격증명 오류'
    - '네트워크 오류'
    - '예상치 못한 응답'
    """


def login(user_id: str, password: str) -> requests.Session:
    if not user_id or not password:
        raise LoginError("자격증명 오류: ID/PW가 비어 있음")

    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (compatible; learnus-cli/0.1)",
    })

    try:
        session.get(LOGIN_URL, timeout=10)
        resp = session.post(
            SSO_LOGIN_URL,
            data={"username": user_id, "password": password},
            timeout=10,
            allow_redirects=True,
        )
    except requests.RequestException as e:
        raise LoginError(f"네트워크 오류: {e}") from e

    if resp.status_code != 200:
        raise LoginError(f"예상치 못한 응답: HTTP {resp.status_code}")

    try:
        dashboard = session.get(LEARNUS_BASE + "/", timeout=10)
    except requests.RequestException as e:
        raise LoginError(f"네트워크 오류: {e}") from e

    if not _is_logged_in(dashboard.text):
        raise LoginError("자격증명 오류: 로그인 후 대시보드 접근 실패")

    return session


def _is_logged_in(html: str) -> bool:
    soup = BeautifulSoup(html, "lxml")
    if soup.find("a", href=lambda h: h and "logout" in h):
        return True
    if "로그아웃" in html:
        return True
    return False
```

Note: 연세포털 SSO 로그인 엔드포인트와 payload 필드 이름(`username`, `password`)은 실제 HTML 폼에 맞춰 Task 12에서 조정될 수 있다. LearnUs는 `passni/sso/coursemosLogin.php`를 사용하는 것으로 알려져 있다.

- [ ] **Step 4: Run tests to confirm they pass**

Run: `pytest tests/test_auth.py -v`
Expected: 2 passed

- [ ] **Step 5: Commit**

```bash
git add src/learnus/auth.py tests/test_auth.py
git commit -m "feat: add auth module with SSO login flow"
```

---

## Task 9: Crawler Orchestration

**Files:**
- Create: `src/learnus/crawler.py`
- Test: `tests/test_crawler.py`

- [ ] **Step 1: Write failing test**

`tests/test_crawler.py`:
```python
from pathlib import Path
from unittest.mock import MagicMock

from learnus.crawler import fetch_all

FIX = Path(__file__).parent / "fixtures"


def test_fetch_all_populates_courses_with_items():
    dashboard = (FIX / "dashboard.html").read_text(encoding="utf-8")
    course_page = (FIX / "course_page.html").read_text(encoding="utf-8")
    assignment_detail = (FIX / "assignment_detail.html").read_text(encoding="utf-8")
    notice_detail = (FIX / "notice_detail.html").read_text(encoding="utf-8")

    session = MagicMock()

    def fake_get(url, *args, **kwargs):
        resp = MagicMock()
        if "/" == url or url.endswith("ys.learnus.org/") or url.endswith("ys.learnus.org"):
            resp.text = dashboard
        elif "/course/view.php" in url:
            resp.text = course_page
        elif "/mod/assign/view.php" in url:
            resp.text = assignment_detail
        elif "/mod/ubboard/view.php" in url:
            resp.text = notice_detail
        else:
            resp.text = "<html></html>"
        return resp

    session.get.side_effect = fake_get

    courses = fetch_all(session)

    assert len(courses) == 2
    first = courses[0]
    assert first.name == "자료구조 (001)"
    assert len(first.assignments) == 2
    assert len(first.notices) == 1
    assert len(first.materials) == 2
    assert len(first.quizzes) == 1


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

- [ ] **Step 2: Run test to confirm it fails**

Run: `pytest tests/test_crawler.py -v`
Expected: FAIL with ImportError

- [ ] **Step 3: Implement crawler**

`src/learnus/crawler.py`:
```python
import logging
import sys
import time

import requests

from learnus.auth import LEARNUS_BASE
from learnus.models import Course
from learnus.parsers.assignment import parse_assignments
from learnus.parsers.course_list import parse_course_list
from learnus.parsers.material import parse_materials
from learnus.parsers.notice import parse_notices
from learnus.parsers.quiz import parse_quizzes

log = logging.getLogger("learnus")

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
        course.notices = _safe(parse_notices, course.name, "공지", html, session)
        course.materials = _safe_noarg(parse_materials, course.name, "자료", html)
        course.quizzes = _safe_noarg(parse_quizzes, course.name, "퀴즈", html)

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

- [ ] **Step 4: Run tests to confirm they pass**

Run: `pytest tests/test_crawler.py -v`
Expected: 2 passed

- [ ] **Step 5: Run all tests**

Run: `pytest -v`
Expected: all tests pass

- [ ] **Step 6: Commit**

```bash
git add src/learnus/crawler.py tests/test_crawler.py
git commit -m "feat: add crawler orchestration with partial-failure handling"
```

---

## Task 10: Render Module

**Files:**
- Create: `src/learnus/render.py`
- Test: `tests/test_render.py`

- [ ] **Step 1: Write failing test**

`tests/test_render.py`:
```python
import json
from datetime import datetime

from learnus.models import Assignment, Course, Notice
from learnus.render import render_courses, render_upcoming, render_json


def _sample_courses():
    c1 = Course(
        id="1", name="자료구조", url="http://x",
        assignments=[
            Assignment(title="HW3", due_at=datetime(2026, 4, 20, 23, 59), submitted=False, url="http://x/1"),
            Assignment(title="HW2", due_at=datetime(2026, 4, 10, 23, 59), submitted=True, url="http://x/2"),
        ],
        notices=[Notice(title="중간고사 범위", posted_at=datetime(2026, 4, 10), url="http://x/3")],
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
    assert hw3_idx < lab2_idx  # HW3 (04-20) before Lab2 (04-23)


def test_render_upcoming_excludes_submitted(capsys):
    render_upcoming(_sample_courses(), now=datetime(2026, 4, 14))
    out = capsys.readouterr().out
    assert "HW2" not in out  # submitted


def test_render_json_produces_valid_json(capsys):
    render_json(_sample_courses())
    out = capsys.readouterr().out
    data = json.loads(out)
    assert len(data) == 2
    assert data[0]["name"] == "자료구조"
    assert data[0]["assignments"][0]["title"] == "HW3"
    assert data[0]["assignments"][0]["due_at"] == "2026-04-20T23:59:00"
```

- [ ] **Step 2: Run test to confirm it fails**

Run: `pytest tests/test_render.py -v`
Expected: FAIL with ImportError

- [ ] **Step 3: Implement render module**

`src/learnus/render.py`:
```python
import json
from dataclasses import asdict
from datetime import datetime
from typing import Iterable

from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from learnus.models import Course

_console = Console()


def render_courses(courses: Iterable[Course]) -> None:
    for course in courses:
        body = Text()
        _append_assignments(body, course)
        _append_notices(body, course)
        _append_materials(body, course)
        _append_quizzes(body, course)
        _console.print(Panel(body, title=course.name, title_align="left"))


def _append_assignments(body: Text, course: Course) -> None:
    body.append("과제\n", style="bold")
    if not course.assignments:
        body.append("  (없음)\n", style="dim")
        return
    now = datetime.now()
    for a in course.assignments:
        mark = "[✓]" if a.submitted else "[ ]"
        due = _format_due(a.due_at, now) if a.due_at else "마감 없음"
        line = f"  {mark} {a.title}    {due}\n"
        body.append(line, style="dim" if a.submitted else None)


def _append_notices(body: Text, course: Course) -> None:
    body.append("공지\n", style="bold")
    if not course.notices:
        body.append("  (없음)\n", style="dim")
        return
    for n in course.notices:
        date = n.posted_at.strftime("%Y-%m-%d") if n.posted_at else "날짜없음"
        body.append(f"  • {n.title}    {date}\n")


def _append_materials(body: Text, course: Course) -> None:
    body.append("자료\n", style="bold")
    if not course.materials:
        body.append("  (없음)\n", style="dim")
        return
    for m in course.materials:
        date = m.posted_at.strftime("%Y-%m-%d") if m.posted_at else ""
        body.append(f"  • [{m.kind}] {m.title}    {date}\n")


def _append_quizzes(body: Text, course: Course) -> None:
    body.append("퀴즈\n", style="bold")
    if not course.quizzes:
        body.append("  (없음)\n", style="dim")
        return
    for q in course.quizzes:
        close = q.closes_at.strftime("%Y-%m-%d %H:%M") if q.closes_at else "마감 미정"
        body.append(f"  • {q.title}    마감 {close}\n")


def _format_due(due: datetime, now: datetime) -> str:
    delta_days = (due.date() - now.date()).days
    if delta_days > 0:
        ddays = f"D-{delta_days}"
    elif delta_days == 0:
        ddays = "D-day"
    else:
        ddays = f"D+{-delta_days}"
    return f"마감 {due.strftime('%Y-%m-%d %H:%M')}  ({ddays})"


def render_upcoming(courses: Iterable[Course], now: datetime | None = None) -> None:
    now = now or datetime.now()
    rows: list[tuple[datetime, str, str, str]] = []
    for course in courses:
        for a in course.assignments:
            if a.submitted or a.due_at is None or a.due_at < now:
                continue
            rows.append((a.due_at, "과제", course.name, a.title))
        for q in course.quizzes:
            if q.closes_at is None or q.closes_at < now:
                continue
            rows.append((q.closes_at, "퀴즈", course.name, q.title))
    rows.sort(key=lambda r: r[0])
    for due, kind, course_name, title in rows:
        delta = (due.date() - now.date()).days
        ddays = f"D-{delta}" if delta > 0 else ("D-day" if delta == 0 else f"D+{-delta}")
        _console.print(f"{ddays}  [{kind}]  {course_name}  | {title}    마감 {due.strftime('%Y-%m-%d %H:%M')}")


def render_json(courses: Iterable[Course]) -> None:
    payload = [asdict(c) for c in courses]
    _console.print(json.dumps(payload, default=_json_default, ensure_ascii=False, indent=2))


def _json_default(obj):
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(f"not serializable: {type(obj)}")
```

- [ ] **Step 4: Run tests to confirm they pass**

Run: `pytest tests/test_render.py -v`
Expected: 4 passed

- [ ] **Step 5: Commit**

```bash
git add src/learnus/render.py tests/test_render.py
git commit -m "feat: add render module with default, upcoming, and json views"
```

---

## Task 11: CLI Entry Point

**Files:**
- Create: `src/learnus/cli.py`
- Test: `tests/test_cli.py`

- [ ] **Step 1: Write failing test**

`tests/test_cli.py`:
```python
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
    assert '"자료구조"' in result.stdout


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
```

- [ ] **Step 2: Run test to confirm it fails**

Run: `pytest tests/test_cli.py -v`
Expected: FAIL with ImportError

- [ ] **Step 3: Implement CLI**

`src/learnus/cli.py`:
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
from learnus.render import render_courses, render_json, render_upcoming

app = typer.Typer(add_completion=False, help="LearnUs crawler CLI")


@app.command()
def main(
    upcoming: bool = typer.Option(False, "--upcoming", help="마감 예정 과제/퀴즈만 flat 출력"),
    course: str = typer.Option("", "--course", help="강좌명 부분일치 필터"),
    json_output: bool = typer.Option(False, "--json", help="JSON 덤프"),
    debug: bool = typer.Option(False, "--debug", help="에러 시 traceback + HTML 덤프"),
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
            _dump_debug_html("crawl_failure", "<no-html>")
        raise typer.Exit(code=1)

    if course:
        courses = [c for c in courses if course in c.name]

    if json_output:
        render_json(courses)
    elif upcoming:
        render_upcoming(courses)
    else:
        render_courses(courses)


def _dump_debug_html(tag: str, html: str) -> None:
    path = Path(f"/tmp/learnus-debug-{tag}-{datetime.now().strftime('%Y%m%d-%H%M%S')}.html")
    path.write_text(html, encoding="utf-8")
    typer.echo(f"[DEBUG] HTML dumped to {path}", err=True)


if __name__ == "__main__":
    app()
```

- [ ] **Step 4: Run tests to confirm they pass**

Run: `pytest tests/test_cli.py -v`
Expected: 4 passed

- [ ] **Step 5: Run full test suite**

Run: `pytest -v`
Expected: all tests pass

- [ ] **Step 6: Commit**

```bash
git add src/learnus/cli.py tests/test_cli.py
git commit -m "feat: add typer CLI entrypoint with flags"
```

---

## Task 12: Smoke Test & Fixture Refinement

이 태스크는 실제 LearnUs 계정으로 동작을 검증하고, 필요 시 fixture와 셀렉터를 실제 HTML에 맞게 갱신한다.

**Files:**
- Create: `.env` (로컬에만 존재, gitignore됨)
- Potentially modify: `tests/fixtures/*.html`, `src/learnus/parsers/*.py`, `src/learnus/auth.py`

- [ ] **Step 1: Create local `.env`**

사용자에게 실제 YONSEI_ID / YONSEI_PW를 `.env`에 입력하도록 안내한다.

```
YONSEI_ID=<your_id>
YONSEI_PW=<your_pw>
```

- [ ] **Step 2: Run `learnus --debug` end-to-end**

Run: `learnus --debug`

예상 결과는 둘 중 하나:
- **성공**: 강좌별 과제/공지/자료/퀴즈가 표시된다 → Step 6으로 진행
- **실패**: 로그인 실패 또는 파싱 결과가 비어 있다 → Step 3으로 진행

- [ ] **Step 3: 실패 원인 분류**

1. **로그인 실패** → `auth.py`의 `SSO_LOGIN_URL`, payload 필드명, `_is_logged_in()` 판정 로직을 실제 폼에 맞춰 수정.
   - 브라우저 개발자도구로 로그인 요청을 확인: URL, 메서드, form field 이름.
2. **강좌 목록이 빔** → `/tmp/learnus-debug-*.html` 또는 수동으로 `curl` 대신 세션을 파이썬 REPL에서 `session.get("https://ys.learnus.org/").text`로 캡처.
   캡처한 HTML을 `tests/fixtures/dashboard.html`로 복사(학번·이름 redact) 후 `parse_course_list`의 CSS 셀렉터(`div.coursebox`, `h3.coursename`)를 실제 구조에 맞춰 조정.
3. **강좌 페이지 파싱 실패** → 동일하게 `session.get(course.url).text` 캡처 → `tests/fixtures/course_page.html` 갱신 → 해당 파서 수정.
4. **과제/공지 상세 페이지 필드가 다름** → `assignment_detail.html`, `notice_detail.html` 갱신 → `_fetch_detail`/`_fetch_posted_at`의 셀렉터 수정.

- [ ] **Step 4: Redact sensitive info from captured HTML**

캡처한 HTML에서 학번, 이름, 이메일 등 개인정보를 placeholder로 치환한 후 fixture로 저장.

- [ ] **Step 5: Re-run parser tests with updated fixtures**

Run: `pytest -v`
Expected: 변경된 fixture/파서에 대해 테스트가 여전히 통과. 필요 시 테스트의 기대값(`assert`)도 실제 구조에 맞게 업데이트.

- [ ] **Step 6: Verify end-to-end output**

Run:
```
learnus
learnus --upcoming
learnus --json | head -30
learnus --course "자료구조"
```

Expected: 각 명령이 에러 없이 기대한 출력을 낸다.

- [ ] **Step 7: Commit any fixture/selector refinements**

```bash
git add tests/fixtures/ src/learnus/
git commit -m "fix: align parsers with real LearnUs HTML from smoke test"
```

(실제로 수정이 없었다면 이 커밋은 생략.)

---

## Done Criteria

- 모든 unit test 통과 (`pytest -v`)
- `learnus` 명령이 실제 LearnUs 계정으로 동작하여 강좌/과제/공지/자료/퀴즈를 출력
- `learnus --upcoming`이 마감일 순으로 정렬된 flat 리스트를 출력
- `learnus --json`이 유효한 JSON을 출력
- `learnus --course "..."` 필터가 동작
- 특정 파서 실패 시 `[WARN]`만 출력되고 나머지 영역은 정상 표시 (부분 실패 허용)
- `.env`와 자격증명은 git에 포함되지 않음
