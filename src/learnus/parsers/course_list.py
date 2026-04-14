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
