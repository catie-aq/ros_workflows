#!/usr/bin/env python3
"""Export the variables of a JSON object to the following steps of a GitHub job.

Used when a job may run without a container (``container.env`` unavailable):
the caller's ``container-env`` input, a JSON object of strings, is appended to
``$GITHUB_ENV``. Values spanning several lines use the heredoc syntax of
``GITHUB_ENV``.
"""

from __future__ import annotations

import json
import os
import re
import sys
import uuid
from pathlib import Path

NAME = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def parse(text: str) -> dict[str, str]:
    """Parse and validate a JSON object of environment variables."""
    data = json.loads(text or "{}")
    if not isinstance(data, dict):
        msg = "expected a JSON object"
        raise TypeError(msg)
    variables = {}
    for name, value in data.items():
        if not NAME.match(name):
            msg = f"invalid variable name: {name!r}"
            raise ValueError(msg)
        if isinstance(value, bool):
            value = "true" if value else "false"  # noqa: PLW2901
        if not isinstance(value, (str, int, float)):
            msg = f"value of {name} must be a string or a number"
            raise TypeError(msg)
        variables[name] = str(value)
    return variables


def render(variables: dict[str, str]) -> str:
    """Render variables in the ``GITHUB_ENV`` file format."""
    lines = []
    for name, value in variables.items():
        if "\n" in value:
            delimiter = f"EOF_{uuid.uuid4().hex}"
            lines += [f"{name}<<{delimiter}", value, delimiter]
        else:
            lines.append(f"{name}={value}")
    return "".join(line + "\n" for line in lines)


def main(argv: list[str] | None = None) -> int:
    """Entry point: ``export_env.py '<json object>'``."""
    args = sys.argv[1:] if argv is None else argv
    try:
        variables = parse(args[0] if args else "{}")
    except (json.JSONDecodeError, TypeError, ValueError) as error:
        print(f"container-env: {error}", file=sys.stderr)
        return 1
    target = os.environ.get("GITHUB_ENV")
    text = render(variables)
    if target:
        with Path(target).open("a", encoding="utf-8") as stream:
            stream.write(text)
    else:
        sys.stdout.write(text)
    print(f"Exported: {', '.join(variables) or 'nothing'}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
