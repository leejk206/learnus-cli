from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock

from learnus.parsers.quiz import parse_quizzes

FIX = Path(__file__).parent / "fixtures"


def test_parse_quizzes_fetches_dates_from_detail():
    html = (FIX / "course_page.html").read_text(encoding="utf-8")
    detail = (FIX / "quiz_detail.html").read_text(encoding="utf-8")

    session = MagicMock()
    session.get.return_value.text = detail

    quizzes = parse_quizzes(html, session)
    assert len(quizzes) == 1
    q = quizzes[0]
    assert q.title == "2주차 퀴즈"
    assert q.url == "https://ys.learnus.org/mod/quiz/view.php?id=77777"
    assert q.opens_at == datetime(2026, 4, 13, 0, 0)
    assert q.closes_at == datetime(2026, 4, 26, 23, 59)


def test_parse_quizzes_empty():
    session = MagicMock()
    assert parse_quizzes("<html></html>", session) == []


def test_parse_quizzes_detail_network_error_keeps_title():
    html = (FIX / "course_page.html").read_text(encoding="utf-8")
    session = MagicMock()
    session.get.side_effect = RuntimeError("network down")
    quizzes = parse_quizzes(html, session)
    assert len(quizzes) == 1
    assert quizzes[0].opens_at is None
    assert quizzes[0].closes_at is None
