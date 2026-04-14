from datetime import datetime

from bs4 import BeautifulSoup

from learnus.models import Assignment


def parse_assignments(course_html: str, session) -> list[Assignment]:
    soup = BeautifulSoup(course_html, "lxml")
    results: list[Assignment] = []
    seen_urls: set[str] = set()
    for li in soup.select("li.activity.assign"):
        link = li.select_one("div.activityinstance a")
        if not link:
            continue
        url = (link.get("href") or "").strip()
        if not url or url in seen_urls:
            continue
        seen_urls.add(url)
        name_span = link.select_one("span.instancename")
        if not name_span:
            continue
        accesshide = name_span.select_one("span.accesshide")
        if accesshide:
            accesshide.extract()
        title = name_span.get_text(strip=True)

        submitted_from_course = _submitted_from_course_li(li)
        due_at, submitted_from_detail = _fetch_detail(session, url)
        submitted = (
            submitted_from_course
            if submitted_from_course is not None
            else submitted_from_detail
        )
        results.append(
            Assignment(title=title, due_at=due_at, submitted=submitted, url=url)
        )
    return results


def _submitted_from_course_li(li) -> bool | None:
    img = li.select_one("span.autocompletion img")
    if not img:
        return None
    alt = (img.get("alt", "") or img.get("title", "")).strip()
    if alt.startswith("완료함") or alt.startswith("Completed"):
        return True
    if alt.startswith("완료하지") or alt.startswith("Not completed"):
        return False
    return None


def _fetch_detail(session, url: str) -> tuple[datetime | None, bool]:
    try:
        resp = session.get(url, timeout=15)
    except Exception:
        return None, False
    soup = BeautifulSoup(resp.text, "lxml")
    due_at: datetime | None = None
    submitted = False
    for row in soup.select("table.generaltable tr"):
        cells = row.find_all(["th", "td"])
        if len(cells) < 2:
            continue
        label = cells[0].get_text(strip=True)
        value = cells[1].get_text(strip=True)
        is_due_label = (
            "종료" in label
            or ("마감" in label and "마감까지" not in label)
            or "Due date" in label
        )
        is_submit_label = "제출 여부" in label or "Submission status" in label
        if is_due_label:
            parsed = _parse_datetime(value)
            if parsed:
                due_at = parsed
        elif is_submit_label:
            submitted = _is_submitted_value(value)
    return due_at, submitted


def _is_submitted_value(value: str) -> bool:
    v = value.strip()
    if "완료" in v:
        return True
    if "Submitted for" in v:
        return True
    if v.startswith("Submitted") and not v.startswith("Submitted:"):
        return True
    return False


def _parse_datetime(text: str) -> datetime | None:
    text = text.strip()
    for fmt in ("%Y-%m-%d %H:%M", "%Y-%m-%d %H:%M:%S", "%Y/%m/%d %H:%M", "%Y.%m.%d %H:%M"):
        try:
            return datetime.strptime(text, fmt)
        except ValueError:
            continue
    return None
