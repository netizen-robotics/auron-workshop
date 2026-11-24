"""Read one ROS pose message through rosbridge without moving either robot."""

import argparse
import asyncio
import json
import math

# Tornado opens the asynchronous WebSocket: https://www.tornadoweb.org/en/stable/websocket.html
# rosbridge JSON operations: https://github.com/RobotWebTools/rosbridge_suite/blob/ros2/ROSBRIDGE_PROTOCOL.md
from tornado.websocket import WebSocketError, websocket_connect


TOPICS = {
    "turtle": ("/turtle1/pose", "turtlesim/msg/Pose"),
    "auron": ("/odom", "nav_msgs/msg/Odometry"),
}


async def read_one_pose(url, topic, message_type):
    async with asyncio.timeout(10):
        websocket = await websocket_connect(url)
        try:
            # Subscribe to a stream and return the first message for this topic.
            subscription = {"op": "subscribe", "topic": topic, "type": message_type}
            await websocket.write_message(json.dumps(subscription))
            while (raw := await websocket.read_message()) is not None:
                packet = json.loads(raw)
                if packet.get("op") == "publish" and packet.get("topic") == topic:
                    return packet["msg"]
                if packet.get("op") == "status" and packet.get("level") == "error":
                    raise RuntimeError(packet["msg"])
            raise RuntimeError("rosbridge closed the connection before sending a pose")
        finally:
            websocket.close()


def print_pose(target, topic, message):
    if target == "turtle":
        print(f"{topic}  x={message['x']:.3f}  y={message['y']:.3f}  "
              f"heading={message['theta']:.3f} rad  (turtlesim units)")
        return

    pose = message["pose"]["pose"]
    position = pose["position"]
    q = pose["orientation"]
    # Odometry encodes orientation as a quaternion. Convert it to the robot’s planar heading.
    yaw = math.atan2(
        2 * (q["w"] * q["z"] + q["x"] * q["y"]),
        1 - 2 * (q["y"] ** 2 + q["z"] ** 2),
    )
    frame = message["header"]["frame_id"]
    child = message["child_frame_id"]
    print(f"{topic}  x={position['x']:.3f} m  y={position['y']:.3f} m  "
          f"yaw={yaw:.3f} rad  ({frame} → {child})")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("target", choices=TOPICS, help="Select the ROS topic and message type")
    parser.add_argument("--url", default="ws://127.0.0.1:9090", help="Rosbridge WebSocket URL")
    parser.add_argument("--topic", help="Override the topic if your robot uses a namespace")
    args = parser.parse_args()
    topic, message_type = TOPICS[args.target]
    topic = args.topic or topic
    try:
        message = asyncio.run(read_one_pose(args.url, topic, message_type))
        print_pose(args.target, topic, message)
    except TimeoutError:
        parser.exit(1, f"Timed out waiting for {topic} via {args.url}. Check the bridge and topic.\n")
    except (OSError, ValueError, WebSocketError, RuntimeError) as error:
        parser.exit(1, f"Could not read {topic} via {args.url}. {error}\n")


if __name__ == "__main__":
    main()
