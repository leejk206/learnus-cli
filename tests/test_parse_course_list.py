from pathlib import Path
from learnus.parsers.course_list import parse_course_list

FIXTURE = Path(__file__).parent / "fixtures" / "dashboard.html"


def test_parse_course_list_returns_courses():
    html = FIXTURE.read_text(encoding="utf-8")
    courses = parse_course_list(html)
    assert len(courses) == 2
    assert courses[0].id == "12345"
    assert courses[0].name == "자료구조 (001)"
    assert courses[0].url == "https://ys.learnus.org/course/view.php?id=12345"
    assert courses[1].id == "67890"
    assert courses[1].name == "운영체제 (002)"


def test_parse_course_list_empty_when_no_courses():
    courses = parse_course_list("<html><body></body></html>")
    assert courses == []
