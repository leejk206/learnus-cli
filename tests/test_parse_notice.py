from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock

from learnus.parsers.notice import parse_notices

FIX = Path(__file__).parent / "fixtures"


def test_parse_notices_from_course_page():
    html = (FIX / "course_page.html").read_text(encoding="utf-8")
    detail_html = (FIX / "notice_detail.html").read_text(encoding="utf-8")

    session = MagicMock()
    session.get.return_value.text = detail_html

    notices = parse_notices(html, session)

    assert len(notices) == 1
    assert notices[0].title == "중간고사 범위 안내"
    assert notices[0].url == "https://ys.learnus.org/mod/ubboard/view.php?id=55555"
    assert notices[0].posted_at == datetime(2026, 4, 10, 9, 30)


def test_parse_notices_empty_when_none():
    session = MagicMock()
    assert parse_notices("<html></html>", session) == []
