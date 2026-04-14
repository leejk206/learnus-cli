from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock

from learnus.parsers.notice import parse_notices

FIX = Path(__file__).parent / "fixtures"


def test_parse_notices_lists_posts_without_fetching_body():
    course_html = (FIX / "course_page.html").read_text(encoding="utf-8")
    list_html = (FIX / "ubboard_list.html").read_text(encoding="utf-8")

    session = MagicMock()

    def fake_get(url, *args, **kwargs):
        resp = MagicMock()
        if "/mod/ubboard/view.php" in url:
            resp.text = list_html
        else:
            resp.text = "<html></html>"
        return resp

    session.get.side_effect = fake_get

    posts = parse_notices(course_html, session)

    assert len(posts) == 2
    assert posts[0].title == "중간시험 일정 안내"
    assert posts[0].author == "이경호"
    assert posts[0].posted_at == datetime(2026, 3, 27)
    assert posts[0].body == ""
    # Article pages must not be fetched
    calls = [c.args[0] for c in session.get.call_args_list]
    assert not any("/article.php" in u for u in calls)


def test_parse_notices_no_notice_board_returns_empty():
    session = MagicMock()
    html = "<html><body><ul class='topics'></ul></body></html>"
    assert parse_notices(html, session) == []


def test_parse_notices_board_fetch_error_returns_empty():
    course_html = (FIX / "course_page.html").read_text(encoding="utf-8")
    session = MagicMock()
    session.get.side_effect = RuntimeError("down")
    assert parse_notices(course_html, session) == []


def test_parse_notices_matches_english_announcement_board():
    # course page has three ubboard activities: Class Announcements, Class Q&A, Class Files.
    # Only the announcement board should be selected.
    course_html = """<html><body><ul class='topics'><li class='section'>
      <ul>
        <li class='activity ubboard modtype_ubboard'>
          <div class='activityinstance'><a href='http://x/announce'>
            <span class='instancename'>Class Announcements<span class='accesshide'>Board</span></span>
          </a></div>
        </li>
        <li class='activity ubboard modtype_ubboard'>
          <div class='activityinstance'><a href='http://x/qa'>
            <span class='instancename'>Class Q&A<span class='accesshide'>Board</span></span>
          </a></div>
        </li>
        <li class='activity ubboard modtype_ubboard'>
          <div class='activityinstance'><a href='http://x/files'>
            <span class='instancename'>Class Files<span class='accesshide'>Board</span></span>
          </a></div>
        </li>
      </ul>
    </li></ul></body></html>"""
    list_html = (FIX / "ubboard_list.html").read_text(encoding="utf-8")

    session = MagicMock()
    fetched = []

    def fake_get(url, *args, **kwargs):
        fetched.append(url)
        resp = MagicMock()
        resp.text = list_html
        return resp

    session.get.side_effect = fake_get
    posts = parse_notices(course_html, session)
    assert len(posts) == 2
    # Only the announcement board was fetched, not Q&A or Files
    assert fetched == ["http://x/announce"]
