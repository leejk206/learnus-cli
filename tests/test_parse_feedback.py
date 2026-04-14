from datetime import datetime
from pathlib import Path

from learnus.parsers.feedback import parse_feedbacks

FIX = Path(__file__).parent / "fixtures"


def test_parse_feedbacks_reads_availability_info():
    html = (FIX / "course_page.html").read_text(encoding="utf-8")
    fbs = parse_feedbacks(html)

    assert len(fbs) == 1
    f = fbs[0]
    assert f.title == "강의 만족도 설문"
    assert f.submitted is False
    assert f.opens_at == datetime(2026, 4, 14)
    assert f.closes_at == datetime(2026, 4, 20)
    assert f.url == "https://ys.learnus.org/mod/feedback/view.php?id=88888"


def test_parse_feedbacks_empty():
    assert parse_feedbacks("<html></html>") == []
