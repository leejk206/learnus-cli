from datetime import datetime

from learnus.models import (
    Assignment, Course, Feedback, NoticePost, Quiz, Video,
)
from learnus.summary import SummaryReport, build_summary


NOW = datetime(2026, 4, 14, 10, 0, 0)


def _sample_courses():
    return [
        Course(
            id="1", name="자료구조", url="http://x",
            assignments=[
                Assignment(title="HW3", due_at=datetime(2026, 4, 20, 23, 59),
                           submitted=False, url="http://x/a1"),
                Assignment(title="HW2", due_at=datetime(2026, 4, 10, 23, 59),
                           submitted=True, url="http://x/a2"),
                Assignment(title="HW1", due_at=datetime(2026, 4, 8),
                           submitted=True, url="http://x/a3"),
            ],
            videos=[
                Video(title="W2 강의", week=2,
                      starts_at=datetime(2026, 3, 10), ends_at=datetime(2026, 3, 16, 23, 59, 59),
                      late_until=datetime(2026, 3, 23, 23, 59, 59),
                      watched=False, length="40:25", url="http://x/v1"),
                Video(title="W6 강의", week=6,
                      starts_at=datetime(2026, 4, 14), ends_at=datetime(2026, 4, 20, 23, 59, 59),
                      late_until=datetime(2026, 4, 27, 23, 59, 59),
                      watched=False, length="25:10", url="http://x/v2"),
                Video(title="W1 강의", week=1,
                      starts_at=datetime(2026, 3, 3), ends_at=datetime(2026, 3, 9, 23, 59, 59),
                      late_until=None, watched=True, length="30:00", url="http://x/v3"),
            ],
            feedbacks=[
                Feedback(title="중간 설문", opens_at=datetime(2026, 4, 14),
                         closes_at=datetime(2026, 4, 20), submitted=False, url="http://x/f1"),
            ],
            quizzes=[
                Quiz(title="Q5", opens_at=datetime(2026, 4, 15, 16, 5),
                     closes_at=datetime(2026, 4, 15, 16, 15), url="http://x/q1"),
            ],
            notices=[
                NoticePost(title="공지A", author="교수", posted_at=datetime(2026, 4, 10),
                           body="내용", url="http://x/n1"),
                NoticePost(title="공지B", author="교수", posted_at=datetime(2026, 4, 12),
                           body="내용2", url="http://x/n2"),
            ],
        ),
    ]


def test_videos_to_watch_filters_watched_and_expired():
    report = build_summary(_sample_courses(), now=NOW)
    titles = [item.video.title for item in report.videos_to_watch]
    assert "W6 강의" in titles
    assert "W1 강의" not in titles
    assert "W2 강의" not in titles


def test_videos_sorted_by_deadline():
    courses = _sample_courses()
    courses[0].videos.append(Video(
        title="W7 강의", week=7, starts_at=datetime(2026, 4, 21),
        ends_at=datetime(2026, 4, 27, 23, 59, 59),
        late_until=datetime(2026, 5, 4, 23, 59, 59),
        watched=False, length="20:00", url="http://x/v4",
    ))
    report = build_summary(courses, now=NOW)
    order = [item.video.title for item in report.videos_to_watch]
    assert order == ["W6 강의", "W7 강의"]


def test_pending_submissions_includes_assignment_and_feedback():
    report = build_summary(_sample_courses(), now=NOW)
    kinds = [i.kind for i in report.pending_submissions]
    titles = [i.title for i in report.pending_submissions]
    assert "과제" in kinds
    assert "설문" in kinds
    assert "HW3" in titles
    assert "중간 설문" in titles
    assert "HW2" not in titles


def test_upcoming_schedule_includes_quiz_and_future_assignments():
    report = build_summary(_sample_courses(), now=NOW)
    titles = [i.title for i in report.upcoming_schedule]
    kinds = [i.kind for i in report.upcoming_schedule]
    assert "Q5" in titles
    assert "HW3" in titles
    assert "HW1" not in titles
    assert "퀴즈" in kinds
    assert "과제" in kinds


def test_notices_by_course_sorted_latest_first():
    report = build_summary(_sample_courses(), now=NOW)
    posts = report.notices_by_course["자료구조"]
    assert [p.title for p in posts] == ["공지B", "공지A"]


def test_pending_submissions_includes_undated_assignment_at_end():
    courses = [
        Course(
            id="1", name="보안", url="http://x",
            assignments=[
                Assignment(title="HW_dated", due_at=datetime(2026, 4, 20, 23, 59),
                           submitted=False, url="http://x/1"),
                Assignment(title="HW_undated", due_at=None,
                           submitted=False, url="http://x/2"),
                Assignment(title="HW_submitted_undated", due_at=None,
                           submitted=True, url="http://x/3"),
            ],
        ),
    ]
    report = build_summary(courses, now=NOW)
    titles = [i.title for i in report.pending_submissions]
    assert titles == ["HW_dated", "HW_undated"]
    undated = report.pending_submissions[1]
    assert undated.due_at is None
    assert undated.days_left is None


def test_empty_courses_produces_empty_report():
    report = build_summary([], now=NOW)
    assert isinstance(report, SummaryReport)
    assert report.videos_to_watch == []
    assert report.pending_submissions == []
    assert report.upcoming_schedule == []
    assert report.notices_by_course == {}
