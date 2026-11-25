#!/usr/bin/env bash
# Install a ROS 2 distribution on a bare Ubuntu host (runner without container),
# the way ros-tooling/setup-ros does: ROS apt source package, ros-<distro>-ros-base,
# build tools. Usage: install_ros.sh <distro>
set -euo pipefail
# shellcheck source=scripts/common.sh disable=SC1091
source "$(dirname "$0")/common.sh"

distro="$1"
if [ -f "/opt/ros/${distro}/setup.bash" ]; then
  echo "ROS 2 ${distro} already installed."
  exit 0
fi

group "Install ROS 2 ${distro}"
apt_install ca-certificates curl gnupg lsb-release locales software-properties-common
as_root add-apt-repository -y universe >/dev/null
# shellcheck disable=SC1091
codename="$(. /etc/os-release && echo "${UBUNTU_CODENAME:-${VERSION_CODENAME}}")"
# Pinned: the GitHub API "latest" lookup is rate limited per IP, shared by all the runners.
version="${ROS_APT_SOURCE_VERSION:-1.3.0}"
curl -fsSL -o /tmp/ros2-apt-source.deb \
  "https://github.com/ros-infrastructure/ros-apt-source/releases/download/${version}/ros2-apt-source_${version}.${codename}_all.deb"
as_root dpkg -i /tmp/ros2-apt-source.deb
rm -f /tmp/.ros2-ci-apt-updated
apt_install "ros-${distro}-ros-base" ros-dev-tools python3-colcon-common-extensions
endgroup
