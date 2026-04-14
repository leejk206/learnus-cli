from learnus.summary import SummaryReport, TaskItem, VideoItem


def render_summary_markdown(report: SummaryReport) -> str:
    lines: list[str] = []
    lines.append(f"# LearnUs 요약 · {report.generated_at:%Y-%m-%d %H:%M}")
    lines.append("")

    lines.append("## 1. 들어야 할 강의 영상 (남은 기한 순)")
    lines.append("")
    if not report.videos_to_watch:
        lines.append("_없음_")
    else:
        for item in report.videos_to_watch:
            lines.extend(_video_lines(item))
    lines.append("")

    lines.append("## 2. 제출해야 할 과제/설문 (남은 기한 순)")
    lines.append("")
    if not report.pending_submissions:
        lines.append("_없음_")
    else:
        for item in report.pending_submissions:
            lines.append(_task_line_with_dday(item))
    lines.append("")

    lines.append("## 3. 앞으로의 시험/과제 일정")
    lines.append("")
    if not report.upcoming_schedule:
        lines.append("_없음_")
    else:
        for item in report.upcoming_schedule:
            lines.append(_task_line_with_date(item))
    lines.append("")

    lines.append("## 4. 과목별 공지")
    lines.append("")
    if not report.notices_by_course:
        lines.append("_없음_")
    else:
        for course_name, posts in report.notices_by_course.items():
            lines.append(f"### {course_name}")
            lines.append("")
            for p in posts:
                date_str = f"{p.posted_at:%Y-%m-%d}" if p.posted_at else "날짜 미상"
                lines.append(f"- {p.title} *({p.author} · {date_str})*")
            lines.append("")
    return "\n".join(lines)


def _video_lines(item: VideoItem) -> list[str]:
    v = item.video
    week = f"Week {v.week}" if v.week is not None else "주차 미상"
    length = v.length or "-"
    dday = _format_dday(item.days_left)
    head = f"- **{dday}** · {item.course_name} · `{week}` · {v.title} ({length})"
    lines = [head]
    if v.late_until and v.ends_at:
        lines.append(
            f"  - 정상: {v.ends_at:%Y-%m-%d %H:%M} / 지각: {v.late_until:%Y-%m-%d %H:%M}"
        )
    elif v.ends_at:
        lines.append(f"  - 마감: {v.ends_at:%Y-%m-%d %H:%M}")
    elif v.late_until:
        lines.append(f"  - 지각 마감: {v.late_until:%Y-%m-%d %H:%M}")
    return lines


def _task_line_with_dday(item: TaskItem) -> str:
    if item.days_left is None or item.due_at is None:
        return f"- **마감 미정** · [{item.kind}] {item.course_name} · {item.title}"
    dday = _format_dday(item.days_left)
    return (
        f"- **{dday}** · [{item.kind}] {item.course_name} · {item.title} · "
        f"마감 {item.due_at:%Y-%m-%d %H:%M}"
    )


def _task_line_with_date(item: TaskItem) -> str:
    return (
        f"- **{item.due_at:%Y-%m-%d %H:%M}** · [{item.kind}] {item.course_name} · {item.title}"
    )


def _format_dday(days_left: int) -> str:
    if days_left > 0:
        return f"D-{days_left}"
    if days_left == 0:
        return "D-day"
    return f"D+{-days_left}"
