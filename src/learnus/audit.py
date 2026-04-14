from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime

from bs4 import BeautifulSoup

from learnus.models import Course

HANDLED_TYPES: frozenset[str] = frozenset({
    "assign",
    "turnitintooltwo",
    "vod",
    "feedback",
    "quiz",
    "ubboard",
    "ubfile",
    "url",
    "resource",
})

SAFELY_IGNORED_TYPES: frozenset[str] = frozenset({
    "label",
})


@dataclass
class CourseAudit:
    name: str
    handled_types: dict[str, int] = field(default_factory=dict)
    unhandled_types: dict[str, int] = field(default_factory=dict)
    assignments_count: int = 0
    assignments_missing_due: int = 0
    videos_count: int = 0
    videos_missing_deadline: int = 0
    feedbacks_count: int = 0
    feedbacks_missing_deadline: int = 0
    quizzes_count: int = 0
    quizzes_missing_deadline: int = 0
    notices_count: int = 0
    notice_board_missing: bool = False


@dataclass
class AuditReport:
    generated_at: datetime
    courses: list[CourseAudit] = field(default_factory=list)


def run_audit(courses: list[Course], session) -> AuditReport:
    audits: list[CourseAudit] = []
    for c in courses:
        handled, unhandled = _activity_type_counts(session, c.url)
        audits.append(CourseAudit(
            name=c.name,
            handled_types=handled,
            unhandled_types=unhandled,
            assignments_count=len(c.assignments),
            assignments_missing_due=sum(1 for a in c.assignments if a.due_at is None),
            videos_count=len(c.videos),
            videos_missing_deadline=sum(
                1 for v in c.videos if (v.late_until or v.ends_at) is None
            ),
            feedbacks_count=len(c.feedbacks),
            feedbacks_missing_deadline=sum(
                1 for f in c.feedbacks if f.closes_at is None
            ),
            quizzes_count=len(c.quizzes),
            quizzes_missing_deadline=sum(
                1 for q in c.quizzes if (q.closes_at or q.opens_at) is None
            ),
            notices_count=len(c.notices),
            notice_board_missing=(
                handled.get("ubboard", 0) > 0 and len(c.notices) == 0
            ),
        ))
    return AuditReport(generated_at=datetime.now(), courses=audits)


def _activity_type_counts(session, course_url: str) -> tuple[dict[str, int], dict[str, int]]:
    try:
        html = session.get(course_url, timeout=15).text
    except Exception:
        return {}, {}
    soup = BeautifulSoup(html, "lxml")
    handled: Counter[str] = Counter()
    unhandled: Counter[str] = Counter()
    for li in soup.select("li.activity"):
        t = _extract_type(li)
        if t is None:
            continue
        if t in HANDLED_TYPES:
            handled[t] += 1
        elif t in SAFELY_IGNORED_TYPES:
            continue
        else:
            unhandled[t] += 1
    return dict(handled), dict(unhandled)


def _extract_type(li) -> str | None:
    for cls in li.get("class", []):
        if cls == "activity":
            continue
        if cls.startswith("modtype_"):
            continue
        return cls
    return None


def aggregate_unhandled(report: AuditReport) -> dict[str, list[str]]:
    """For each unhandled type, list the course names where it appears."""
    out: dict[str, list[str]] = {}
    for c in report.courses:
        for t in c.unhandled_types:
            out.setdefault(t, []).append(c.name)
    return out
