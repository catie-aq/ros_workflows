"""Tests of scripts/ros2_ci_report.py on recorded colcon build trees."""

from __future__ import annotations

from pathlib import Path

import pytest
import ros2_ci_report as report

BUILD = Path(__file__).parent / "fixtures" / "build"


@pytest.fixture
def collected() -> tuple[list[report.PackageResult], list[report.Coverage]]:
    return report.collect(BUILD)


def test_collect_keeps_packages_with_results(collected) -> None:
    results, _ = collected
    assert [result.name for result in results] == ["cpp_pkg", "py_pkg"]


def test_python_counts(collected) -> None:
    results, _ = collected
    py_pkg = next(result for result in results if result.name == "py_pkg")
    assert py_pkg.total == 4
    assert py_pkg.count("passed") == 2
    assert py_pkg.failed == 1
    assert py_pkg.count("skipped") == 1


def test_cpp_counts_gtest_and_linter_errors(collected) -> None:
    results, _ = collected
    cpp_pkg = next(result for result in results if result.name == "cpp_pkg")
    # 3 gtest cases + 1 linter error; broken.xml is ignored.
    assert cpp_pkg.total == 4
    assert cpp_pkg.count("failed") == 1
    assert cpp_pkg.count("error") == 1
    assert cpp_pkg.failed == 2


def test_failure_message_is_first_line(collected) -> None:
    results, _ = collected
    py_pkg = next(result for result in results if result.name == "py_pkg")
    failed = next(case for case in py_pkg.cases if case.outcome == "failed")
    assert failed.name == "py_pkg.test.test_geometry.test_clamp_above"
    assert failed.message == "assert 5 == 4"


def test_coverage_per_language(collected) -> None:
    _, coverages = collected
    by_package = {(cov.package, cov.language): cov for cov in coverages}
    python = by_package["py_pkg", "Python"]
    assert (python.lines_covered, python.lines_valid) == (30, 40)
    assert python.line_rate == pytest.approx(0.75)
    assert python.branch_rate == pytest.approx(0.75)
    cpp = by_package["cpp_pkg", "C/C++"]
    assert cpp.line_rate == pytest.approx(0.9)
    assert cpp.branch_rate is None


def test_markdown_report(collected) -> None:
    results, coverages = collected
    markdown = report.render_markdown("Tests ROS 2 (jazzy)", results, coverages)
    assert markdown.startswith("## Tests ROS 2 (jazzy)")
    assert ":x: 4 réussis, 3 en échec, 1 ignorés sur 8 tests dans 2 paquets." in markdown
    assert "| `py_pkg` | 4 | 2 | 1 | 1 |" in markdown
    assert "| **Total** | 8 | 4 | 3 | 1 |" in markdown
    assert "### Tests en échec" in markdown
    # Pipes in test names and messages must not break the table.
    assert "`MathTest.Pipe\\|Name`" in markdown
    assert "| `py_pkg` | Python | 30/40 | 75.0 % | 75.0 % |" in markdown
    assert "| `cpp_pkg` | C/C++ | 9/10 | 90.0 % | n/a |" in markdown


def test_markdown_all_green() -> None:
    result = report.PackageResult("ok_pkg", [report.TestCase("ok_pkg", "t", "passed")])
    markdown = report.render_markdown("T", [result], [])
    assert ":white_check_mark: 1 réussis, 0 en échec" in markdown
    assert "Tests en échec" not in markdown
    assert "Couverture" not in markdown


def test_markdown_without_results(tmp_path: Path) -> None:
    results, coverages = report.collect(tmp_path / "missing")
    markdown = report.render_markdown("T", results, coverages)
    assert "Aucun résultat de test trouvé" in markdown


def test_annotations_are_escaped(collected) -> None:
    results, _ = collected
    commands = report.annotations(results)
    assert len(commands) == 3
    gtest = next(command for command in commands if "Pipe" in command)
    assert gtest.startswith("::error title=cpp_pkg%3A MathTest.Pipe|Name::")
    assert "\n" not in gtest


def test_copy_reports(tmp_path: Path) -> None:
    copied = report.copy_reports(BUILD, tmp_path)
    assert copied == 6
    assert (tmp_path / "py_pkg" / "pytest.xml").is_file()
    assert (tmp_path / "cpp_pkg" / "test_results" / "cpp_pkg" / "test_math.gtest.xml").is_file()
    assert (tmp_path / "cpp_pkg" / "coverage-gcovr.xml").is_file()


def test_main_github_outputs(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys) -> None:
    summary = tmp_path / "summary.md"
    outputs = tmp_path / "outputs"
    monkeypatch.setenv("GITHUB_STEP_SUMMARY", str(summary))
    monkeypatch.setenv("GITHUB_OUTPUT", str(outputs))
    output = tmp_path / "report.md"
    code = report.main(["--build-base", str(BUILD), "--title", "CI", "--output", str(output), "--github"])
    assert code == 0
    assert summary.read_text(encoding="utf-8").startswith("## CI")
    assert output.read_text(encoding="utf-8") == summary.read_text(encoding="utf-8")
    assert outputs.read_text(encoding="utf-8") == "tests=8\nfailures=3\nskipped=1\n"
    assert "::error title=" in capsys.readouterr().out
