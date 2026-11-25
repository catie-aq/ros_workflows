#!/usr/bin/env bash
# Build a colcon workspace.
#
# Environment (all optional):
#   WORKSPACE       colcon workspace (default: ws)
#   DISTRIBUTION    ROS distribution (default: $ROS_DISTRO)
#   PACKAGES        build these packages and their dependencies (--packages-up-to)
#   MERGE_INSTALL   true for --merge-install
#   SYMLINK_INSTALL true for --symlink-install
#   BUILD_TYPE      CMAKE_BUILD_TYPE (default: RelWithDebInfo)
#   COVERAGE        true to compile C and C++ with --coverage (gcov)
#   SANITIZER       none (default) or asan (AddressSanitizer)
#   CCACHE          true to compile through ccache (CCACHE_DIR, default: ./.ccache)
#   CMAKE_ARGS      extra CMake arguments, whitespace separated
#   COLCON_ARGS     extra colcon build arguments, whitespace separated
set -euo pipefail
# shellcheck source=scripts/common.sh disable=SC1091
source "$(dirname "$0")/common.sh"

workspace="${WORKSPACE:-ws}"
distro="$(resolve_distro "${DISTRIBUTION:-}")"
source_setup "/opt/ros/${distro}/setup.bash"

flags=()
linker_flags=()
if [ "${COVERAGE:-false}" = "true" ]; then
  flags+=(--coverage)
  linker_flags+=(--coverage)
fi
case "${SANITIZER:-none}" in
  none | "") ;;
  asan)
    flags+=(-fsanitize=address -fno-omit-frame-pointer)
    linker_flags+=(-fsanitize=address)
    ;;
  *)
    echo "Unknown SANITIZER '${SANITIZER}', expected none or asan." >&2
    exit 1
    ;;
esac

cmake_args=("-DCMAKE_BUILD_TYPE=${BUILD_TYPE:-RelWithDebInfo}")
if [ "${#flags[@]}" -gt 0 ]; then
  cmake_args+=(
    "-DCMAKE_C_FLAGS=${flags[*]}"
    "-DCMAKE_CXX_FLAGS=${flags[*]}"
    "-DCMAKE_EXE_LINKER_FLAGS=${linker_flags[*]}"
    "-DCMAKE_SHARED_LINKER_FLAGS=${linker_flags[*]}"
  )
fi

if [ "${CCACHE:-false}" = "true" ]; then
  apt_install ccache
  CCACHE_DIR="${CCACHE_DIR:-$(pwd)/.ccache}"
  export CCACHE_DIR
  export CCACHE_BASEDIR="${CCACHE_BASEDIR:-$(cd "${workspace}" && pwd)}"
  export CCACHE_MAXSIZE="${CCACHE_MAXSIZE:-500M}"
  ccache --zero-stats >/dev/null
  cmake_args+=(-DCMAKE_C_COMPILER_LAUNCHER=ccache -DCMAKE_CXX_COMPILER_LAUNCHER=ccache)
fi

if [ -n "${CMAKE_ARGS:-}" ]; then
  # shellcheck disable=SC2206
  cmake_args+=(${CMAKE_ARGS})
fi

args=(build --event-handlers console_cohesion+ summary+ status- desktop_notification-)
if [ "${MERGE_INSTALL:-false}" = "true" ]; then
  args+=(--merge-install)
fi
if [ "${SYMLINK_INSTALL:-false}" = "true" ]; then
  args+=(--symlink-install)
fi
selection_args --packages-up-to "${PACKAGES:-}"
args+=("${SELECTION[@]}")
if [ -n "${COLCON_ARGS:-}" ]; then
  # shellcheck disable=SC2206
  args+=(${COLCON_ARGS})
fi
# --cmake-args takes every following argument: keep it last.
args+=(--cmake-args "${cmake_args[@]}")

cd "${workspace}"
echo "+ colcon ${args[*]}"
colcon "${args[@]}"

if [ "${CCACHE:-false}" = "true" ]; then
  group "ccache statistics"
  ccache --show-stats
  endgroup
fi
