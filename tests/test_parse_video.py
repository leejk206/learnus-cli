from datetime import datetime
from pathlib import Path

from learnus.parsers.video import parse_videos

FIX = Path(__file__).parent / "fixtures"


def test_parse_videos_extracts_ubstrap_and_watched():
    html = (FIX / "course_page.html").read_text(encoding="utf-8")
    videos = parse_videos(html)

    assert len(videos) == 2

    w1 = next(v for v in videos if v.week == 1)
    assert w1.title == "1주차 강의 영상"
    assert w1.watched is True
    assert w1.starts_at == datetime(2026, 3, 3)
    assert w1.ends_at == datetime(2026, 3, 9, 23, 59, 59)
    assert w1.late_until == datetime(2026, 3, 16, 23, 59, 59)
    assert w1.length == "40:25"
    assert w1.url == "https://ys.learnus.org/mod/vod/view.php?id=22222"

    w2 = next(v for v in videos if v.week == 2)
    assert w2.watched is False
    assert w2.length == "25:10"


def test_parse_videos_empty():
    assert parse_videos("<html></html>") == []
