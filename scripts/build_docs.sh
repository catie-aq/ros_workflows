#!/usr/bin/env bash
# Build the API documentation of the workspace packages with rosdoc2 (the tool
# behind docs.ros.org): Sphinx for Python, Doxygen and Breathe for C++.
#
# Environment (all optional):
#   WORKSPACE     colcon workspace, sources in $WORKSPACE/src (default: ws)
#   DISTRIBUTION  ROS distribution (default: $ROS_DISTRO)
#   PACKAGES      document only these packages
#   OUTPUT_DIR    directory receiving one HTML tree per package (default: docs_output)
set -euo pipefail
# shellcheck source=scripts/common.sh disable=SC1091
source "$(dirname "$0")/common.sh"

workspace="${WORKSPACE:-ws}"
distro="$(resolve_distro "${DISTRIBUTION:-}")"
output_dir="$(mkdir -p "${OUTPUT_DIR:-docs_output}" && cd "${OUTPUT_DIR:-docs_output}" && pwd)"

group "Install rosdoc2"
apt_install python3-rosdoc2 doxygen graphviz
endgroup

source_setup "$(ros_setup_file "${distro}")"
if [ -f "${workspace}/install/setup.bash" ]; then
  # Python API pages import the modules: use the built workspace when there is one.
  source_setup "${workspace}/install/setup.bash"
fi

selection_args --packages-select "${PACKAGES:-}"
work="$(mktemp -d)"
status=0
while read -r name path _; do
  group "rosdoc2 ${name}"
  if rosdoc2 build --package-path "${path}" --output-directory "${output_dir}" \
    --doc-build-directory "${work}/build" --cross-reference-directory "${work}/cross_reference"; then
    echo "${name}: ${output_dir}/${name}/index.html"
  else
    echo "::error::rosdoc2 failed for ${name}"
    status=1
  fi
  endgroup
done < <(colcon list --base-paths "${workspace}/src" "${SELECTION[@]}")
exit "${status}"
