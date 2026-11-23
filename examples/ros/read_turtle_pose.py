"""Read one pose from the local turtlesim with native ROS 2."""

import os
from time import monotonic

import rclpy
from turtlesim.msg import Pose


def main() -> int:
    if os.environ.get("ROS_AUTOMATIC_DISCOVERY_RANGE") != "LOCALHOST":
        print("Use the workshop Dev Container for local-only ROS discovery.")
        return 1

    received = False

    def show_pose(pose: Pose) -> None:
        nonlocal received
        print(f"x={pose.x:.2f} y={pose.y:.2f} theta={pose.theta:.2f} rad")
        received = True

    rclpy.init(args=[])
    try:
        node = rclpy.create_node("tuesday_pose_reader")
        try:
            node.create_subscription(Pose, "/turtle1/pose", show_pose, 10)
            deadline = monotonic() + 5
            while rclpy.ok() and not received and monotonic() < deadline:
                rclpy.spin_once(node, timeout_sec=0.1)
        finally:
            node.destroy_node()
    finally:
        rclpy.try_shutdown()

    if not received:
        print("No pose received. Start turtlesim and check that turtle1 exists.")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
