import json
import sys
from dataclasses import asdict
from datetime import datetime
from typing import Iterable

from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from learnus.audit import AuditReport, CourseAudit, aggregate_unhandled
from learnus.models import Course
from learnus.summary import SummaryReport, TaskItem, VideoItem  # noqa: F401

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

    _console.rule("[bold]2. 제출해야 할 과제/설문/시험 (남은 기한 순)")
    if not report.pending_submissions:
        _console.print("[dim](없음)[/]")
    for item in report.pending_submissions:
        _console.print(_format_task_line_dday(item))

    _console.rule("[bold]3. 과목별 공지")
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
    if item.days_left is None or item.due_at is None:
        return f"마감 미정  \\[{item.kind}]  {item.course_name}  | {item.title}"
    dday = _format_dday_compact(item.days_left)
    return (
        f"{dday}  \\[{item.kind}]  {item.course_name}  | {item.title}  "
        f"마감 {item.due_at:%Y-%m-%d %H:%M}"
    )


def render_audit_terminal(report: AuditReport) -> None:
    _console.rule("[bold]파서 커버리지 진단 (Audit)")
    total = len(report.courses)
    total_unhandled = sum(len(c.unhandled_types) for c in report.courses)
    _console.print(
        f"강좌 {total}개 분석 · 파서가 모르는 활동 타입 "
        f"{total_unhandled}종 발견\n"
    )

    for c in report.courses:
        _render_course_audit(c)

    unhandled_by_type = aggregate_unhandled(report)
    if unhandled_by_type:
        _console.rule("[bold]처리되지 않는 활동 타입 전체 목록")
        for t, course_names in sorted(unhandled_by_type.items()):
            _console.print(f"  [red]{t}[/]  ({len(course_names)}개 강좌)")
            for n in course_names[:3]:
                _console.print(f"    - {n}")
        _console.print(
            "\n[dim]위 타입이 포함된 항목은 요약에 나타나지 않습니다. "
            "중요한 항목이면 이슈를 열거나 파서를 추가해주세요.[/]"
        )
    else:
        _console.print(
            "\n[green]모든 활동 타입이 파서에 의해 처리됩니다.[/]"
        )


def _render_course_audit(c: CourseAudit) -> None:
    _console.print(f"[bold cyan]{c.name}[/]")
    if c.handled_types:
        handled_str = ", ".join(
            f"{t}×{n}" for t, n in sorted(c.handled_types.items())
        )
        _console.print(f"  [green]✓ 처리됨:[/] {handled_str}")
    else:
        _console.print("  [dim]처리된 활동 없음[/]")

    if c.unhandled_types:
        unhandled_str = ", ".join(
            f"{t}×{n}" for t, n in sorted(c.unhandled_types.items())
        )
        _console.print(f"  [red]⚠ 미처리:[/] {unhandled_str}")

    warnings: list[str] = []
    if c.assignments_missing_due:
        warnings.append(f"과제 {c.assignments_missing_due}개 마감일 없음")
    if c.quizzes_missing_deadline:
        warnings.append(f"퀴즈 {c.quizzes_missing_deadline}개 기한 없음")
    if c.feedbacks_missing_deadline:
        warnings.append(f"설문 {c.feedbacks_missing_deadline}개 기한 없음")
    if c.videos_missing_deadline:
        warnings.append(f"영상 {c.videos_missing_deadline}개 기한 없음")
    if c.notice_board_missing:
        warnings.append(
            "공지 게시판 미인식 (이름에 '공지' 또는 'announcement'가 없음)"
        )
    if warnings:
        _console.print(f"  [yellow]! 참고:[/] " + " · ".join(warnings))
    _console.print()


def _format_dday_compact(days_left: int) -> str:
    if days_left > 0:
        return f"D-{days_left}"
    if days_left == 0:
        return "D-day"
    return f"D+{-days_left}"
