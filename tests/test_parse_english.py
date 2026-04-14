from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock

from learnus.parsers.assignment import parse_assignments
from learnus.parsers.video import parse_videos

FIX = Path(__file__).parent / "fixtures"


def test_video_parses_english_section_header_and_completed():
    html = (FIX / "course_page_en.html").read_text(encoding="utf-8")
    videos = parse_videos(html)
    assert len(videos) == 1
    v = videos[0]
    assert v.week == 3                              # from "Week 3 [17 March - 23 March]"
    assert v.title == "03-Access-Control"           # accesshide stripped
    assert v.watched is True                        # "Completed: ..."
    assert v.starts_at == datetime(2026, 3, 17)
    assert v.length == "46:51"


def test_assignment_parses_english_detail_table():
    html = (FIX / "course_page_en.html").read_text(encoding="utf-8")
    detail = (FIX / "assignment_detail_en.html").read_text(encoding="utf-8")
    session = MagicMock()
    session.get.return_value.text = detail

    assigns = parse_assignments(html, session)
    assert len(assigns) == 1
    a = assigns[0]
    assert a.title == "Homework #1"
    # Course page says "Not completed" → False, but detail says "Submitted for grading" → True.
    # submitted_from_course takes priority.
    assert a.submitted is False
    assert a.due_at == datetime(2026, 3, 17, 14, 59)


def test_assignment_english_submitted_from_detail_when_course_unknown():
    # A case where course-page completion img is absent → falls back to detail
    course_html = """<html><body><ul class='topics'><li class='section'>
      <h3 class='sectionname'>Week 1</h3>
      <ul><li class='activity assign modtype_assign'>
        <div class='activityinstance'><a href='http://x/a'>
          <span class='instancename'>HW1</span></a></div>
      </li></ul></li></ul></body></html>"""
    detail = (FIX / "assignment_detail_en.html").read_text(encoding="utf-8")
    session = MagicMock()
    session.get.return_value.text = detail
    assigns = parse_assignments(course_html, session)
    assert assigns[0].submitted is True
    assert assigns[0].due_at == datetime(2026, 3, 17, 14, 59)
