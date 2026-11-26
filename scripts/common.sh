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

# Never wait for an answer: debconf questions (tzdata...) take their default.
export DEBIAN_FRONTEND=noninteractive

# Marker of the apt index update, once per job. It assumes an ephemeral runner
# or container: one job, one temporary directory.
apt_marker() {
  echo "${TMPDIR:-/tmp}/.ros2-ci-apt-updated"
}

# Bound apt network operations (also those run by rosdep): a stalled mirror
# fails after retries instead of hanging until the job timeout.
apt_configure() {
  local conf=/etc/apt/apt.conf.d/80-ros2-ci
  if [ -d /etc/apt/apt.conf.d ] && [ ! -f "${conf}" ]; then
    printf 'Acquire::Retries "3";\nAcquire::http::Timeout "60";\nAcquire::https::Timeout "60";\n' |
      as_root tee "${conf}" >/dev/null
  fi
}

apt_update_once() {
  if [ ! -f "$(apt_marker)" ]; then
    apt_configure
    as_root apt-get update -qq
    touch "$(apt_marker)"
  fi
}

# Install missing apt packages, updating the index once per job.
apt_install() {
  local missing=()
  local package
  for package in "$@"; do
    dpkg-query -W -f='${Status}' "${package}" 2>/dev/null | grep -q "install ok installed" || missing+=("${package}")
  done
  if [ "${#missing[@]}" -eq 0 ]; then
    return 0
  fi
  apt_update_once
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

# rosdep update with a bound and retries: it downloads from raw.githubusercontent.com.
rosdep_update() {
  local attempt
  for attempt in 1 2 3; do
    if timeout 300 rosdep update --rosdistro "$1"; then
      return 0
    fi
    echo "rosdep update failed (attempt ${attempt}/3)" >&2
    sleep 10
  done
  return 1
}

# Directories of the packages colcon discovers under a base path, optionally
# restricted to a selection and its dependencies (--packages-up-to). colcon
# honours COLCON_IGNORE and AMENT_IGNORE, unlike rosdep --from-paths on a tree,
# which reads every package.xml it finds. Fills PACKAGE_PATHS; fails when empty.
package_paths() {
  local base="$1"
  local packages="${2:-}"
  local listed
  selection_args --packages-up-to "${packages}"
  listed="$(colcon list --base-paths "${base}" --paths-only "${SELECTION[@]}")"
  PACKAGE_PATHS=()
  if [ -n "${listed}" ]; then
    mapfile -t PACKAGE_PATHS <<<"${listed}"
  fi
  if [ "${#PACKAGE_PATHS[@]}" -eq 0 ]; then
    if [ -n "${packages//[[:space:]]/}" ]; then
      echo "No ROS package found under ${base} for: ${packages}" >&2
    else
      echo "No ROS package found under ${base}." >&2
    fi
    return 1
  fi
}
