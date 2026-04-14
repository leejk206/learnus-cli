from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Assignment:
    title: str
    due_at: datetime | None
    submitted: bool
    url: str


@dataclass
class Video:
    title: str
    week: int | None
    starts_at: datetime | None
    ends_at: datetime | None
    late_until: datetime | None
    watched: bool
    length: str | None
    url: str


@dataclass
class Feedback:
    title: str
    opens_at: datetime | None
    closes_at: datetime | None
    submitted: bool
    url: str


@dataclass
class Material:
    title: str
    week: int | None
    posted_at: datetime | None
    kind: str
    url: str


@dataclass
class Quiz:
    title: str
    opens_at: datetime | None
    closes_at: datetime | None
    url: str


@dataclass
class NoticePost:
    title: str
    author: str
    posted_at: datetime | None
    body: str
    url: str


@dataclass
class Course:
    id: str
    name: str
    url: str
    assignments: list[Assignment] = field(default_factory=list)
    videos: list[Video] = field(default_factory=list)
    feedbacks: list[Feedback] = field(default_factory=list)
    materials: list[Material] = field(default_factory=list)
    quizzes: list[Quiz] = field(default_factory=list)
    notices: list[NoticePost] = field(default_factory=list)
