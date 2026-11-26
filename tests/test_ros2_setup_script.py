"""Run scripts/ros2_setup.sh with fake ROS tools and check what rosdep receives.

rosdep must only see the packages colcon discovers: given a source tree, it
reads every package.xml, including those of ignored trees (COLCON_IGNORE) and
test fixtures, and fails on the first invalid one. The real behaviour of colcon
on COLCON_IGNORE is exercised by the self-test, whose workspace contains
tests/fixtures/ros_ws/src/ignored/broken_pkg.
"""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).parent.parent
SCRIPT = ROOT / "scripts" / "ros2_setup.sh"
BASH = shutil.which("bash") or "/bin/bash"

STUBS = {
    # colcon list prints the paths given in FAKE_COLCON_PATHS, one per line.
    "colcon": """#!/usr/bin/env bash
echo "colcon $*" >> "${FAKE_LOG}"
if [ "$1" = list ] && [ -n "${FAKE_COLCON_PATHS}" ]; then
  tr ':' '\\n' <<<"${FAKE_COLCON_PATHS}"
fi
""",
    "rosdep": """#!/usr/bin/env bash
echo "rosdep $*" >> "${FAKE_LOG}"
""",
    "sudo": """#!/usr/bin/env bash
[ "$1" = -E ] && shift
exec "$@"
""",
    "apt-get": "#!/usr/bin/env bash\nexit 0\n",
    "tee": "#!/usr/bin/env bash\ncat >/dev/null\n",
    "git": "#!/usr/bin/env bash\nexit 0\n",
}


@pytest.fixture
def sandbox(tmp_path: Path) -> dict:
    ros_root = tmp_path / "ros"
    (ros_root / "jazzy").mkdir(parents=True)
    (ros_root / "jazzy" / "setup.bash").write_text("", encoding="utf-8")
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    for name, text in STUBS.items():
        stub = bin_dir / name
        stub.write_text(text, encoding="utf-8")
        stub.chmod(0o755)
    repo = tmp_path / "repo"
    (repo / "ws" / "src").mkdir(parents=True)
    (tmp_path / "home").mkdir()
    env = {key: value for key, value in os.environ.items() if not key.startswith("GITHUB_")}
    env.update(
        {
            "PATH": f"{bin_dir}{os.pathsep}{env['PATH']}",
            "HOME": str(tmp_path / "home"),
            "TMPDIR": str(tmp_path),
            "ROS_INSTALL_ROOT": str(ros_root),
            "DISTRIBUTION": "jazzy",
            "WORKSPACE": "ws",
            "FAKE_LOG": str(tmp_path / "calls.log"),
            "FAKE_COLCON_PATHS": "ws/src/repo/pkg_a:ws/src/repo/sub/pkg_b",
        }
    )
    return {"repo": repo, "env": env, "log": tmp_path / "calls.log"}


def run(sandbox: dict, **variables: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(  # noqa: S603 - fixed script path
        [BASH, str(SCRIPT)],
        cwd=sandbox["repo"],
        env={**sandbox["env"], **variables},
        capture_output=True,
        text=True,
        check=False,
    )


def calls(sandbox: dict, tool: str, subcommand: str) -> list[str]:
    lines = sandbox["log"].read_text(encoding="utf-8").splitlines()
    return [line for line in lines if line.startswith(f"{tool} {subcommand}")]


def test_rosdep_gets_the_paths_colcon_discovers(sandbox: dict) -> None:
    result = run(sandbox)
    assert result.returncode == 0, result.stderr
    assert calls(sandbox, "colcon", "list") == ["colcon list --base-paths ws/src --paths-only"]
    for subcommand in ("install", "check"):
        (line,) = calls(sandbox, "rosdep", subcommand)
        assert "--from-paths ws/src/repo/pkg_a ws/src/repo/sub/pkg_b --ignore-src" in line
        assert "--from-paths ws/src " not in line


def test_package_selection_is_passed_to_colcon(sandbox: dict) -> None:
    result = run(sandbox, PACKAGES="pkg_b  pkg_a", ROSDEP_CHECK="false")
    assert result.returncode == 0, result.stderr
    assert calls(sandbox, "colcon", "list") == [
        "colcon list --base-paths ws/src --paths-only --packages-up-to pkg_b pkg_a"
    ]
    assert calls(sandbox, "rosdep", "check") == []


def test_no_package_fails_before_rosdep(sandbox: dict) -> None:
    result = run(sandbox, FAKE_COLCON_PATHS="")
    assert result.returncode == 1
    assert "No ROS package found under ws/src." in result.stderr
    assert calls(sandbox, "rosdep", "install") == []
