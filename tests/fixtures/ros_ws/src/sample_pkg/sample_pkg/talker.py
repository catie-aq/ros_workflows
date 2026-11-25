"""Node that publishes a counter on ``chatter``, used by the integration test."""

import rclpy
from rclpy.node import Node
from std_msgs.msg import String


class Talker(Node):
    """Publish ``hello <n>`` on ``chatter`` every 100 ms."""

    def __init__(self) -> None:
        """Create the publisher and the timer."""
        super().__init__("talker")
        self._publisher = self.create_publisher(String, "chatter", 10)
        self._count = 0
        self.create_timer(0.1, self._publish)

    def _publish(self) -> None:
        self._publisher.publish(String(data=f"hello {self._count}"))
        self._count += 1


def main() -> None:
    """Spin the talker until interrupted."""
    rclpy.init()
    node = Talker()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.try_shutdown()
