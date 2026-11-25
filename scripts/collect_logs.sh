#!/usr/bin/env bash
# Gather colcon logs ($WORKSPACE/log) and ROS logs (~/.ros/log, $ROS_LOG_DIR) in one
# directory for upload. Usage: collect_logs.sh <workspace> <destination>
set -uo pipefail

workspace="${1:-ws}"
destination="${2:-ros2-logs}"
mkdir -p "${destination}"
if [ -d "${workspace}/log" ]; then
  cp -rL "${workspace}/log" "${destination}/colcon" 2>/dev/null || true
fi
for dir in "${ROS_LOG_DIR:-}" "${ROS_HOME:-${HOME}/.ros}/log"; do
  if [ -n "${dir}" ] && [ -d "${dir}" ]; then
    mkdir -p "${destination}/ros"
    cp -rL "${dir}/." "${destination}/ros/" 2>/dev/null || true
  fi
done
echo "$(find "${destination}" -type f | wc -l) log files in ${destination}"
