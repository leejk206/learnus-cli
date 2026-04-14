import sys
from datetime import datetime

from bs4 import BeautifulSoup

from learnus.models import NoticePost


def parse_notices(course_html: str, session) -> list[NoticePost]:
    board_url = _find_notice_board_url(course_html)
    if not board_url:
        return []
    try:
        list_html = session.get(board_url, timeout=15).text
    except Exception as e:
        print(f"[WARN] 공지 게시판 GET 실패: {e}", file=sys.stderr)
        return []
    return [
        NoticePost(
            title=title,
            author=author,
            posted_at=_parse_list_date(date),
            body="",
            url=url,
        )
        for title, url, author, date in _extract_post_rows(list_html)
    ]


def _find_notice_board_url(course_html: str) -> str | None:
    soup = BeautifulSoup(course_html, "lxml")
    for li in soup.select("li.activity.ubboard"):
        link = li.select_one("div.activityinstance a")
        if not link:
            continue
        name = link.select_one("span.instancename")
        if not name:
            continue
        hide = name.select_one("span.accesshide")
        if hide:
            hide.extract()
        title = name.get_text(strip=True)
        if _is_notice_board(title):
            return (link.get("href") or "").strip() or None
    return None


def _is_notice_board(title: str) -> bool:
    if "공지" in title:
        return True
    t = title.lower()
    if "announcement" in t or "announce" in t:
        return True
    return False


def _extract_post_rows(list_html: str) -> list[tuple[str, str, str, str]]:
    soup = BeautifulSoup(list_html, "lxml")
    table = soup.find("table", class_="ubboard_table")
    if not table:
        return []
    rows: list[tuple[str, str, str, str]] = []
    tbody = table.find("tbody")
    trs = tbody.find_all("tr") if tbody else table.find_all("tr")[1:]
    for tr in trs:
        tds = tr.find_all("td")
        if len(tds) < 4:
            continue
        a = tds[1].find("a")
        if not a:
            continue
        url = (a.get("href") or "").strip()
        title = a.get_text(strip=True)
        author = tds[2].get_text(strip=True)
        date = tds[3].get_text(strip=True)
        if not url or not title:
            continue
        rows.append((title, url, author, date))
    return rows


def _parse_list_date(text: str) -> datetime | None:
    text = (text or "").strip()
    for fmt in ("%Y-%m-%d %H:%M", "%Y-%m-%d"):
        try:
            return datetime.strptime(text, fmt)
        except ValueError:
            continue
    return None
