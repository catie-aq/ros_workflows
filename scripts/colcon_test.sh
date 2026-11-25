#!/usr/bin/env bash
# Test a built colcon workspace, then summarise results and coverage.
#
# Environment (all optional):
#   WORKSPACE      colcon workspace (default: ws)
#   DISTRIBUTION   ROS distribution (default: $ROS_DISTRO)
#   PACKAGES       test only these packages (--packages-select)
#   MERGE_INSTALL  true if the workspace was built with --merge-install
#   PYTEST_ARGS    JSON array of pytest arguments, for example ["-m", "not integration"]
#   RETRIES        rerun failing tests up to N times (ctest and pytest-rerunfailures)
#   COVERAGE       true for Python (pytest-cov) and C/C++ (gcovr) coverage reports
#   REPORT_TITLE   title of the Markdown summary
#   REPORT_DIR     directory receiving JUnit and coverage files, relative to the
#                  starting directory (default: $WORKSPACE/test-reports)
#   COLCON_ARGS    extra colcon test arguments, whitespace separated
set -euo pipefail
# shellcheck source=scripts/common.sh disable=SC1091
source "$(dirname "$0")/common.sh"
scripts="$(cd "$(dirname "$0")" && pwd)"

workspace="${WORKSPACE:-ws}"
distro="$(resolve_distro "${DISTRIBUTION:-}")"
retries="${RETRIES:-0}"
coverage="${COVERAGE:-false}"
if ! [[ "${retries}" =~ ^[0-9]+$ ]]; then
  echo "RETRIES must be a non-negative integer, got '${retries}'." >&2
  exit 1
fi
# Relative to the directory the script is started from, not to the workspace.
report_dir="${REPORT_DIR:-${workspace}/test-reports}"
case "${report_dir}" in
  /*) ;;
  *) report_dir="$(pwd)/${report_dir}" ;;
esac

# Parse before anything else: an invalid value must stop the step, not vanish in
# a process substitution.
pytest_args=()
if [ -n "${PYTEST_ARGS:-}" ]; then
  parsed="$(python3 -c '
import json, sys
try:
    values = json.loads(sys.argv[1] or "[]")
except json.JSONDecodeError as error:
    sys.exit(f"PYTEST_ARGS is not valid JSON: {error}")
if not isinstance(values, list) or not all(isinstance(v, str) for v in values):
    sys.exit("PYTEST_ARGS must be a JSON array of strings")
for value in values:
    # colcon reads arguments starting with a dash as its own options unless prefixed by a space.
    print(" " + value if value.startswith("-") else value)
' "${PYTEST_ARGS}")"
  if [ -n "${parsed}" ]; then
    mapfile -t pytest_args <<<"${parsed}"
  fi
fi

packages_to_install=()
if [ "${coverage}" = "true" ]; then
  packages_to_install+=(python3-pytest-cov gcovr)
fi
if [ "${retries}" -gt 0 ]; then
  packages_to_install+=(python3-pytest-rerunfailures)
fi
if [ "${#packages_to_install[@]}" -gt 0 ]; then
  group "Install test tools"
  apt_install "${packages_to_install[@]}"
  endgroup
fi

cd "${workspace}"
source_setup "$(ros_setup_file "${distro}")"
source_setup install/setup.bash

if [ "${retries}" -gt 0 ]; then
  pytest_args+=(" --reruns" "${retries}")
fi

args=(test --event-handlers console_cohesion+ summary+ status- desktop_notification-)
if [ "${MERGE_INSTALL:-false}" = "true" ]; then
  args+=(--merge-install)
fi
selection_args --packages-select "${PACKAGES:-}"
args+=("${SELECTION[@]}")
if [ "${retries}" -gt 0 ]; then
  args+=(--retest-until-pass "${retries}")
fi
if [ "${coverage}" = "true" ]; then
  args+=(--pytest-with-coverage)
fi
if [ -n "${COLCON_ARGS:-}" ]; then
  # shellcheck disable=SC2206
  args+=(${COLCON_ARGS})
fi
if [ "${#pytest_args[@]}" -gt 0 ]; then
  # --pytest-args takes every following argument: keep it last.
  args+=(--pytest-args "${pytest_args[@]}")
fi

echo "+ colcon ${args[*]}"
set +e
colcon "${args[@]}"
test_code=$?
set -e

if [ "${coverage}" = "true" ]; then
  group "C/C++ coverage (gcovr)"
  # gcovr 5 (Ubuntu 22.04, Humble) only knows --xml; --cobertura came later.
  cobertura_option=--cobertura
  gcovr --help | grep -q -- '--cobertura' || cobertura_option=--xml
  while read -r name path type; do
    if [ "${type}" != "(ros.ament_cmake)" ] && [ "${type}" != "(cmake)" ]; then
      continue
    fi
    if [ -z "$(find "build/${name}" -name '*.gcda' -print -quit 2>/dev/null)" ]; then
      continue
    fi
    source_dir="$(cd "${path}" && pwd)"
    gcovr --root "${source_dir}" --filter "${source_dir}/" --exclude "${source_dir}/test/" \
      "${cobertura_option}" "build/${name}/coverage-gcovr.xml" --print-summary "build/${name}" ||
      echo "::warning::gcovr failed for ${name}"
  done < <(colcon list "${SELECTION[@]}")
  endgroup
fi

summary_args=(--build-base build --title "${REPORT_TITLE:-Tests ROS 2 (${distro})}" --collect "${report_dir}"
  --output "${report_dir}/summary.md")
if [ -n "${GITHUB_ACTIONS:-}" ]; then
  summary_args+=(--github)
fi
python3 "${scripts}/ros2_ci_report.py" "${summary_args[@]}"

group "colcon test-result"
set +e
colcon test-result --test-result-base build --verbose
result_code=$?
set -e
endgroup

if [ "${test_code}" -ne 0 ]; then
  echo "colcon test exited with ${test_code}" >&2
  exit "${test_code}"
fi
exit "${result_code}"
