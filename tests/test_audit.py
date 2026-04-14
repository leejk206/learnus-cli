from unittest.mock import MagicMock

from learnus.audit import (
    AuditReport,
    aggregate_unhandled,
    run_audit,
)
from learnus.models import Assignment, Course, Quiz, Video


_COURSE_HTML = """<html><body>
<ul class="topics">
  <li class="section">
    <ul>
      <li class="activity assign modtype_assign"></li>
      <li class="activity assign modtype_assign"></li>
      <li class="activity vod modtype_vod"></li>
      <li class="activity ubboard modtype_ubboard"></li>
      <li class="activity label modtype_label"></li>
      <li class="activity workshop modtype_workshop"></li>
      <li class="activity laby modtype_laby"></li>
      <li class="activity laby modtype_laby"></li>
    </ul>
  </li>
</ul>
</body></html>"""


def _course(name="C1", assignments=None, quizzes=None, videos=None, notices=None):
    return Course(
        id="1", name=name, url="http://x",
        assignments=assignments or [],
        quizzes=quizzes or [],
        videos=videos or [],
        notices=notices or [],
    )


def test_run_audit_counts_handled_and_unhandled_types():
    session = MagicMock()
    session.get.return_value.text = _COURSE_HTML

    report = run_audit([_course()], session)
    assert len(report.courses) == 1
    c = report.courses[0]
    assert c.handled_types == {"assign": 2, "vod": 1, "ubboard": 1}
    assert c.unhandled_types == {"workshop": 1, "laby": 2}


def test_run_audit_reports_missing_deadlines():
    session = MagicMock()
    session.get.return_value.text = _COURSE_HTML

    courses = [_course(
        assignments=[
            Assignment(title="A", due_at=None, submitted=False, url="http://x"),
            Assignment(title="B", due_at=None, submitted=True, url="http://x"),
        ],
        quizzes=[Quiz(title="Q", opens_at=None, closes_at=None, url="http://x")],
    )]
    report = run_audit(courses, session)
    c = report.courses[0]
    assert c.assignments_count == 2
    assert c.assignments_missing_due == 2
    assert c.quizzes_count == 1
    assert c.quizzes_missing_deadline == 1


def test_run_audit_flags_missing_notice_board():
    # Course HAS an ubboard activity but no notices were parsed (e.g., board
    # name didn't contain 공지/announcement).
    session = MagicMock()
    session.get.return_value.text = _COURSE_HTML

    report = run_audit([_course(notices=[])], session)
    assert report.courses[0].notice_board_missing is True


def test_run_audit_ok_when_no_ubboard_at_all():
    html = """<html><body><ul class='topics'><li class='section'><ul>
      <li class='activity assign modtype_assign'></li>
    </ul></li></ul></body></html>"""
    session = MagicMock()
    session.get.return_value.text = html

    report = run_audit([_course()], session)
    assert report.courses[0].notice_board_missing is False


def test_aggregate_unhandled_lists_courses_per_type():
    session = MagicMock()
    session.get.return_value.text = _COURSE_HTML
    report = run_audit(
        [_course(name="알파"), _course(name="베타")], session
    )
    agg = aggregate_unhandled(report)
    assert set(agg["workshop"]) == {"알파", "베타"}
    assert set(agg["laby"]) == {"알파", "베타"}


def test_run_audit_empty_courses():
    report = run_audit([], MagicMock())
    assert isinstance(report, AuditReport)
    assert report.courses == []
