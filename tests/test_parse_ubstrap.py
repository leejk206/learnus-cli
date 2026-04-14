from datetime import datetime
from learnus.parsers._ubstrap import parse_ubstrap


def test_full_with_late():
    text = "2026-04-14 00:00:00 ~ 2026-04-20 23:59:59 (지각 : 2026-04-27 23:59:59)"
    start, end, late = parse_ubstrap(text)
    assert start == datetime(2026, 4, 14, 0, 0, 0)
    assert end == datetime(2026, 4, 20, 23, 59, 59)
    assert late == datetime(2026, 4, 27, 23, 59, 59)


def test_without_late():
    text = "2026-03-03 00:00:00 ~ 2026-03-09 23:59:59"
    start, end, late = parse_ubstrap(text)
    assert start == datetime(2026, 3, 3)
    assert end == datetime(2026, 3, 9, 23, 59, 59)
    assert late is None


def test_empty_returns_all_none():
    assert parse_ubstrap("") == (None, None, None)


def test_malformed_returns_all_none():
    assert parse_ubstrap("언젠가 마감") == (None, None, None)
