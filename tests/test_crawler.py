from pathlib import Path
from unittest.mock import MagicMock

from learnus.crawler import fetch_all

FIX = Path(__file__).parent / "fixtures"


def test_fetch_all_populates_courses_with_items():
    dashboard = (FIX / "dashboard.html").read_text(encoding="utf-8")
    course_page = (FIX / "course_page.html").read_text(encoding="utf-8")
    assignment_detail = (FIX / "assignment_detail.html").read_text(encoding="utf-8")
    quiz_detail = (FIX / "quiz_detail.html").read_text(encoding="utf-8")
    ubboard_list = (FIX / "ubboard_list.html").read_text(encoding="utf-8")
    notice_post = (FIX / "notice_post.html").read_text(encoding="utf-8")

    session = MagicMock()

    def fake_get(url, *args, **kwargs):
        resp = MagicMock()
        if url.endswith("ys.learnus.org/") or url.endswith("ys.learnus.org"):
            resp.text = dashboard
        elif "/course/view.php" in url:
            resp.text = course_page
        elif "/mod/assign/view.php" in url:
            resp.text = assignment_detail
        elif "/mod/quiz/view.php" in url:
            resp.text = quiz_detail
        elif "/mod/ubboard/view.php" in url:
            resp.text = ubboard_list
        elif "/mod/ubboard/article.php" in url:
            resp.text = notice_post
        else:
            resp.text = "<html></html>"
        return resp

    session.get.side_effect = fake_get

    courses = fetch_all(session)

    assert len(courses) == 2
    first = courses[0]
    assert len(first.assignments) == 2
    assert len(first.videos) == 2
    assert len(first.feedbacks) == 1
    assert len(first.quizzes) == 1
    assert len(first.notices) == 2
    assert len(first.materials) == 3  # 2 vods (counted as video kind) + 1 ubfile


def test_fetch_all_continues_on_course_page_error():
    dashboard = (FIX / "dashboard.html").read_text(encoding="utf-8")

    session = MagicMock()
    calls = {"n": 0}

    def fake_get(url, *args, **kwargs):
        resp = MagicMock()
        if "/course/view.php?id=12345" in url:
            raise RuntimeError("boom")
        calls["n"] += 1
        resp.text = dashboard if calls["n"] == 1 else "<html></html>"
        return resp

    session.get.side_effect = fake_get
    courses = fetch_all(session)
    assert len(courses) == 2
    assert courses[0].assignments == []
