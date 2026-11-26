#!/usr/bin/env bash
# Static checks of the ROS 2 packages of a source tree, without building them:
# package.xml against its schema (ament_xmllint), CMakeLists.txt style
# (ament_lint_cmake) and, optionally, Python with ruff.
#
# Environment (all optional):
#   LINT_PATH     source tree to check (default: ws/src)
#   DISTRIBUTION  ROS distribution (default: $ROS_DISTRO)
#   XMLLINT       true (default) to check every package.xml
#   CMAKE_LINT    true (default) to check every CMakeLists.txt of a package
#   RUFF          true to run ruff check on the tree (uses the tree's ruff configuration)
#   RUFF_VERSION  ruff version installed when ruff is missing (default: 0.17.6)
set -euo pipefail
# shellcheck source=scripts/common.sh disable=SC1091
source "$(dirname "$0")/common.sh"

lint_path="${LINT_PATH:-ws/src}"
distro="$(resolve_distro "${DISTRIBUTION:-}")"
source_setup "$(ros_setup_file "${distro}")"

# Package directories, skipping trees marked COLCON_IGNORE or AMENT_IGNORE.
ignored_list="$(mktemp)"
mapfile -t packages < <(
  find "${lint_path}" \( -name COLCON_IGNORE -o -name AMENT_IGNORE \) -printf '%h\n' >"${ignored_list}"
  find "${lint_path}" -name package.xml -not -path '*/.git/*' -printf '%h\n' | sort | while read -r dir; do
    skip=false
    while read -r ignored; do
      case "${dir}/" in "${ignored}/"*) skip=true ;; esac
    done <"${ignored_list}"
    [ "${skip}" = "false" ] && echo "${dir}"
  done
)
echo "${#packages[@]} packages under ${lint_path}"

status=0
report() {
  local name="$1" code="$2"
  local line
  if [ "${code}" -eq 0 ]; then
    line="| ${name} | :white_check_mark: |"
  else
    line="| ${name} | :x: |"
    status=1
  fi
  results+=("${line}")
}
results=()

if [ "${XMLLINT:-true}" = "true" ] && [ "${#packages[@]}" -gt 0 ]; then
  group "ament_xmllint (package.xml)"
  set +e
  ament_xmllint "${packages[@]/%//package.xml}"
  code=$?
  set -e
  endgroup
  report "\`ament_xmllint\` (package.xml)" "${code}"
fi

if [ "${CMAKE_LINT:-true}" = "true" ]; then
  cmake_files=()
  for dir in "${packages[@]}"; do
    [ -f "${dir}/CMakeLists.txt" ] && cmake_files+=("${dir}/CMakeLists.txt")
  done
  if [ "${#cmake_files[@]}" -gt 0 ]; then
    group "ament_lint_cmake (CMakeLists.txt)"
    set +e
    ament_lint_cmake "${cmake_files[@]}"
    code=$?
    set -e
    endgroup
    report "\`ament_lint_cmake\` (CMakeLists.txt)" "${code}"
  fi
fi

if [ "${RUFF:-false}" = "true" ]; then
  if ! command -v ruff >/dev/null; then
    ruff_version="${RUFF_VERSION:-0.17.6}"
    group "Install ruff ${ruff_version}"
    # Standalone binary from the GitHub release: no pip, no virtual environment in the
    # ROS image. Checksum pinned for the default version, otherwise the one published
    # next to the archive.
    archive="ruff-$(uname -m)-unknown-linux-gnu.tar.gz"
    url="https://github.com/astral-sh/ruff/releases/download/${ruff_version}/${archive}"
    mkdir -p /tmp/ruff-bin
    curl -fsSL -o "/tmp/ruff-bin/${archive}" "${url}"
    if [ "${ruff_version}/${archive}" = "0.17.6/ruff-x86_64-unknown-linux-gnu.tar.gz" ]; then
      expected="94b33791f48cd54ab35ad673a443a5c001d3e6d87effeaba9899070b700d45f3"
    else
      expected="$(curl -fsSL "${url}.sha256" | awk '{print $1}')"
    fi
    echo "${expected}  /tmp/ruff-bin/${archive}" | sha256sum --check --strict
    tar -xzf "/tmp/ruff-bin/${archive}" -C /tmp/ruff-bin --strip-components 1
    export PATH="/tmp/ruff-bin:${PATH}"
    endgroup
  fi
  group "ruff check"
  set +e
  ruff check --output-format "${RUFF_FORMAT:-full}" "${lint_path}"
  code=$?
  set -e
  endgroup
  report "\`ruff check\`" "${code}"
fi

summary="$(printf '## Lint ROS 2\n\n| Outil | Résultat |\n| ----- | -------- |\n'; printf '%s\n' "${results[@]}")"
echo "${summary}"
if [ -n "${GITHUB_STEP_SUMMARY:-}" ]; then
  printf '%s\n\n' "${summary}" >>"${GITHUB_STEP_SUMMARY}"
fi
exit "${status}"
