#!/usr/bin/env python3
"""Summarise colcon test results and coverage reports as Markdown.

The script reads what ``colcon test`` leaves in the build directory:

- JUnit files: ``build/<pkg>/pytest.xml`` (ament_python) and
  ``build/<pkg>/test_results/**/*.xml`` (ament_cmake: gtest, pytest, linters);
- Cobertura coverage files: ``build/<pkg>/coverage.xml`` (pytest-cov through
  ``colcon test --pytest-with-coverage``) and ``build/<pkg>/coverage-gcovr.xml``
  (gcovr, C and C++).

It prints a Markdown report (per-package counts, failed tests, coverage) and can
append it to the GitHub job summary, emit error annotations for failed tests,
write counts to ``$GITHUB_OUTPUT`` and copy the raw reports into a directory
for upload as an artifact. Only the standard library is used, so the script
runs in any ROS 2 image.
"""

from __future__ import annotations

import argparse
import os
import shutil
import sys
from dataclasses import dataclass, field
from pathlib import Path
from xml.etree import ElementTree as ET

PYTHON_COVERAGE = "coverage.xml"
CPP_COVERAGE = "coverage-gcovr.xml"
MESSAGE_LENGTH = 200
JUNIT_ROOTS = {"testsuite", "testsuites"}


@dataclass
class TestCase:
    """One test case read from a JUnit file."""

    package: str
    name: str
    outcome: str
    message: str = ""


@dataclass
class PackageResult:
    """Aggregated test results of one package."""

    name: str
    cases: list[TestCase] = field(default_factory=list)

    def count(self, outcome: str) -> int:
        """Return the number of cases with the given outcome."""
        return sum(1 for case in self.cases if case.outcome == outcome)

    @property
    def total(self) -> int:
        """Return the number of test cases."""
        return len(self.cases)

    @property
    def failed(self) -> int:
        """Return the number of failed or errored cases."""
        return self.count("failed") + self.count("error")


@dataclass
class Coverage:
    """Line and branch coverage of one package for one language."""

    package: str
    language: str
    lines_valid: int
    lines_covered: int
    branches_valid: int
    branches_covered: int

    @property
    def line_rate(self) -> float | None:
        """Return the covered line ratio, or None without measurable lines."""
        if self.lines_valid == 0:
            return None
        return self.lines_covered / self.lines_valid

    @property
    def branch_rate(self) -> float | None:
        """Return the covered branch ratio, or None without measured branches."""
        if self.branches_valid == 0:
            return None
        return self.branches_covered / self.branches_valid


def _first_line(text: str | None) -> str:
    """Return the first non-empty line of a message, shortened."""
    for line in (text or "").splitlines():
        stripped = line.strip()
        if stripped:
            if len(stripped) > MESSAGE_LENGTH:
                return stripped[: MESSAGE_LENGTH - 1] + "…"
            return stripped
    return ""


def _case_outcome(element: ET.Element) -> tuple[str, str]:
    """Return the outcome of a ``testcase`` element and its message."""
    for tag, outcome in (("failure", "failed"), ("error", "error"), ("skipped", "skipped")):
        child = element.find(tag)
        if child is not None:
            return outcome, _first_line(child.get("message") or child.text)
    return "passed", ""


def parse_junit(path: Path, package: str) -> list[TestCase] | None:
    """Parse a JUnit file into test cases, or return None if it is not JUnit."""
    try:
        root = ET.parse(path).getroot()  # noqa: S314 - local files written by the build
    except ET.ParseError:
        return None
    if root.tag not in JUNIT_ROOTS:
        return None
    cases = []
    for element in root.iter("testcase"):
        classname = element.get("classname", "")
        name = element.get("name", "")
        full_name = f"{classname}.{name}" if classname else name
        outcome, message = _case_outcome(element)
        cases.append(TestCase(package, full_name, outcome, message))
    return cases


def junit_files(package_dir: Path) -> list[Path]:
    """Return the JUnit files colcon leaves in a package build directory."""
    files = []
    pytest_file = package_dir / "pytest.xml"
    if pytest_file.is_file():
        files.append(pytest_file)
    results_dir = package_dir / "test_results"
    if results_dir.is_dir():
        files.extend(sorted(results_dir.rglob("*.xml")))
    return files


def parse_coverage(path: Path, package: str, language: str) -> Coverage | None:
    """Parse a Cobertura file, or return None if it is not Cobertura."""
    try:
        root = ET.parse(path).getroot()  # noqa: S314 - local files written by the build
    except ET.ParseError:
        return None
    if root.tag != "coverage":
        return None

    def number(attribute: str) -> int:
        try:
            return int(float(root.get(attribute, "0")))
        except ValueError:
            return 0

    return Coverage(
        package=package,
        language=language,
        lines_valid=number("lines-valid"),
        lines_covered=number("lines-covered"),
        branches_valid=number("branches-valid"),
        branches_covered=number("branches-covered"),
    )


def package_dirs(build_base: Path) -> list[Path]:
    """Return the package build directories, sorted by name."""
    if not build_base.is_dir():
        return []
    return sorted(path for path in build_base.iterdir() if path.is_dir())


