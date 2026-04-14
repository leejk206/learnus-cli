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
