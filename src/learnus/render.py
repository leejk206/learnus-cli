import json
import sys
from dataclasses import asdict
from datetime import datetime
from typing import Iterable

from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from learnus.models import Course
from learnus.summary import SummaryReport, TaskItem, VideoItem

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
    sys.stdout.write(json.dumps(payload, default=_json_default, ensure_ascii=False, indent=2))
    sys.stdout.write("\n")


def _json_default(obj):
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(f"not serializable: {type(obj)}")


def render_summary_terminal(report: SummaryReport) -> None:
    _console.rule("[bold]1. 들어야 할 강의 영상 (남은 기한 순)")
    if not report.videos_to_watch:
        _console.print("[dim](없음)[/]")
    for item in report.videos_to_watch:
        _console.print(_format_video_line(item))

    _console.rule("[bold]2. 제출해야 할 과제/설문 (남은 기한 순)")
    if not report.pending_submissions:
        _console.print("[dim](없음)[/]")
    for item in report.pending_submissions:
        _console.print(_format_task_line_dday(item))

    _console.rule("[bold]3. 앞으로의 시험/과제 일정")
    if not report.upcoming_schedule:
        _console.print("[dim](없음)[/]")
    for item in report.upcoming_schedule:
        _console.print(_format_task_line_date(item))

    _console.rule("[bold]4. 과목별 공지")
    if not report.notices_by_course:
        _console.print("[dim](없음)[/]")
    for course_name, posts in report.notices_by_course.items():
        _console.print(f"\n[bold cyan]{course_name}[/]")
        for p in posts:
            date_str = f"{p.posted_at:%Y-%m-%d}" if p.posted_at else "날짜 미상"
            _console.print(f"  • {p.title}  [dim]({p.author} · {date_str})[/]")


def _format_video_line(item: VideoItem) -> str:
    v = item.video
    dday = _format_dday_compact(item.days_left)
    week = f"W{v.week}" if v.week is not None else "W?"
    length = v.length or "-"
    deadline = v.late_until or v.ends_at
    deadline_str = f"{deadline:%Y-%m-%d %H:%M}" if deadline else "-"
    return f"{dday}  [{week}] {item.course_name}  | {v.title} ({length})  ~{deadline_str}"


def _format_task_line_dday(item: TaskItem) -> str:
    dday = _format_dday_compact(item.days_left)
    return (
        f"{dday}  \\[{item.kind}]  {item.course_name}  | {item.title}  "
        f"마감 {item.due_at:%Y-%m-%d %H:%M}"
    )


def _format_task_line_date(item: TaskItem) -> str:
    return (
        f"{item.due_at:%Y-%m-%d %H:%M}  \\[{item.kind}]  {item.course_name}  | {item.title}"
    )


def _format_dday_compact(days_left: int) -> str:
    if days_left > 0:
        return f"D-{days_left}"
    if days_left == 0:
        return "D-day"
    return f"D+{-days_left}"
