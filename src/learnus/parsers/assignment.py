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
