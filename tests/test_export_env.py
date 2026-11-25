"""Tests of scripts/export_env.py."""

from __future__ import annotations

from typing import TYPE_CHECKING

import export_env
import pytest

if TYPE_CHECKING:
    from pathlib import Path


def test_parse_strings_numbers_and_booleans() -> None:
    assert export_env.parse('{"LIBGL_ALWAYS_SOFTWARE": "1", "ROS_DOMAIN_ID": 42, "FLAG": true}') == {
        "LIBGL_ALWAYS_SOFTWARE": "1",
        "ROS_DOMAIN_ID": "42",
        "FLAG": "true",
    }


def test_parse_empty() -> None:
    assert export_env.parse("") == {}
    assert export_env.parse("{}") == {}


@pytest.mark.parametrize(
    ("text", "error"),
    [("[]", TypeError), ('{"1BAD": "x"}', ValueError), ('{"A": {"b": 1}}', TypeError)],
)
def test_parse_rejects(text: str, error: type[Exception]) -> None:
    with pytest.raises(error):
        export_env.parse(text)


def test_render_multiline_uses_heredoc() -> None:
    text = export_env.render({"A": "1", "B": "line1\nline2"})
    lines = text.splitlines()
    assert lines[0] == "A=1"
    assert lines[1].startswith("B<<EOF_")
    assert lines[2:4] == ["line1", "line2"]
    assert lines[4] == lines[1].split("<<", 1)[1]


def test_main_appends_to_github_env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    target = tmp_path / "env"
    target.write_text("EXISTING=1\n", encoding="utf-8")
    monkeypatch.setenv("GITHUB_ENV", str(target))
    assert export_env.main(['{"ROS_DOMAIN_ID": "7"}']) == 0
    assert target.read_text(encoding="utf-8") == "EXISTING=1\nROS_DOMAIN_ID=7\n"


def test_main_invalid_json(capsys) -> None:
    assert export_env.main(["{not json"]) == 1
    assert "container-env:" in capsys.readouterr().err