def collect(build_base: Path) -> tuple[list[PackageResult], list[Coverage]]:
    """Collect test results and coverage of every package in the build base."""
    results = []
    coverages = []
    for package_dir in package_dirs(build_base):
        package = package_dir.name
        result = PackageResult(package)
        for path in junit_files(package_dir):
            cases = parse_junit(path, package)
            if cases is not None:
                result.cases.extend(cases)
        if result.cases:
            results.append(result)
        for filename, language in ((PYTHON_COVERAGE, "Python"), (CPP_COVERAGE, "C/C++")):
            path = package_dir / filename
            if path.is_file():
                coverage = parse_coverage(path, package, language)
                if coverage is not None:
                    coverages.append(coverage)
    return results, coverages


def _plural(count: int, word: str) -> str:
    return f"{count} {word}" if count == 1 else f"{count} {word}s"


def _percent(rate: float | None) -> str:
    return "n/a" if rate is None else f"{rate * 100:.1f} %"


def _escape_cell(text: str) -> str:
    return text.replace("|", "\\|").replace("\n", " ")


def render_markdown(
    title: str,
    results: list[PackageResult],
    coverages: list[Coverage],
) -> str:
    """Render the report as GitHub-flavoured Markdown."""
    lines = [f"## {title}", ""]
    total = sum(result.total for result in results)
    failed = sum(result.failed for result in results)
    skipped = sum(result.count("skipped") for result in results)
    passed = sum(result.count("passed") for result in results)

    if not results:
        lines += [":warning: Aucun résultat de test trouvé.", ""]
    else:
        icon = ":x:" if failed else ":white_check_mark:"
        lines += [
            (
                f"{icon} {passed} réussis, {failed} en échec, {skipped} ignorés "
                f"sur {_plural(total, 'test')} dans {_plural(len(results), 'paquet')}."
            ),
            "",
            "| Paquet | Tests | Réussis | En échec | Ignorés |",
            "| ------ | ----: | ------: | -------: | ------: |",
        ]
        lines += [
            f"| `{result.name}` | {result.total} | {result.count('passed')} "
            f"| {result.failed} | {result.count('skipped')} |"
            for result in results
        ]
        lines += [f"| **Total** | {total} | {passed} | {failed} | {skipped} |", ""]

    failures = [case for result in results for case in result.cases if case.outcome in {"failed", "error"}]
    if failures:
        lines += ["### Tests en échec", "", "| Paquet | Test | Message |", "| ------ | ---- | ------- |"]
        lines += [
            f"| `{case.package}` | `{_escape_cell(case.name)}` | {_escape_cell(case.message)} |"
            for case in failures
        ]
        lines.append("")

    if coverages:
        lines += [
            "### Couverture",
            "",
            "| Paquet | Langage | Lignes | Couverture | Branches |",
            "| ------ | ------- | -----: | ---------: | -------: |",
        ]
        lines += [
            f"| `{cov.package}` | {cov.language} | {cov.lines_covered}/{cov.lines_valid} "
            f"| {_percent(cov.line_rate)} | {_percent(cov.branch_rate)} |"
            for cov in coverages
        ]
        lines.append("")
    return "\n".join(lines)


def _escape_data(text: str) -> str:
    return text.replace("%", "%25").replace("\r", "%0D").replace("\n", "%0A")


def _escape_property(text: str) -> str:
    return _escape_data(text).replace(":", "%3A").replace(",", "%2C")


def annotations(results: list[PackageResult]) -> list[str]:
    """Return GitHub ``::error`` workflow commands, one per failed test."""
    commands = []
    for result in results:
        for case in result.cases:
            if case.outcome in {"failed", "error"}:
                title = _escape_property(f"{case.package}: {case.name}")
                message = _escape_data(case.message or "test failed")
                commands.append(f"::error title={title}::{message}")
    return commands


def copy_reports(build_base: Path, destination: Path) -> int:
    """Copy JUnit and coverage files into ``destination/<pkg>/``; return the file count."""
    copied = 0
    for package_dir in package_dirs(build_base):
        files = junit_files(package_dir)
        files += [package_dir / name for name in (PYTHON_COVERAGE, CPP_COVERAGE)]
        for path in files:
            if not path.is_file():
                continue
            target = destination / package_dir.name / path.relative_to(package_dir)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, target)
            copied += 1
    return copied


def _append(path: str | None, text: str) -> None:
    if path:
        with Path(path).open("a", encoding="utf-8") as stream:
            stream.write(text)


def main(argv: list[str] | None = None) -> int:
    """Entry point."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--build-base", type=Path, default=Path("build"), help="colcon build base")
    parser.add_argument("--title", default="Tests ROS 2", help="title of the Markdown report")
    parser.add_argument("--output", type=Path, help="write the Markdown report to this file")
    parser.add_argument("--collect", type=Path, help="copy JUnit and coverage files into this directory")
    parser.add_argument(
        "--github",
        action="store_true",
        help="append to $GITHUB_STEP_SUMMARY, write $GITHUB_OUTPUT and print error annotations",
    )
    args = parser.parse_args(argv)

    results, coverages = collect(args.build_base)
    report = render_markdown(args.title, results, coverages)
    print(report)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(report + "\n", encoding="utf-8")
    if args.collect:
        count = copy_reports(args.build_base, args.collect)
        print(f"Copied {count} report files to {args.collect}", file=sys.stderr)
    if args.github:
        _append(os.environ.get("GITHUB_STEP_SUMMARY"), report + "\n")
        for command in annotations(results):
            print(command)
        total = sum(result.total for result in results)
        failed = sum(result.failed for result in results)
        skipped = sum(result.count("skipped") for result in results)
        _append(os.environ.get("GITHUB_OUTPUT"), f"tests={total}\nfailures={failed}\nskipped={skipped}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
