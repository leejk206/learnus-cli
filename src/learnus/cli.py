import os
import traceback
from datetime import datetime
from pathlib import Path

import typer
from dotenv import load_dotenv

from learnus.auth import LoginError, login
from learnus.crawler import fetch_all
from learnus.render import render_courses, render_json, render_upcoming

app = typer.Typer(add_completion=False, help="LearnUs crawler CLI")


@app.command()
def main(
    upcoming: bool = typer.Option(False, "--upcoming", help="마감 예정 과제/퀴즈만 flat 출력"),
    course: str = typer.Option("", "--course", help="강좌명 부분일치 필터"),
    json_output: bool = typer.Option(False, "--json", help="JSON 덤프"),
    debug: bool = typer.Option(False, "--debug", help="에러 시 traceback + HTML 덤프"),
) -> None:
    load_dotenv()
    user_id = os.getenv("YONSEI_ID", "")
    password = os.getenv("YONSEI_PW", "")

    if not user_id or not password:
        typer.echo("[ERROR] YONSEI_ID / YONSEI_PW가 .env에 없습니다.", err=True)
        raise typer.Exit(code=2)

    try:
        session = login(user_id, password)
    except LoginError as e:
        typer.echo(f"[ERROR] 로그인 실패: {e}", err=True)
        if debug:
            traceback.print_exc()
        raise typer.Exit(code=1)

    try:
        courses = fetch_all(session)
    except Exception as e:
        typer.echo(f"[ERROR] 크롤링 실패: {e}", err=True)
        if debug:
            traceback.print_exc()
            _dump_debug_html("crawl_failure", "<no-html>")
        raise typer.Exit(code=1)

    if course:
        courses = [c for c in courses if course in c.name]

    if json_output:
        render_json(courses)
    elif upcoming:
        render_upcoming(courses)
    else:
        render_courses(courses)


def _dump_debug_html(tag: str, html: str) -> None:
    path = Path(f"/tmp/learnus-debug-{tag}-{datetime.now().strftime('%Y%m%d-%H%M%S')}.html")
    path.write_text(html, encoding="utf-8")
    typer.echo(f"[DEBUG] HTML dumped to {path}", err=True)


if __name__ == "__main__":
    app()
