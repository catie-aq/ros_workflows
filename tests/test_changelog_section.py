"""Tests of scripts/changelog_section.py."""

from __future__ import annotations

from pathlib import Path

import changelog_section as changelog
import pytest

CHANGELOG = Path(__file__).parent / "fixtures" / "changelog" / "CHANGELOG.md"
TEXT = CHANGELOG.read_text(encoding="utf-8")


def test_bracket_heading_with_link_and_date() -> None:
    section = changelog.extract_section(TEXT, "2.3.0")
    assert section == (
        "Refactor up to Nav2 in simulation.\n\n### Changed\n\n- Single `map_server` for the fleet"
    )


@pytest.mark.parametrize("version", ["2.2.1", "v2.2.1"])
def test_v_prefix(version: str) -> None:
    assert changelog.extract_section(TEXT, version) == "### Fixed\n\n- Lidar frame renamed"


def test_last_section_runs_to_end_of_file() -> None:
    assert changelog.extract_section(TEXT, "2.2.0") == "First listed version."


def test_version_prefix_does_not_match_longer_version() -> None:
    # 2.3 must not match the 2.3.0 heading.
    assert changelog.extract_section(TEXT, "2.3") is None


def test_missing_version() -> None:
    assert changelog.extract_section(TEXT, "9.9.9") is None


def test_main_writes_output(tmp_path: Path) -> None:
    output = tmp_path / "notes.md"
    assert changelog.main([str(CHANGELOG), "2.2.0", "--output", str(output)]) == 0
    assert output.read_text(encoding="utf-8") == "First listed version.\n"


def test_main_missing_version_fails(capsys) -> None:
    assert changelog.main([str(CHANGELOG), "9.9.9"]) == 1
    assert "no section for version 9.9.9" in capsys.readouterr().err


def test_main_missing_file_fails(tmp_path: Path) -> None:
    assert changelog.main([str(tmp_path / "nope.md"), "1.0.0"]) == 1
