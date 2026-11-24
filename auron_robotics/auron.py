"""Read and control one instructor-assigned Auron through rosbridge."""

import argparse
import base64
from contextlib import closing
from io import BytesIO
import json
import math
from pathlib import Path
from time import monotonic, monotonic_ns, sleep
from urllib.parse import urlsplit

# Pillow decodes and saves RGB images: https://pillow.readthedocs.io/en/stable/reference/Image.html
# websocket-client connects to the ROS bridge: https://websocket-client.readthedocs.io/en/latest/
# rosbridge protocol: https://github.com/RobotWebTools/rosbridge_suite/blob/ros2/ROSBRIDGE_PROTOCOL.md
from PIL import Image
from websocket import create_connection, WebSocketException

VELOCITY_TYPE = "geometry_msgs/msg/TwistStamped"
MOTION_NAMES = ("forward", "left", "stop")


def load_station(path):
    station = json.loads(Path(path).read_text())
    url = urlsplit(station["url"])
    if url.scheme not in ("ws", "wss") or not url.hostname or url.hostname == "auron_ip":
        raise ValueError("Set the instructor's rosbridge URL in station.json.")
    if url.username or url.password:
        raise ValueError("Use the instructor's URL without credentials in the file.")
    return station


def send(socket, **packet):
    socket.send(json.dumps(packet, allow_nan=False))


def receive(socket, matches):
    deadline = monotonic() + 5
    while monotonic() < deadline:
        socket.settimeout(max(0.01, deadline - monotonic()))
        packet = json.loads(socket.recv())
        if packet.get("op") == "status" and packet.get("level") == "error":
            raise RuntimeError(packet.get("msg", "ROS bridge reported an error."))
        if matches(packet):
            return packet
    raise TimeoutError("No matching response from Auron within five seconds.")


def call_service(socket, service):
    send(socket, op="call_service", service=service, id=service, args={})
    # Match this response to the request ID because one connection can see several packet types.
    result = receive(socket, lambda packet: packet.get("op") == "service_response"
                     and packet.get("id") == service)
    if not result.get("result"):
        raise RuntimeError(f"{service}: {result.get('values')}")
    return result["values"]


def topics(station):
    with closing(create_connection(station["url"], timeout=5)) as socket:
        response = call_service(socket, "/rosapi/topics")
    return dict(zip(response["topics"], response["types"], strict=True))


def subscribe_once(station, topic):
    with closing(create_connection(station["url"], timeout=5)) as socket:
        send(socket, op="subscribe", topic=topic, id="workshop-read", queue_length=1)
        return receive(socket, lambda packet: packet.get("op") == "publish"
                       and packet.get("topic") == topic)["msg"]


def summarize(message):
    fields = {}
    for key, value in message.items():
        if key == "data" or isinstance(value, list) and len(value) > 24:
            fields[key] = {"length": len(value), "sample": value[:5] if key != "data" else None}
            if key == "ranges":
                # Use only finite LiDAR ranges within the sensor’s advertised range in metres.
                valid = [item for item in value if isinstance(item, (int, float))
                         and math.isfinite(item) and message["range_min"] <= item <= message["range_max"]]
                fields[key]["nearest_valid_m"] = min(valid, default=None)
        else:
            fields[key] = value
    return fields


def read_sensor(station, name):
    topic = station["sensors"][name]
    return {"topic": topic, "fields": summarize(subscribe_once(station, topic))}


def capture_rgb(station, output):
    topic = station["sensors"]["rgb"]
    frame = subscribe_once(station, topic)
    if "format" not in frame:
        raise ValueError("Set rgb to Auron's verified sensor_msgs/msg/CompressedImage topic.")
    # rosbridge carries compressed image bytes as base64. Decode them before Pillow opens the frame.
    jpeg = BytesIO()
    with Image.open(BytesIO(base64.b64decode(frame["data"], validate=True))) as image:
        size = image.size
        image.convert("RGB").save(jpeg, "JPEG")
    with Path(output).open("xb") as file:
        file.write(jpeg.getbuffer())
    return {"topic": topic, "file": str(output), "size": size, "header": frame.get("header")}


