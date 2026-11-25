#!/usr/bin/env bash
# Choose how OpenGL renders in this job (Gazebo sensors, RViz) and export it.
#
#   RENDERING=auto (default)  hardware if a GPU is usable here, software otherwise
#   RENDERING=hardware        force hardware rendering
#   RENDERING=software        force Mesa llvmpipe (LIBGL_ALWAYS_SOFTWARE=1)
#
# A GPU is usable when nvidia-smi lists one (NVIDIA runtime) or a DRI render
# node is readable (Mesa drivers). Exports ROS2_CI_RENDERING=hardware|software and,
# for software rendering, LIBGL_ALWAYS_SOFTWARE=1, to $GITHUB_ENV when set,
# otherwise prints the assignments for eval.
set -euo pipefail

mode="${RENDERING:-auto}"
reason="forced"
if [ "${mode}" = "auto" ]; then
  mode="software"
  reason="no GPU visible"
  if command -v nvidia-smi >/dev/null 2>&1 && gpu="$(nvidia-smi -L 2>/dev/null | head -n 1)" && [ -n "${gpu}" ]; then
    mode="hardware"
    reason="${gpu}"
  else
    for node in /dev/dri/renderD*; do
      if [ -r "${node}" ] && [ -w "${node}" ]; then
        mode="hardware"
        reason="DRI render node ${node}"
        break
      fi
    done
  fi
fi
case "${mode}" in
  hardware | software) ;;
  *)
    echo "Unknown RENDERING '${mode}', expected auto, hardware or software." >&2
    exit 1
    ;;
esac

lines=("ROS2_CI_RENDERING=${mode}")
if [ "${mode}" = "software" ]; then
  lines+=("LIBGL_ALWAYS_SOFTWARE=1")
fi
echo "Rendering: ${mode} (${reason})" >&2
if [ -n "${GITHUB_ENV:-}" ]; then
  printf '%s\n' "${lines[@]}" >>"${GITHUB_ENV}"
  if [ -n "${GITHUB_STEP_SUMMARY:-}" ]; then
    printf 'Rendu OpenGL : **%s** (%s)\n\n' "${mode}" "${reason}" >>"${GITHUB_STEP_SUMMARY}"
  fi
else
  printf 'export %s\n' "${lines[@]}"
fi
