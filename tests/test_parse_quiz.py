from pathlib import Path

from learnus.parsers.quiz import parse_quizzes

FIX = Path(__file__).parent / "fixtures"


def test_parse_quizzes_from_course_page():
    html = (FIX / "course_page.html").read_text(encoding="utf-8")
    quizzes = parse_quizzes(html)
    assert len(quizzes) == 1
    assert quizzes[0].title == "2주차 퀴즈"
    assert quizzes[0].url == "https://ys.learnus.org/mod/quiz/view.php?id=66666"


def test_parse_quizzes_empty_when_none():
    assert parse_quizzes("<html></html>") == []
