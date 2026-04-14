from datetime import datetime
from learnus.models import Course, Assignment, Notice, Material, Quiz


def test_assignment_defaults():
    a = Assignment(title="HW1", due_at=None, submitted=False, url="http://x")
    assert a.title == "HW1"
    assert a.submitted is False


def test_course_empty_lists():
    c = Course(id="1", name="자료구조", url="http://x",
               assignments=[], notices=[], materials=[], quizzes=[])
    assert c.assignments == []


def test_material_kind_values():
    m = Material(title="강의1", week=1, posted_at=None, kind="video", url="http://x")
    assert m.kind == "video"


def test_quiz_fields():
    q = Quiz(title="퀴즈1", opens_at=datetime(2026, 4, 14),
             closes_at=datetime(2026, 4, 15), url="http://x")
    assert q.opens_at.day == 14
