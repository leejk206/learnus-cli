from bs4 import BeautifulSoup

from learnus.models import Quiz


def parse_quizzes(course_html: str) -> list[Quiz]:
    soup = BeautifulSoup(course_html, "lxml")
    results: list[Quiz] = []
    for li in soup.select("li.activity.quiz"):
        link = li.select_one("div.activityinstance a")
        if not link:
            continue
        url = link.get("href", "").strip()
        name_span = link.select_one("span.instancename")
        if not name_span:
            continue
        accesshide = name_span.select_one("span.accesshide")
        if accesshide:
            accesshide.extract()
        title = name_span.get_text(strip=True)
        results.append(Quiz(title=title, opens_at=None, closes_at=None, url=url))
    return results
