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
