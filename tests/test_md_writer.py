from datetime import datetime

from learnus.md_writer import render_summary_markdown
from learnus.models import Assignment, Course, Feedback, NoticePost, Quiz, Video
from learnus.summary import build_summary

NOW = datetime(2026, 4, 14, 10, 0, 0)


def _courses():
    return [
        Course(
            id="1", name="자료구조", url="http://x",
            assignments=[
                Assignment(title="HW3", due_at=datetime(2026, 4, 20, 23, 59),
                           submitted=False, url="http://x/a1"),
            ],
            videos=[
                Video(title="W6 강의", week=6,
                      starts_at=datetime(2026, 4, 14), ends_at=datetime(2026, 4, 20, 23, 59, 59),
                      late_until=datetime(2026, 4, 27, 23, 59, 59),
                      watched=False, length="25:10", url="http://x/v1"),
            ],
            feedbacks=[
                Feedback(title="설문", opens_at=datetime(2026, 4, 14),
                         closes_at=datetime(2026, 4, 20), submitted=False, url="http://x/f1"),
            ],
            quizzes=[
                Quiz(title="Q5", opens_at=datetime(2026, 4, 15, 16, 5),
                     closes_at=datetime(2026, 4, 15, 16, 15), url="http://x/q1"),
            ],
            notices=[
                NoticePost(title="공지A", author="교수",
                           posted_at=datetime(2026, 4, 10, 9, 0),
                           body="", url="http://x/n1"),
            ],
        )
    ]


def test_markdown_has_all_sections():
    md = render_summary_markdown(build_summary(_courses(), now=NOW))
    assert "# LearnUs 요약" in md
    assert "## 1. 들어야 할 강의 영상" in md
    assert "## 2. 제출해야 할 과제/설문/시험" in md
    assert "## 3. 과목별 공지" in md
    assert "앞으로의 시험/과제 일정" not in md


def test_markdown_contains_items_and_notice_titles():
    md = render_summary_markdown(build_summary(_courses(), now=NOW))
    assert "W6 강의" in md
    assert "25:10" in md
    assert "HW3" in md
    assert "Q5" in md
    assert "설문" in md
    assert "시험" in md            # quiz rendered as 시험 kind
    assert "공지A" in md
    # body should not appear
    assert "본문" not in md


def test_markdown_days_left_formatted():
    md = render_summary_markdown(build_summary(_courses(), now=NOW))
    # HW3 due 2026-04-20 from NOW 2026-04-14 → D-6
    assert "D-6" in md
