import json
from pathlib import Path
from unittest.mock import patch

from typer.testing import CliRunner

from learnus.cli import app
from learnus.models import Assignment, Course

runner = CliRunner()


def _fake_courses():
    return [
        Course(
            id="1", name="자료구조", url="http://x",
            assignments=[Assignment(title="HW1", due_at=None, submitted=False, url="http://x/1")],
        )
    ]


def test_cli_default_runs():
    with patch("learnus.cli.login") as m_login, \
         patch("learnus.cli.fetch_all", return_value=_fake_courses()):
        m_login.return_value = object()
        result = runner.invoke(app, [], env={"YONSEI_ID": "x", "YONSEI_PW": "y"})
    assert result.exit_code == 0
    assert "자료구조" in result.stdout


def test_cli_json_flag_outputs_json():
    with patch("learnus.cli.login") as m_login, \
         patch("learnus.cli.fetch_all", return_value=_fake_courses()):
        m_login.return_value = object()
        result = runner.invoke(app, ["--json"], env={"YONSEI_ID": "x", "YONSEI_PW": "y"})
    assert result.exit_code == 0
    data = json.loads(result.stdout)
    assert data[0]["name"] == "자료구조"


def test_cli_course_filter_narrows_output():
    with patch("learnus.cli.login") as m_login, \
         patch("learnus.cli.fetch_all", return_value=_fake_courses()):
        m_login.return_value = object()
        result = runner.invoke(app, ["--course", "없는과목"],
                                env={"YONSEI_ID": "x", "YONSEI_PW": "y"})
    assert result.exit_code == 0
    assert "자료구조" not in result.stdout


def test_cli_missing_credentials_exits_nonzero():
    result = runner.invoke(app, [], env={"YONSEI_ID": "", "YONSEI_PW": ""})
    assert result.exit_code != 0


def test_cli_summary_writes_md_file(tmp_path, monkeypatch):
    monkeypatch.setattr("learnus.cli._reports_dir", lambda: tmp_path)
    with patch("learnus.cli.login") as m_login, \
         patch("learnus.cli.fetch_all", return_value=_fake_courses()):
        m_login.return_value = object()
        result = runner.invoke(app, ["--summary"],
                                env={"YONSEI_ID": "x", "YONSEI_PW": "y"})
    assert result.exit_code == 0
    md_files = list(tmp_path.glob("*.md"))
    assert len(md_files) == 1
    content = md_files[0].read_text(encoding="utf-8")
    assert "# LearnUs 요약" in content
    assert "## 1. 들어야 할 강의 영상" in content
