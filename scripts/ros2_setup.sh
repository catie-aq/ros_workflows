#!/usr/bin/env bash
# Prepare a colcon workspace: ROS 2 (installed if absent), upstream repositories,
# system dependencies with rosdep.
#
# Environment (all optional except where noted):
#   WORKSPACE      colcon workspace, sources in $WORKSPACE/src (default: ws)
#   DISTRIBUTION   ROS distribution (default: $ROS_DISTRO of the image)
#   INSTALL_ROS    install ROS 2 when /opt/ros/<distro> is missing (default: true)
#   REPOS_FILE     .repos file imported with vcs into $WORKSPACE/src
#   PACKAGES       restrict rosdep to these packages and their workspace dependencies
#   SKIP_KEYS      rosdep keys to skip, whitespace separated
#   ROSDEP_CHECK   run rosdep check after the install (default: true)
#   APT_PACKAGES   extra apt packages, whitespace separated
#   GIT_TOKEN      token used for private https://github.com/ repositories
set -euo pipefail
# shellcheck source=scripts/common.sh disable=SC1091
source "$(dirname "$0")/common.sh"

workspace="${WORKSPACE:-ws}"
APT_PACKAGES="${APT_PACKAGES:-}"
PACKAGES="${PACKAGES:-}"
SKIP_KEYS="${SKIP_KEYS:-}"
distro="$(resolve_distro "${DISTRIBUTION:-}")"
export ROS_DISTRO="${distro}"

if [ ! -f "/opt/ros/${distro}/setup.bash" ]; then
  if [ "${INSTALL_ROS:-true}" != "true" ]; then
    echo "/opt/ros/${distro} is missing and INSTALL_ROS is false." >&2
    exit 1
  fi
  "$(dirname "$0")/install_ros.sh" "${distro}"
fi

# Sources checked out by another user (actions/checkout on the host) stay usable by git.
git config --global --add safe.directory '*'
if [ -n "${GIT_TOKEN:-}" ]; then
  git config --global url."https://x-access-token:${GIT_TOKEN}@github.com/".insteadOf "https://github.com/"
fi

mkdir -p "${workspace}/src"
if [ -n "${REPOS_FILE:-}" ]; then
  group "Import ${REPOS_FILE}"
  vcs import --recursive --shallow --input "${REPOS_FILE}" "${workspace}/src"
  endgroup
fi

if [ -n "${APT_PACKAGES//[[:space:]]/}" ]; then
  group "Install extra apt packages"
  # shellcheck disable=SC2086
  apt_install ${APT_PACKAGES}
  endgroup
fi

paths=("${workspace}/src")
if [ -n "${PACKAGES//[[:space:]]/}" ]; then
  source_setup "/opt/ros/${distro}/setup.bash"
  selection_args --packages-up-to "${PACKAGES}"
  mapfile -t paths < <(colcon list --base-paths "${workspace}/src" --paths-only "${SELECTION[@]}")
  if [ "${#paths[@]}" -eq 0 ]; then
    echo "No package matches PACKAGES='${PACKAGES}'." >&2
    exit 1
  fi
fi

group "rosdep install (${distro})"
if [ ! -f /etc/ros/rosdep/sources.list.d/20-default.list ]; then
  as_root rosdep init
fi
rosdep update --rosdistro "${distro}"
if [ ! -f /tmp/.ros2-ci-apt-updated ]; then
  as_root apt-get update -qq
  touch /tmp/.ros2-ci-apt-updated
fi
skip=()
if [ -n "${SKIP_KEYS//[[:space:]]/}" ]; then
  skip=(--skip-keys "${SKIP_KEYS}")
fi
DEBIAN_FRONTEND=noninteractive rosdep install --from-paths "${paths[@]}" --ignore-src -y -q \
  --rosdistro "${distro}" "${skip[@]}"
endgroup

if [ "${ROSDEP_CHECK:-true}" = "true" ]; then
  group "rosdep check"
  rosdep check --from-paths "${paths[@]}" --ignore-src --rosdistro "${distro}" "${skip[@]}"
  endgroup
fi
