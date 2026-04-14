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
    text = header.get_text(strip=True)
    m = re.search(r"(\d+)\s*주차", text)
    if m:
        return int(m.group(1))
    m = re.search(r"Week\s*(\d+)", text, re.IGNORECASE)
    if m:
        return int(m.group(1))
    return None


def _watched_from_li(li) -> bool:
    img = li.select_one("span.autocompletion img")
    if not img:
        return False
    alt = (img.get("alt", "") or img.get("title", "")).strip()
    return alt.startswith("완료함") or alt.startswith("Completed")
