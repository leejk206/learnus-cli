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
