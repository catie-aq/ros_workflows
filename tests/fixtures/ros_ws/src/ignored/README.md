Tree ignored by colcon (`COLCON_IGNORE`). `broken_pkg/package.xml` is invalid on
purpose (no `<version>`): `ros2_setup`, `ros2_lint` and `ros2_debs` must not read
it. rosdep alone would (`rosdep install --from-paths` does not honour
`COLCON_IGNORE`), which broke the first GitHub run of the self-test.
