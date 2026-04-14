from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock

from learnus.parsers.assignment import parse_assignments

FIX = Path(__file__).parent / "fixtures"


def test_parse_assignments_from_course_page():
    html = (FIX / "course_page.html").read_text(encoding="utf-8")
    detail_html = (FIX / "assignment_detail.html").read_text(encoding="utf-8")

    session = MagicMock()
    session.get.return_value.text = detail_html

    assignments = parse_assignments(html, session)

    assert len(assignments) == 2
    titles = [a.title for a in assignments]
    assert "HW1: 배열 구현" in titles
    assert "HW2: 연결리스트" in titles
    assert assignments[0].url == "https://ys.learnus.org/mod/assign/view.php?id=11111"
    assert assignments[0].due_at == datetime(2026, 4, 20, 23, 59)
    assert assignments[0].submitted is True


def test_parse_assignments_empty_when_none():
    session = MagicMock()
    result = parse_assignments("<html><body><ul class='topics'></ul></body></html>", session)
    assert result == []