def motion_plan(station, command):
    config = station["motion"]
    if config.get("enabled") is not True:
        raise RuntimeError("Motion remains disabled until the instructor verifies this station.")
    if config["topic"] != "/cmd_vel_teleop":
        raise ValueError("This starter supports Auron's /cmd_vel_teleop input.")
    linear = float(config["forward_m_s"])
    turn = float(config["turn_rad_s"])
    seconds = float(config["seconds"])
    if not (0 < linear <= 0.10 and 0 < turn <= 0.35 and 0 < seconds <= 0.60):
        raise ValueError("The station limits exceed the workshop pulse envelope.")
    x, z = {"forward": (linear, 0), "left": (0, turn), "stop": (0, 0)}[command]
    return {"command": command, "robot": station["url"], "topic": config["topic"],
            "type": VELOCITY_TYPE, "linear_x_m_s": x, "angular_z_rad_s": z, "seconds": seconds}


def robot_clock(socket):
    """Reference the robot clock at receipt, with a small allowance for clock drift."""
    for _ in range(3):
        started = monotonic_ns()
        response = call_service(socket, "/rosapi/get_time")["time"]
        received = monotonic_ns()
        if received - started <= 150_000_000 and response["sec"] > 0:
            break
    else:
        raise RuntimeError("Could not synchronize with the robot clock in time.")
    # Anchor updates to the robot clock, then advance it using elapsed monotonic time on this laptop.
    reference = response["sec"] * 1_000_000_000 + response["nanosec"] - 10_000_000

    def stamp():
        sec, nanosec = divmod(reference + (monotonic_ns() - received), 1_000_000_000)
        return {"sec": sec, "nanosec": nanosec}

    return stamp


def publish_twist(socket, topic, x, z, stamp):
    # Auron expects a stamped Twist: https://github.com/ros2/common_interfaces/blob/jazzy/geometry_msgs/msg/TwistStamped.msg
    send(socket, op="publish", topic=topic, msg={
        "header": {"frame_id": "base_link", "stamp": stamp},
        "twist": {"linear": {"x": x, "y": 0, "z": 0}, "angular": {"x": 0, "y": 0, "z": z}},
    })


def move(station, command):
    plan = motion_plan(station, command)
    topic = plan["topic"]
    if topics(station).get(topic) != VELOCITY_TYPE:
        raise RuntimeError("Expected TwistStamped on the supported velocity topic.")
    if command != "stop":
        status = subscribe_once(station, "/robot_mode_status")
        if not (status.get("active_mode") == "manual" and status.get("state") == "idle"
                and status.get("nav_ready") is True):
            raise RuntimeError("Auron must be ready in manual mode. Ask the instructor.")
    with closing(create_connection(station["url"], timeout=2)) as socket:
        stamp = robot_clock(socket)
        send(socket, op="advertise", topic=topic, type=VELOCITY_TYPE)
        try:
            deadline = monotonic() + plan["seconds"]
            while monotonic() < deadline:
                publish_twist(socket, topic, plan["linear_x_m_s"], plan["angular_z_rad_s"], stamp())
                sleep(min(0.05, max(0, deadline - monotonic())))
        # Attempt a final zero on exit. Use the robot feedback and spotter to verify the actual stop.
        finally:
            publish_twist(socket, topic, 0, 0, stamp())
    return {"command_sent": command, "zero_sent": True, "check": "Verify motion and stop on Auron."}


def confirmed(plan):
    print(json.dumps(plan, indent=2))
    return input("Spotter ready and area clear? Enter MOVE to send this command: ") == "MOVE"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--station", default="station.json")
    sub = parser.add_subparsers(dest="exercise", required=True)
    sub.add_parser("topics")
    sub.add_parser("inventory")
    sub.add_parser("read").add_argument("sensor")
    sub.add_parser("capture").add_argument("output", type=Path)
    sub.add_parser("move").add_argument("command", choices=MOTION_NAMES)
    args = parser.parse_args()
    try:
        station = load_station(args.station)
        if args.exercise == "topics":
            result = topics(station)
        elif args.exercise == "inventory":
            active = topics(station)
            result = {name: {"topic": topic, "type": active.get(topic)}
                      for name, topic in station["sensors"].items()}
        elif args.exercise == "read":
            result = read_sensor(station, args.sensor)
        elif args.exercise == "capture":
            result = capture_rgb(station, args.output)
        else:
            result = move(station, args.command) if confirmed(motion_plan(station, args.command)) else {"cancelled": True}
        print(json.dumps(result, indent=2))
    except (OSError, EOFError, ValueError, KeyError, RuntimeError, WebSocketException) as error:
        parser.exit(1, f"{error}\n")


if __name__ == "__main__":
    main()
