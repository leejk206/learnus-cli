import re
import sys
import time
from datetime import datetime

from bs4 import BeautifulSoup

from learnus.models import NoticePost

_POST_GAP = 0.3


def parse_notices(course_html: str, session) -> list[NoticePost]:
    board_url = _find_notice_board_url(course_html)
    if not board_url:
        return []
    try:
        list_html = session.get(board_url, timeout=15).text
    except Exception as e:
        print(f"[WARN] 공지 게시판 GET 실패: {e}", file=sys.stderr)
        return []

    post_rows = _extract_post_rows(list_html)
    results: list[NoticePost] = []
    for title, url, author_fallback, date_fallback in post_rows:
        try:
            resp = session.get(url, timeout=15)
            body_title, author, posted_at, body = _parse_post(resp.text)
        except Exception as e:
            print(f"[WARN] 공지 본문 가져오기 실패 ({title}): {e}", file=sys.stderr)
            results.append(NoticePost(
                title=title, author=author_fallback,
                posted_at=_parse_list_date(date_fallback),
                body="", url=url,
            ))
            time.sleep(_POST_GAP)
            continue
        results.append(NoticePost(
            title=body_title or title,
            author=author or author_fallback,
            posted_at=posted_at or _parse_list_date(date_fallback),
            body=body,
            url=url,
        ))
        time.sleep(_POST_GAP)
    return results


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
        if "공지" in title:
            return (link.get("href") or "").strip() or None
    return None


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


def _parse_post(html: str) -> tuple[str, str, datetime | None, str]:
    soup = BeautifulSoup(html, "lxml")
    view = soup.select_one("div.ubboard_view")
    if not view:
        return "", "", None, ""
    title_el = view.select_one("div.subject h3")
    title = title_el.get_text(strip=True) if title_el else ""
    writer_el = view.select_one("div.info div.writer")
    author = ""
    if writer_el:
        text = writer_el.get_text(" ", strip=True)
        author = text.split(":", 1)[-1].strip() if ":" in text else text
    date_el = view.select_one("div.info div.date")
    posted_at = None
    if date_el:
        text = date_el.get_text(" ", strip=True)
        m = re.search(r"(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2})", text)
        if m:
            try:
                posted_at = datetime.strptime(m.group(1), "%Y-%m-%d %H:%M")
            except ValueError:
                posted_at = None
    content_el = view.select_one("div.content div.text_to_html") or view.select_one("div.content")
    body = content_el.get_text("\n", strip=True) if content_el else ""
    return title, author, posted_at, body


def _parse_list_date(text: str) -> datetime | None:
    text = (text or "").strip()
    for fmt in ("%Y-%m-%d %H:%M", "%Y-%m-%d"):
        try:
            return datetime.strptime(text, fmt)
        except ValueError:
            continue
    return None
