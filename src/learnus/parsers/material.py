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
