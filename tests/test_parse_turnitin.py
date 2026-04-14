from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock

from learnus.parsers.turnitin import parse_turnitin_assignments

FIX = Path(__file__).parent / "fixtures"


def test_parse_turnitin_returns_two_assignments_with_due_dates():
    course_html = (FIX / "turnitin_course_page.html").read_text(encoding="utf-8")
    unsubmitted = (FIX / "turnitin_detail_unsubmitted.html").read_text(encoding="utf-8")
    submitted = (FIX / "turnitin_detail_submitted.html").read_text(encoding="utf-8")

    session = MagicMock()

    def fake_get(url, *args, **kwargs):
        resp = MagicMock()
        if url.endswith("?id=aa"):
            resp.text = unsubmitted
        elif url.endswith("?id=bb"):
            resp.text = submitted
        else:
            resp.text = "<html></html>"
        return resp

    session.get.side_effect = fake_get

    assigns = parse_turnitin_assignments(course_html, session)
    assert len(assigns) == 2

    a1 = assigns[0]
    assert a1.title == "개인소과제 1: '행복의기원' 북리뷰"
    assert a1.due_at == datetime(2026, 4, 17, 23, 59)
    assert a1.submitted is False
    assert a1.url == "https://ys.learnus.org/mod/turnitintooltwo/view.php?id=aa"

    a2 = assigns[1]
    assert a2.title == "개인소과제 2: '아주보통의행복' 북리뷰"
    assert a2.due_at == datetime(2026, 5, 10, 23, 59)
    assert a2.submitted is True


def test_parse_turnitin_empty_when_none():
    session = MagicMock()
    assert parse_turnitin_assignments("<html></html>", session) == []


def test_parse_turnitin_network_error_keeps_title():
    course_html = (FIX / "turnitin_course_page.html").read_text(encoding="utf-8")
    session = MagicMock()
    session.get.side_effect = RuntimeError("down")
    assigns = parse_turnitin_assignments(course_html, session)
    assert len(assigns) == 2
    assert assigns[0].due_at is None
    assert assigns[0].submitted is False
