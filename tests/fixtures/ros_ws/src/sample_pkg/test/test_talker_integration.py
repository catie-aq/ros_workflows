"""Integration test: a listener receives what the talker node publishes."""

import os
import threading

import pytest
import rclpy
from rclpy.executors import SingleThreadedExecutor
from rclpy.node import Node
from sample_pkg.talker import Talker
from std_msgs.msg import String


@pytest.mark.integration
def test_listener_receives_talker() -> None:
    rclpy.init()
    try:
        talker = Talker()
        listener = Node("listener")
        received = threading.Event()
        listener.create_subscription(String, "chatter", lambda _msg: received.set(), 10)
        executor = SingleThreadedExecutor()
        executor.add_node(talker)
        executor.add_node(listener)
        for _ in range(100):
            executor.spin_once(timeout_sec=0.1)
            if received.is_set():
                break
        assert received.is_set()
    finally:
        rclpy.try_shutdown()


@pytest.mark.integration
def test_rendering_mode_is_exported() -> None:
    # Set by scripts/detect_rendering.sh in the integration job.
    assert os.environ.get("ROS2_CI_RENDERING") in {"hardware", "software"}
