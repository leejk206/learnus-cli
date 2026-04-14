from pathlib import Path

from learnus.parsers.material import parse_materials

FIX = Path(__file__).parent / "fixtures"


def test_parse_materials_separates_video_and_file():
    html = (FIX / "course_page.html").read_text(encoding="utf-8")
    materials = parse_materials(html)

    kinds = {m.kind for m in materials}
    assert kinds == {"video", "file"}

    video = next(m for m in materials if m.kind == "video")
    assert video.title == "1주차 강의 영상"
    assert video.week == 1

    file = next(m for m in materials if m.kind == "file")
    assert file.title == "1주차 강의노트.pdf"
    assert file.week == 1


def test_parse_materials_empty_when_none():
    assert parse_materials("<html></html>") == []
