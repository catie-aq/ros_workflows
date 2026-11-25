#!/usr/bin/env python3
"""Extract the section of one version from a Keep a Changelog style file.

A version section starts with a level-2 heading naming the version, with or
without brackets, link or ``v`` prefix (``## [2.3.0](url) - date``,
``## v2.3.0``, ``## 2.3.0``), and ends at the next level-2 heading. The body,
without its heading, is printed or written to ``--output``; it becomes the body
of the GitHub release. Exit code 1 when the version is not found.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


def heading_pattern(version: str) -> re.Pattern[str]:
    """Return the pattern of a level-2 heading for ``version``."""
    escaped = re.escape(version.removeprefix("v"))
    return re.compile(rf"^##\s+\[?v?{escaped}(?:\]|\s|$)")


def extract_section(text: str, version: str) -> str | None:
    """Return the body of the section of ``version``, or None if absent."""
    pattern = heading_pattern(version)
    lines = text.splitlines()
    start = next((index for index, line in enumerate(lines) if pattern.match(line)), None)
    if start is None:
        return None
    body = []
    for line in lines[start + 1 :]:
        if re.match(r"^##\s", line):
            break
        body.append(line)
    return "\n".join(body).strip("\n")


def main(argv: list[str] | None = None) -> int:
    """Entry point."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("changelog", type=Path, help="path of the changelog")
    parser.add_argument("version", help="version to extract, for example 2.3.0")
    parser.add_argument("--output", type=Path, help="write the section to this file")
    args = parser.parse_args(argv)

    if not args.changelog.is_file():
        print(f"{args.changelog}: no such file", file=sys.stderr)
        return 1
    section = extract_section(args.changelog.read_text(encoding="utf-8"), args.version)
    if section is None:
        print(f"{args.changelog}: no section for version {args.version}", file=sys.stderr)
        return 1
    if args.output:
        args.output.write_text(section + "\n", encoding="utf-8")
    else:
        print(section)
    return 0


if __name__ == "__main__":
    sys.exit(main())
