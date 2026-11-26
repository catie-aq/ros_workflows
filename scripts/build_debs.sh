#!/usr/bin/env bash
# Build Debian packages of the workspace packages with bloom, the way the ROS
# buildfarm does: bloom-generate rosdebian, then debian/rules binary, in
# dependency order. Each package is installed after its build so that the
# workspace packages depending on it find it. Needs root (apt, rosdep sources).
#
# Environment (all optional):
#   WORKSPACE     colcon workspace, sources in $WORKSPACE/src (default: ws)
#   DISTRIBUTION  ROS distribution (default: $ROS_DISTRO)
#   PACKAGES      package these packages and their workspace dependencies
#   OUTPUT_DIR    directory receiving the .deb files (default: debs)
set -euo pipefail
# shellcheck source=scripts/common.sh disable=SC1091
source "$(dirname "$0")/common.sh"
scripts="$(cd "$(dirname "$0")" && pwd)"

workspace="${WORKSPACE:-ws}"
distro="$(resolve_distro "${DISTRIBUTION:-}")"
output_dir="$(mkdir -p "${OUTPUT_DIR:-debs}" && cd "${OUTPUT_DIR:-debs}" && pwd)"
# shellcheck disable=SC1091
os_version="$(. /etc/os-release && echo "${VERSION_CODENAME}")"
source_setup "$(ros_setup_file "${distro}")"

group "Install packaging tools"
apt_install python3-bloom fakeroot debhelper dh-python
endgroup

selection_args --packages-up-to "${PACKAGES:-}"
mapfile -t entries < <(colcon list --base-paths "${workspace}/src" --topological-order "${SELECTION[@]}")
if [ "${#entries[@]}" -eq 0 ]; then
  echo "No package to build." >&2
  exit 1
fi
paths=()
for entry in "${entries[@]}"; do
  read -r _ path _ <<<"${entry}"
  paths+=("${path}")
done

group "rosdep keys of the workspace packages"
rosdep_yaml="$(mktemp -d)/workspace.yaml"
python3 "${scripts}/workspace_rosdep.py" --distro "${distro}" --output "${rosdep_yaml}" "${paths[@]}"
echo "yaml file://${rosdep_yaml}" | as_root tee /etc/ros/rosdep/sources.list.d/00-workspace.list
rosdep_update "${distro}" >/dev/null
endgroup

# Like the buildfarm binary jobs: tests belong to the CI, not to the package build.
# Without this, dh_auto_test runs every test of the package (integration ones
# included), which can be slow or wait on a ROS graph.
export DEB_BUILD_OPTIONS="${DEB_BUILD_OPTIONS:-nocheck}"

staging="$(mktemp -d)"
for entry in "${entries[@]}"; do
  read -r name path _ <<<"${entry}"
  group "Debian package of ${name}"
  # Work on a copy: bloom writes debian/ and the build leaves files next to the sources.
  cp -a "${path}" "${staging}/${name}"
  (
    cd "${staging}/${name}"
    bloom-generate rosdebian --os-name ubuntu --os-version "${os_version}" --ros-distro "${distro}"
    fakeroot debian/rules binary
  )
  mapfile -t built < <(find "${staging}" -maxdepth 1 -name "ros-${distro}-${name//_/-}_*.deb")
  if [ "${#built[@]}" -eq 0 ]; then
    echo "No .deb produced for ${name}" >&2
    exit 1
  fi
  as_root env DEBIAN_FRONTEND=noninteractive apt-get install -y -qq "${built[@]}"
  mv "${built[@]}" "${output_dir}/"
  find "${staging}" -maxdepth 1 -name "ros-${distro}-${name//_/-}-dbgsym_*.ddeb" -exec mv {} "${output_dir}/" \;
  endgroup
done

echo "Debian packages in ${output_dir}:"
ls -1 "${output_dir}"
if [ -n "${GITHUB_STEP_SUMMARY:-}" ]; then
  {
    printf '## Paquets Debian (%s, %s)\n\n' "${distro}" "${os_version}"
    # shellcheck disable=SC2016 # literal backquotes for Markdown
    find "${output_dir}" -maxdepth 1 -name '*.deb' -printf '- `%f`\n' | sort
    echo
  } >>"${GITHUB_STEP_SUMMARY}"
fi
