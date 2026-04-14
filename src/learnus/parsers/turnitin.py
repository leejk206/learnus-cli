import re
from datetime import datetime

from bs4 import BeautifulSoup

from learnus.models import Assignment

_DATE_RE = re.compile(
    r"(\d{4})[-\s]*(\d{1,2})\s*월[-\s]*(\d{1,2})\s+(\d{1,2}):(\d{1,2})"
)


def parse_turnitin_assignments(course_html: str, session) -> list[Assignment]:
    soup = BeautifulSoup(course_html, "lxml")
    results: list[Assignment] = []
    seen: set[str] = set()
    for li in soup.select("li.activity.turnitintooltwo"):
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

        due_at, submitted = _fetch_detail(session, url)
        results.append(Assignment(title=title, due_at=due_at, submitted=submitted, url=url))
    return results


def _fetch_detail(session, url: str) -> tuple[datetime | None, bool]:
    try:
        resp = session.get(url, timeout=15)
    except Exception:
        return None, False
    soup = BeautifulSoup(resp.text, "lxml")
    return _extract_due(soup), _extract_submitted(soup)


def _extract_due(soup) -> datetime | None:
    table = soup.find("table", class_="partDetails")
    if not table:
        return None
    rows = table.find_all("tr")
    if len(rows) < 2:
        return None
    header_cells = rows[0].find_all(["th", "td"])
    headers = [c.get_text(strip=True) for c in header_cells]
    try:
        idx = next(i for i, h in enumerate(headers) if "마감" in h)
    except StopIteration:
        return None
    data_cells = rows[1].find_all(["th", "td"])
    if idx >= len(data_cells):
        return None
    return _parse_date(data_cells[idx].get_text(strip=True))


def _extract_submitted(soup) -> bool:
    table = soup.find("table", class_="submissionsDataTable")
    if not table:
        return False
    rows = table.find_all("tr")
    if len(rows) < 2:
        return False
    header_cells = rows[0].find_all(["th", "td"])
    headers = [c.get_text(strip=True) for c in header_cells]
    try:
        idx = next(i for i, h in enumerate(headers) if "제출" in h and "일" in h)
    except StopIteration:
        return False
    for row in rows[1:]:
        cells = row.find_all(["th", "td"])
        if idx >= len(cells):
            continue
        value = cells[idx].get_text(strip=True)
        if value and value != "--":
            return True
    return False


def _parse_date(text: str) -> datetime | None:
    m = _DATE_RE.search(text)
    if not m:
        return None
    y, mo, d, h, mi = m.groups()
    try:
        return datetime(int(y), int(mo), int(d), int(h), int(mi))
    except ValueError:
        return None
