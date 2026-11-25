"""Run scripts/colcon_test.sh against a fake ROS installation and a fake colcon.

The fake colcon writes one JUnit file, as ``colcon test`` would, and records its
arguments; the real script then summarises it. This checks the paths the
composite action relies on, without a ROS image.
"""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).parent.parent
SCRIPT = ROOT / "scripts" / "colcon_test.sh"
BASH = shutil.which("bash") or "/bin/bash"

FAKE_COLCON = """#!/usr/bin/env bash
case "$1" in
  test)
    printf '%s\\n' "$@" > "${FAKE_COLCON_ARGS}"
    mkdir -p build/fake_pkg
    echo '<testsuites><testsuite name="pytest"><testcase classname="fake" name="test_ok"/></testsuite>'\
'</testsuites>' > build/fake_pkg/pytest.xml
    ;;
  list | test-result) ;;
esac
"""


@pytest.fixture
def sandbox(tmp_path: Path) -> dict:
    """Fake ROS root, fake colcon on PATH, and a repository directory with a workspace."""
    ros_root = tmp_path / "ros"
    (ros_root / "jazzy").mkdir(parents=True)
    (ros_root / "jazzy" / "setup.bash").write_text("", encoding="utf-8")
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    colcon = bin_dir / "colcon"
    colcon.write_text(FAKE_COLCON, encoding="utf-8")
    colcon.chmod(0o755)
    repo = tmp_path / "repo"
    (repo / "ws" / "install").mkdir(parents=True)
    (repo / "ws" / "install" / "setup.bash").write_text("", encoding="utf-8")
    env = {key: value for key, value in os.environ.items() if not key.startswith("GITHUB_")}
    env.update(
        {
            "PATH": f"{bin_dir}{os.pathsep}{env['PATH']}",
            "ROS_INSTALL_ROOT": str(ros_root),
            "DISTRIBUTION": "jazzy",
            "WORKSPACE": "ws",
            "FAKE_COLCON_ARGS": str(tmp_path / "colcon-args"),
        }
    )
    return {"repo": repo, "env": env, "args": tmp_path / "colcon-args"}


def run(sandbox: dict, **variables: str) -> subprocess.CompletedProcess[str]:
    env = {**sandbox["env"], **variables}
    return subprocess.run(  # noqa: S603 - fixed script path
        [BASH, str(SCRIPT)], cwd=sandbox["repo"], env=env, capture_output=True, text=True, check=False
    )


def test_relative_report_dir_is_relative_to_the_starting_directory(sandbox: dict) -> None:
    # colcon_test/action.yml passes REPORT_DIR=<workspace>/test-reports and uploads that path.
    result = run(sandbox, REPORT_DIR="ws/test-reports")
    assert result.returncode == 0, result.stderr
    reports = sandbox["repo"] / "ws" / "test-reports"
    assert (reports / "summary.md").is_file()
    assert (reports / "fake_pkg" / "pytest.xml").is_file()
    assert not (sandbox["repo"] / "ws" / "ws").exists()


def test_default_report_dir(sandbox: dict) -> None:
    result = run(sandbox)
    assert result.returncode == 0, result.stderr
    assert (sandbox["repo"] / "ws" / "test-reports" / "summary.md").is_file()


def test_pytest_args_are_passed_last_with_dash_prefix(sandbox: dict) -> None:
    result = run(sandbox, PYTEST_ARGS='["-m", "not integration"]')
    assert result.returncode == 0, result.stderr
    args = sandbox["args"].read_text(encoding="utf-8").splitlines()
    assert args[-3:] == ["--pytest-args", " -m", "not integration"]


@pytest.mark.parametrize(
    ("value", "message"),
    [("{not json", "PYTEST_ARGS is not valid JSON"), ('{"m": 1}', "must be a JSON array of strings")],
)
def test_invalid_pytest_args_fail_loudly(sandbox: dict, value: str, message: str) -> None:
    result = run(sandbox, PYTEST_ARGS=value)
    assert result.returncode != 0
    assert message in result.stderr
    assert not sandbox["args"].exists(), "colcon must not run"


def test_invalid_retries(sandbox: dict) -> None:
    result = run(sandbox, RETRIES="two")
    assert result.returncode == 1
    assert "RETRIES must be a non-negative integer, got 'two'" in result.stderr
