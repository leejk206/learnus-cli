import json
from datetime import datetime

from learnus.models import Assignment, Course, Notice
from learnus.render import render_courses, render_upcoming, render_json


def _sample_courses():
    c1 = Course(
        id="1", name="자료구조", url="http://x",
        assignments=[
            Assignment(title="HW3", due_at=datetime(2026, 4, 20, 23, 59), submitted=False, url="http://x/1"),
            Assignment(title="HW2", due_at=datetime(2026, 4, 10, 23, 59), submitted=True, url="http://x/2"),
        ],
        notices=[Notice(title="중간고사 범위", posted_at=datetime(2026, 4, 10), url="http://x/3")],
    )
    c2 = Course(
        id="2", name="운영체제", url="http://y",
        assignments=[
            Assignment(title="Lab2", due_at=datetime(2026, 4, 23, 23, 59), submitted=False, url="http://y/1"),
        ],
    )
    return [c1, c2]


def test_render_courses_contains_course_names(capsys):
    render_courses(_sample_courses())
    out = capsys.readouterr().out
    assert "자료구조" in out
    assert "운영체제" in out
    assert "HW3" in out
    assert "중간고사 범위" in out


def test_render_upcoming_sorts_by_due_date(capsys):
    render_upcoming(_sample_courses(), now=datetime(2026, 4, 14))
    out = capsys.readouterr().out
    hw3_idx = out.index("HW3")
    lab2_idx = out.index("Lab2")
    assert hw3_idx < lab2_idx


def test_render_upcoming_excludes_submitted(capsys):
    render_upcoming(_sample_courses(), now=datetime(2026, 4, 14))
    out = capsys.readouterr().out
    assert "HW2" not in out


def test_render_json_produces_valid_json(capsys):
    render_json(_sample_courses())
    out = capsys.readouterr().out
    data = json.loads(out)
    assert len(data) == 2
    assert data[0]["name"] == "자료구조"
    assert data[0]["assignments"][0]["title"] == "HW3"
    assert data[0]["assignments"][0]["due_at"] == "2026-04-20T23:59:00"
