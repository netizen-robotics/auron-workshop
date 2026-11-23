"""Send a short velocity pulse to turtlesim on the lab machine."""

import os
from time import monotonic, sleep

TOPIC = "/turtle1/cmd_vel"


def send_pulse(linear: float, angular: float) -> None:
    if os.environ.get("ROS_AUTOMATIC_DISCOVERY_RANGE") != "LOCALHOST":
        raise RuntimeError("Set ROS_AUTOMATIC_DISCOVERY_RANGE=LOCALHOST in both ROS terminals.")
    if not (abs(linear) <= 0.5 and abs(angular) <= 1.0):
        raise ValueError("Command exceeds the simulator limits. Run the exercise tests first.")
    try:
        import rclpy
        from geometry_msgs.msg import Twist
    except ImportError as error:
        raise RuntimeError("Use the prepared ROS 2 Jazzy terminal for turtlesim.") from error

    command = Twist()
    command.linear.x = linear
    command.angular.z = angular

    rclpy.init(args=[])
    try:
        node = rclpy.create_node("tuesday_turtlesim_lab")
        try:
            publisher = node.create_publisher(Twist, TOPIC, 10)
            deadline = monotonic() + 3
            while publisher.get_subscription_count() == 0:
                if monotonic() >= deadline:
                    raise RuntimeError("No turtlesim subscriber found. Start turtlesim first.")
                sleep(0.05)
            try:
                for _ in range(8):
                    publisher.publish(command)
                    sleep(0.1)
            finally:
                if rclpy.ok():
                    publisher.publish(Twist())
                    sleep(0.1)
        finally:
            node.destroy_node()
    finally:
        rclpy.try_shutdown()
