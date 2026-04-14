from dataclasses import dataclass, field
from datetime import datetime

from learnus.models import Course, NoticePost, Video


@dataclass
class VideoItem:
    course_name: str
    video: Video
    days_left: int


@dataclass
class TaskItem:
    course_name: str
    kind: str          # "과제" | "퀴즈" | "설문"
    title: str
    due_at: datetime | None
    url: str
    days_left: int | None


@dataclass
class SummaryReport:
    generated_at: datetime
    videos_to_watch: list[VideoItem] = field(default_factory=list)
    pending_submissions: list[TaskItem] = field(default_factory=list)
    upcoming_schedule: list[TaskItem] = field(default_factory=list)
    notices_by_course: dict[str, list[NoticePost]] = field(default_factory=dict)


def build_summary(courses: list[Course], now: datetime) -> SummaryReport:
    report = SummaryReport(generated_at=now)

    for c in courses:
        for v in c.videos:
            if v.watched:
                continue
            deadline = v.late_until or v.ends_at
            if deadline is None or deadline < now:
                continue
            report.videos_to_watch.append(VideoItem(
                course_name=c.name, video=v,
                days_left=(deadline.date() - now.date()).days,
            ))
    report.videos_to_watch.sort(
        key=lambda x: (x.video.late_until or x.video.ends_at or datetime.max)
    )

    for c in courses:
        for a in c.assignments:
            if a.submitted:
                continue
            if a.due_at is None:
                report.pending_submissions.append(TaskItem(
                    course_name=c.name, kind="과제", title=a.title,
                    due_at=None, url=a.url, days_left=None,
                ))
                continue
            if a.due_at < now:
                continue
            report.pending_submissions.append(TaskItem(
                course_name=c.name, kind="과제", title=a.title,
                due_at=a.due_at, url=a.url,
                days_left=(a.due_at.date() - now.date()).days,
            ))
        for f in c.feedbacks:
            if f.submitted:
                continue
            if f.closes_at is None:
                report.pending_submissions.append(TaskItem(
                    course_name=c.name, kind="설문", title=f.title,
                    due_at=None, url=f.url, days_left=None,
                ))
                continue
            if f.closes_at < now:
                continue
            report.pending_submissions.append(TaskItem(
                course_name=c.name, kind="설문", title=f.title,
                due_at=f.closes_at, url=f.url,
                days_left=(f.closes_at.date() - now.date()).days,
            ))
    # Dated items first (by date asc), then undated at the end.
    report.pending_submissions.sort(
        key=lambda x: (x.due_at is None, x.due_at or datetime.max)
    )

    for c in courses:
        for a in c.assignments:
            if a.due_at is None or a.due_at < now:
                continue
            report.upcoming_schedule.append(TaskItem(
                course_name=c.name, kind="과제", title=a.title,
                due_at=a.due_at, url=a.url,
                days_left=(a.due_at.date() - now.date()).days,
            ))
        for q in c.quizzes:
            due = q.closes_at or q.opens_at
            if due is None or due < now:
                continue
            report.upcoming_schedule.append(TaskItem(
                course_name=c.name, kind="퀴즈", title=q.title,
                due_at=due, url=q.url,
                days_left=(due.date() - now.date()).days,
            ))
    report.upcoming_schedule.sort(key=lambda x: x.due_at)

    for c in courses:
        if not c.notices:
            continue
        report.notices_by_course[c.name] = sorted(
            c.notices,
            key=lambda p: p.posted_at or datetime.min,
            reverse=True,
        )

    return report
