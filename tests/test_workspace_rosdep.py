"""Tests of scripts/workspace_rosdep.py on the sample workspace."""

from __future__ import annotations

from pathlib import Path

import pytest
import workspace_rosdep

SRC = Path(__file__).parent / "fixtures" / "ros_ws" / "src"


def test_package_name() -> None:
    assert workspace_rosdep.package_name(SRC / "sample_pkg" / "package.xml") == "sample_pkg"


def test_package_name_missing(tmp_path: Path) -> None:
    package_xml = tmp_path / "package.xml"
    package_xml.write_text('<package format="3"><version>1.0.0</version></package>', encoding="utf-8")
    with pytest.raises(ValueError, match="missing <name>"):
        workspace_rosdep.package_name(package_xml)


def test_debian_name() -> None:
    assert workspace_rosdep.debian_name("minipock_msgs", "jazzy") == "ros-jazzy-minipock-msgs"


def test_render_yaml_sorted_and_unique() -> None:
    text = workspace_rosdep.render_yaml(["b_pkg", "a_pkg", "b_pkg"], "humble", "ubuntu")
    assert text == "a_pkg:\n  ubuntu: [ros-humble-a-pkg]\nb_pkg:\n  ubuntu: [ros-humble-b-pkg]\n"


def test_main(tmp_path: Path) -> None:
    output = tmp_path / "workspace.yaml"
    paths = [str(SRC / "sample_pkg"), str(SRC / "sample_cpp_pkg")]
    assert workspace_rosdep.main([*paths, "--distro", "jazzy", "--output", str(output)]) == 0
    assert output.read_text(encoding="utf-8") == (
        "sample_cpp_pkg:\n  ubuntu: [ros-jazzy-sample-cpp-pkg]\n"
        "sample_pkg:\n  ubuntu: [ros-jazzy-sample-pkg]\n"
    )
