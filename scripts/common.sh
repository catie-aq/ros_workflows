#!/usr/bin/env bash
# Helpers shared by the scripts of the composite actions. Sourced, not run.

# Run a command as root: directly in a root container, through sudo on a runner host.
as_root() {
  if [ "$(id -u)" -eq 0 ]; then
    "$@"
  else
    sudo -E "$@"
  fi
}

# Collapsible log groups on GitHub, plain titles elsewhere.
group() {
  if [ -n "${GITHUB_ACTIONS:-}" ]; then
    echo "::group::$*"
  else
    echo "==> $*"
  fi
}

endgroup() {
  if [ -n "${GITHUB_ACTIONS:-}" ]; then
    echo "::endgroup::"
  fi
}

# ROS distribution: explicit value, else the ROS_DISTRO of the image.
resolve_distro() {
  local distro="${1:-${ROS_DISTRO:-}}"
  if [ -z "${distro}" ]; then
    echo "No ROS distribution: set the distribution input or ROS_DISTRO." >&2
    return 1
  fi
  echo "${distro}"
}

# Setup file of a ROS distribution. ROS_INSTALL_ROOT (default /opt/ros) only
# exists so that tests can point the scripts at a fake installation.
ros_setup_file() {
  echo "${ROS_INSTALL_ROOT:-/opt/ros}/$1/setup.bash"
}

# Source a setup file; ROS setup files read unset variables, so relax nounset meanwhile.
source_setup() {
  set +u
  # shellcheck disable=SC1090
  source "$1"
  set -u
}

# Install missing apt packages, updating the index once per job. The marker
# file assumes an ephemeral runner or container: one job, one /tmp.
apt_install() {
  local missing=()
  local package
  for package in "$@"; do
    dpkg-query -W -f='${Status}' "${package}" 2>/dev/null | grep -q "install ok installed" || missing+=("${package}")
  done
  if [ "${#missing[@]}" -eq 0 ]; then
    return 0
  fi
  if [ ! -f /tmp/.ros2-ci-apt-updated ]; then
    as_root apt-get update -qq
    touch /tmp/.ros2-ci-apt-updated
  fi
  as_root env DEBIAN_FRONTEND=noninteractive apt-get install -y -qq --no-install-recommends "${missing[@]}"
}

# Package selection arguments for colcon, from a whitespace separated list.
# Usage: selection_args <--packages-up-to|--packages-select> "$PACKAGES"
selection_args() {
  local option="$1"
  local packages="$2"
  SELECTION=()
  if [ -n "${packages//[[:space:]]/}" ]; then
    # shellcheck disable=SC2206,SC2034
    SELECTION=("${option}" ${packages})
  fi
}
