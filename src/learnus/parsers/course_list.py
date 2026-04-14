from urllib.parse import parse_qs, urlparse

from bs4 import BeautifulSoup

from learnus.models import Course


def parse_course_list(html: str) -> list[Course]:
    soup = BeautifulSoup(html, "lxml")
    courses: list[Course] = []
    seen: set[str] = set()
    for link in soup.select("a.course-link"):
        href = (link.get("href") or "").strip()
        if "/course/view.php" not in href:
            continue
        qs = parse_qs(urlparse(href).query)
        course_id = (qs.get("id") or [""])[0]
        if not course_id or course_id in seen:
            continue
        title_tag = link.select_one("div.course-title h3")
        name = title_tag.get_text(strip=True) if title_tag else ""
        if not name:
            continue
        seen.add(course_id)
        courses.append(Course(id=course_id, name=name, url=href))
    return courses
