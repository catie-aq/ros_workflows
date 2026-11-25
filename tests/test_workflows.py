"""Consistency checks between the workflows and the composite actions.

actionlint cannot check the inputs passed to ``./.ros_workflows/<action>``: that
path only exists once the job has checked out this repository. These tests do.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import TYPE_CHECKING

import pytest
import yaml

if TYPE_CHECKING:
    from collections.abc import Iterator

ROOT = Path(__file__).parent.parent
WORKFLOWS = sorted((ROOT / ".github" / "workflows").glob("*.yml"))
ACTIONS = {path.parent.name: path for path in ROOT.glob("*/action.yml")}
LOCAL_ACTION = re.compile(r"^\./\.ros_workflows/(?P<name>[a-z0-9_]+)$")
SCRIPT = re.compile(r"(?:\.ros_workflows/|\$\{GITHUB_ACTION_PATH\}/\.\./)scripts/(?P<name>[A-Za-z0-9_.]+)")


def load(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def local_action_steps() -> Iterator[pytest.param]:
    for workflow in WORKFLOWS:
        for job_name, job in load(workflow)["jobs"].items():
            for step in job.get("steps", []):
                match = LOCAL_ACTION.match(step.get("uses", ""))
                if match:
                    yield pytest.param(
                        match["name"], step.get("with", {}), id=f"{workflow.stem}:{job_name}:{match['name']}"
                    )


@pytest.mark.parametrize(("action", "arguments"), list(local_action_steps()))
def test_local_action_inputs_exist(action: str, arguments: dict) -> None:
    assert action in ACTIONS, f"no {action}/action.yml"
    inputs = load(ACTIONS[action]).get("inputs", {})
    unknown = sorted(set(arguments) - set(inputs))
    assert not unknown, f"unknown inputs of {action}: {unknown}"


@pytest.mark.parametrize("action", sorted(ACTIONS))
def test_action_inputs_have_description_and_string_default(action: str) -> None:
    for name, spec in load(ACTIONS[action]).get("inputs", {}).items():
        assert spec.get("description"), f"{action}.{name} has no description"
        if "default" in spec:
            assert isinstance(spec["default"], str), f"{action}.{name}: default must be a string"


def referenced_scripts() -> Iterator[pytest.param]:
    files = [*WORKFLOWS, *ACTIONS.values()]
    for path in files:
        for match in SCRIPT.finditer(path.read_text(encoding="utf-8")):
            yield pytest.param(match["name"], id=f"{path.parent.name}/{path.name}:{match['name']}")


@pytest.mark.parametrize("script", list(referenced_scripts()))
def test_referenced_scripts_exist_and_are_executable(script: str) -> None:
    path = ROOT / "scripts" / script
    assert path.is_file()
    assert path.stat().st_mode & 0o111, f"{script} is not executable"


def test_every_workflow_and_action_has_a_doc() -> None:
    docs = {path.stem for path in (ROOT / "docs").glob("*.md")}
    expected = {path.stem for path in WORKFLOWS} | set(ACTIONS)
    assert sorted(expected - docs) == []
