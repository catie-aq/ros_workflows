#!/usr/bin/env python3
"""Write a rosdep YAML file that maps workspace packages to their Debian names.

``bloom-generate rosdebian`` resolves every dependency through rosdep. Packages
of the workspace are not in the public rosdep database, so a package that
depends on another one of the workspace cannot be packaged without this
mapping: ``<name>`` resolves to ``ros-<distro>-<name with dashes>``, the name
bloom gives to the Debian package it generates.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from xml.etree import ElementTree as ET


def package_name(package_xml: Path) -> str:
    """Return the name declared in a package.xml."""
    root = ET.parse(package_xml).getroot()  # noqa: S314 - workspace files
    name = root.findtext("name")
    if not name or not name.strip():
        msg = f"{package_xml}: missing <name>"
        raise ValueError(msg)
    return name.strip()


def debian_name(package: str, distro: str) -> str:
    """Return the Debian package name bloom generates for a ROS package."""
    return f"ros-{distro}-{package.replace('_', '-')}"


def render_yaml(packages: list[str], distro: str, os_name: str) -> str:
    """Render the rosdep YAML mapping for ``packages``."""
    lines = []
    for package in sorted(set(packages)):
        lines += [f"{package}:", f"  {os_name}: [{debian_name(package, distro)}]"]
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    """Entry point."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("paths", nargs="+", type=Path, help="package directories")
    parser.add_argument("--distro", required=True, help="ROS distribution, for example jazzy")
    parser.add_argument("--os-name", default="ubuntu", help="rosdep OS name")
    parser.add_argument("--output", type=Path, required=True, help="YAML file to write")
    args = parser.parse_args(argv)

    names = [package_name(path / "package.xml") for path in args.paths]
    args.output.write_text(render_yaml(names, args.distro, args.os_name), encoding="utf-8")
    print(f"{len(names)} workspace packages mapped in {args.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
