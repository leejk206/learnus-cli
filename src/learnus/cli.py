import os
import traceback
from datetime import datetime
from pathlib import Path

import typer
from dotenv import load_dotenv

from learnus.auth import LoginError, login
from learnus.crawler import fetch_all
from learnus.md_writer import render_summary_markdown
from learnus.render import (
    render_courses,
    render_json,
    render_summary_terminal,
    render_upcoming,
)
from learnus.summary import build_summary

app = typer.Typer(add_completion=False, help="LearnUs crawler CLI")


@app.command()
def main(
    upcoming: bool = typer.Option(False, "--upcoming", help="마감 예정 과제/퀴즈만 flat 출력"),
    course: str = typer.Option("", "--course", help="강좌명 부분일치 필터"),
    json_output: bool = typer.Option(False, "--json", help="JSON 덤프"),
    summary: bool = typer.Option(False, "--summary", help="4섹션 요약 + MD 저장"),
    debug: bool = typer.Option(False, "--debug", help="에러 시 traceback"),
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
        raise typer.Exit(code=1)

    if summary:
        now = datetime.now()
        report = build_summary(courses, now)
        render_summary_terminal(report)
        md = render_summary_markdown(report)
        out_dir = _reports_dir()
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / f"{now:%Y%m%d}.md"
        try:
            out_path.write_text(md, encoding="utf-8")
        except OSError as e:
            typer.echo(f"[ERROR] MD 저장 실패: {e}", err=True)
            raise typer.Exit(code=1)
        typer.echo(f"[INFO] 저장됨: {out_path}", err=True)
        return

    if course:
        courses = [c for c in courses if course in c.name]

    if json_output:
        render_json(courses)
    elif upcoming:
        render_upcoming(courses)
    else:
        render_courses(courses)


def _reports_dir() -> Path:
    return Path(__file__).resolve().parents[2] / "reports"


if __name__ == "__main__":
    app()
