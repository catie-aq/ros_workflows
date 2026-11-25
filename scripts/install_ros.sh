#!/usr/bin/env bash
# Install a ROS 2 distribution on a bare Ubuntu host (runner without container),
# the way ros-tooling/setup-ros does: ROS apt source package, ros-<distro>-ros-base,
# build tools. Usage: install_ros.sh <distro>
set -euo pipefail
# shellcheck source=scripts/common.sh disable=SC1091
source "$(dirname "$0")/common.sh"

distro="$1"
if [ -f "$(ros_setup_file "${distro}")" ]; then
  echo "ROS 2 ${distro} already installed."
  exit 0
fi

group "Install ROS 2 ${distro}"
apt_install ca-certificates curl gnupg lsb-release locales software-properties-common
as_root add-apt-repository -y universe >/dev/null
# shellcheck disable=SC1091
codename="$(. /etc/os-release && echo "${UBUNTU_CODENAME:-${VERSION_CODENAME}}")"
# Pinned version and checksums: the GitHub API "latest" lookup is rate limited per
# IP (shared by all the runners), and the package installs the apt signing key.
version="${ROS_APT_SOURCE_VERSION:-1.3.0}"
case "${version}/${codename}" in
  1.3.0/noble) expected="f31d84adf5054c7d60ded0e82c0f776a77ea33af53d08f40b9ad7c94cca55296" ;;
  1.3.0/jammy) expected="110b9a462d55252decb8b7c816f61c2ba0d9890ce5fb93ac504e97cae5860d76" ;;
  *) expected="${ROS_APT_SOURCE_SHA256:-}" ;;
esac
if [ -z "${expected}" ]; then
  echo "No pinned checksum for ros2-apt-source ${version} on ${codename}: set ROS_APT_SOURCE_SHA256." >&2
  exit 1
fi
curl -fsSL -o /tmp/ros2-apt-source.deb \
  "https://github.com/ros-infrastructure/ros-apt-source/releases/download/${version}/ros2-apt-source_${version}.${codename}_all.deb"
echo "${expected}  /tmp/ros2-apt-source.deb" | sha256sum --check --strict
as_root dpkg -i /tmp/ros2-apt-source.deb
rm -f /tmp/.ros2-ci-apt-updated
apt_install "ros-${distro}-ros-base" ros-dev-tools python3-colcon-common-extensions
endgroup
