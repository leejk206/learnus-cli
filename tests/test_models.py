from datetime import datetime
from learnus.models import (
    Assignment, Course, Feedback, Material, NoticePost, Quiz, Video,
)


def test_assignment_defaults():
    a = Assignment(title="HW1", due_at=None, submitted=False, url="http://x")
    assert a.title == "HW1"


def test_video_fields():
    v = Video(title="W1 강의", week=1, starts_at=datetime(2026, 4, 14),
              ends_at=datetime(2026, 4, 20), late_until=datetime(2026, 4, 27),
              watched=False, length="40:25", url="http://x")
    assert v.week == 1
    assert v.watched is False
    assert v.length == "40:25"


def test_feedback_fields():
    f = Feedback(title="설문1", opens_at=datetime(2026, 4, 14),
                 closes_at=datetime(2026, 4, 20), submitted=False, url="http://x")
    assert f.submitted is False


def test_notice_post_fields():
    p = NoticePost(title="중간고사 안내", author="이경호",
                   posted_at=datetime(2026, 3, 27, 15, 52),
                   body="본문 내용", url="http://x")
    assert p.author == "이경호"
    assert p.body == "본문 내용"


def test_material_kind_values():
    m = Material(title="강의1", week=1, posted_at=None, kind="video", url="http://x")
    assert m.kind == "video"


def test_quiz_fields():
    q = Quiz(title="퀴즈1", opens_at=datetime(2026, 4, 14),
             closes_at=datetime(2026, 4, 15), url="http://x")
    assert q.opens_at.day == 14


def test_course_has_all_collections():
    c = Course(id="1", name="자료구조", url="http://x")
    assert c.assignments == []
    assert c.videos == []
    assert c.feedbacks == []
    assert c.materials == []
    assert c.quizzes == []
    assert c.notices == []
