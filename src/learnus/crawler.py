import sys
import time

import requests

from learnus.auth import LEARNUS_BASE
from learnus.models import Course
from learnus.parsers.assignment import parse_assignments
from learnus.parsers.course_list import parse_course_list
from learnus.parsers.feedback import parse_feedbacks
from learnus.parsers.material import parse_materials
from learnus.parsers.notice import parse_notices
from learnus.parsers.quiz import parse_quizzes
from learnus.parsers.video import parse_videos

RATE_LIMIT_SEC = 0.3


def fetch_course_list(session: requests.Session) -> list[Course]:
    resp = session.get(LEARNUS_BASE + "/")
    return parse_course_list(resp.text)


def fetch_all(session: requests.Session) -> list[Course]:
    courses = fetch_course_list(session)
    for course in courses:
        try:
            resp = session.get(course.url)
            html = resp.text
        except Exception as e:
            print(f"[WARN] {course.name}: 강좌 페이지 요청 실패: {e}", file=sys.stderr)
            continue

        course.assignments = _safe(parse_assignments, course.name, "과제", html, session)
        course.videos     = _safe_noarg(parse_videos,     course.name, "강의", html)
        course.feedbacks  = _safe_noarg(parse_feedbacks,  course.name, "설문", html)
        course.materials  = _safe_noarg(parse_materials,  course.name, "자료", html)
        course.quizzes    = _safe(parse_quizzes,          course.name, "퀴즈", html, session)
        course.notices    = _safe(parse_notices,          course.name, "공지", html, session)

        time.sleep(RATE_LIMIT_SEC)
    return courses


def _safe(fn, course_name: str, area: str, html: str, session):
    try:
        return fn(html, session)
    except Exception as e:
        print(f"[WARN] {course_name}/{area} 파싱 실패: {e}", file=sys.stderr)
        return []


def _safe_noarg(fn, course_name: str, area: str, html: str):
    try:
        return fn(html)
    except Exception as e:
        print(f"[WARN] {course_name}/{area} 파싱 실패: {e}", file=sys.stderr)
        return []
