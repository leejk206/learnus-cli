from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Assignment:
    title: str
    due_at: datetime | None
    submitted: bool
    url: str


@dataclass
class Notice:
    title: str
    posted_at: datetime | None
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
class Course:
    id: str
    name: str
    url: str
    assignments: list[Assignment] = field(default_factory=list)
    notices: list[Notice] = field(default_factory=list)
    materials: list[Material] = field(default_factory=list)
    quizzes: list[Quiz] = field(default_factory=list)
