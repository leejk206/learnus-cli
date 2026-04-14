from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock

from learnus.parsers.notice import parse_notices

FIX = Path(__file__).parent / "fixtures"


def test_parse_notices_lists_posts_and_fetches_body():
    course_html = (FIX / "course_page.html").read_text(encoding="utf-8")
    list_html = (FIX / "ubboard_list.html").read_text(encoding="utf-8")
    post_html = (FIX / "notice_post.html").read_text(encoding="utf-8")

    session = MagicMock()

    def fake_get(url, *args, **kwargs):
        resp = MagicMock()
        if "/mod/ubboard/view.php" in url:
            resp.text = list_html
        elif "/mod/ubboard/article.php" in url:
            resp.text = post_html
        else:
            resp.text = "<html></html>"
        return resp

    session.get.side_effect = fake_get

    posts = parse_notices(course_html, session)

    assert len(posts) == 2
    assert posts[0].title == "중간시험 일정 안내"
    assert posts[0].author == "이경호"
    assert posts[0].posted_at == datetime(2026, 3, 27, 15, 52)
    assert "중간시험 일정을 아래와 같이 공지합니다" in posts[0].body


def test_parse_notices_no_notice_board_returns_empty():
    session = MagicMock()
    html = "<html><body><ul class='topics'></ul></body></html>"
    assert parse_notices(html, session) == []


def test_parse_notices_continues_on_post_fetch_error():
    course_html = (FIX / "course_page.html").read_text(encoding="utf-8")
    list_html = (FIX / "ubboard_list.html").read_text(encoding="utf-8")
    post_html = (FIX / "notice_post.html").read_text(encoding="utf-8")

    session = MagicMock()
    call_count = {"n": 0}

    def fake_get(url, *args, **kwargs):
        resp = MagicMock()
        if "/mod/ubboard/view.php" in url:
            resp.text = list_html
            return resp
        if "/mod/ubboard/article.php" in url:
            call_count["n"] += 1
            if call_count["n"] == 1:
                raise RuntimeError("boom")
            resp.text = post_html
            return resp
        resp.text = "<html></html>"
        return resp

    session.get.side_effect = fake_get
    posts = parse_notices(course_html, session)
    assert len(posts) == 2
    assert posts[0].body == ""  # failed
    assert posts[1].body != ""  # succeeded
