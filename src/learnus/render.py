import json
from dataclasses import asdict
from datetime import datetime
from typing import Iterable

from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from learnus.models import Course

_console = Console()


def render_courses(courses: Iterable[Course]) -> None:
    for course in courses:
        body = Text()
        _append_assignments(body, course)
        _append_notices(body, course)
        _append_materials(body, course)
        _append_quizzes(body, course)
        _console.print(Panel(body, title=course.name, title_align="left"))


def _append_assignments(body: Text, course: Course) -> None:
    body.append("과제\n", style="bold")
    if not course.assignments:
        body.append("  (없음)\n", style="dim")
        return
    now = datetime.now()
    for a in course.assignments:
        mark = "[✓]" if a.submitted else "[ ]"
        due = _format_due(a.due_at, now) if a.due_at else "마감 없음"
        line = f"  {mark} {a.title}    {due}\n"
        body.append(line, style="dim" if a.submitted else None)


def _append_notices(body: Text, course: Course) -> None:
    body.append("공지\n", style="bold")
    if not course.notices:
        body.append("  (없음)\n", style="dim")
        return
    for n in course.notices:
        date = n.posted_at.strftime("%Y-%m-%d") if n.posted_at else "날짜없음"
        body.append(f"  • {n.title}    {date}\n")


def _append_materials(body: Text, course: Course) -> None:
    body.append("자료\n", style="bold")
    if not course.materials:
        body.append("  (없음)\n", style="dim")
        return
    for m in course.materials:
        date = m.posted_at.strftime("%Y-%m-%d") if m.posted_at else ""
        body.append(f"  • [{m.kind}] {m.title}    {date}\n")


def _append_quizzes(body: Text, course: Course) -> None:
    body.append("퀴즈\n", style="bold")
    if not course.quizzes:
        body.append("  (없음)\n", style="dim")
        return
    for q in course.quizzes:
        close = q.closes_at.strftime("%Y-%m-%d %H:%M") if q.closes_at else "마감 미정"
        body.append(f"  • {q.title}    마감 {close}\n")


def _format_due(due: datetime, now: datetime) -> str:
    delta_days = (due.date() - now.date()).days
    if delta_days > 0:
        ddays = f"D-{delta_days}"
    elif delta_days == 0:
        ddays = "D-day"
    else:
        ddays = f"D+{-delta_days}"
    return f"마감 {due.strftime('%Y-%m-%d %H:%M')}  ({ddays})"


def render_upcoming(courses: Iterable[Course], now: datetime | None = None) -> None:
    now = now or datetime.now()
    rows: list[tuple[datetime, str, str, str]] = []
    for course in courses:
        for a in course.assignments:
            if a.submitted or a.due_at is None or a.due_at < now:
                continue
            rows.append((a.due_at, "과제", course.name, a.title))
        for q in course.quizzes:
            if q.closes_at is None or q.closes_at < now:
                continue
            rows.append((q.closes_at, "퀴즈", course.name, q.title))
    rows.sort(key=lambda r: r[0])
    for due, kind, course_name, title in rows:
        delta = (due.date() - now.date()).days
        ddays = f"D-{delta}" if delta > 0 else ("D-day" if delta == 0 else f"D+{-delta}")
        _console.print(f"{ddays}  [{kind}]  {course_name}  | {title}    마감 {due.strftime('%Y-%m-%d %H:%M')}")


def render_json(courses: Iterable[Course]) -> None:
    payload = [asdict(c) for c in courses]
    _console.print(json.dumps(payload, default=_json_default, ensure_ascii=False, indent=2))


def _json_default(obj):
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(f"not serializable: {type(obj)}")
