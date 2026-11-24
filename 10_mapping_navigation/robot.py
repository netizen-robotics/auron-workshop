"""Shared Auron controls for the terminal and the Thursday MCP tools."""

from importlib import import_module
from collections.abc import Callable
from contextlib import closing
import json
import math
from pathlib import PurePosixPath
import re
from time import monotonic, sleep
from uuid import uuid4

from websocket import WebSocketException, WebSocketTimeoutException, create_connection

auron = import_module("06_auron_robotics.auron")

STATUS = "/robot_mode_status"
SWITCH = "/switch_robot_mode"
TELEOP = "/cmd_vel_teleop"
ASSIST = "/assisted_teleop"
NAVIGATE = "/navigate_to_pose"
TERMINAL = {4, 5, 6}


class Interrupted(RuntimeError):
    """The operator interrupted the exercise."""


class UnknownStop(RuntimeError):
    """An active action could still be running."""


def station_profile(path):
    station = auron.load_station(path)
    for key, maximum in (("linear_m_s", 0.10), ("turn_rad_s", 0.35), ("pulse_s", 0.60)):
        value = station["mapping"][key]
        if type(value) not in (int, float) or not 0 < value <= maximum:
            raise ValueError(f"Invalid mapping limit: {key}.")
    for mission, max_steps in (("mapping", 15), ("nav", 3)):
        config = station[mission]
        if type(config["max_steps"]) is not int or not 1 <= config["max_steps"] <= max_steps:
            raise ValueError(f"Invalid {mission} step limit.")
        if type(config["mission_s"]) is not int or not 1 <= config["mission_s"] <= 180:
            raise ValueError(f"Invalid {mission} time limit.")
    mapping = station["mapping"]
    for key, minimum in (("front_clearance_m", 0.45), ("turn_clearance_m", 0.30)):
        if not math.isfinite(mapping[key]) or mapping[key] < minimum:
            raise ValueError(f"Invalid mapping clearance: {key}.")
    if not math.isfinite(mapping["scan_yaw_deg"]):
        raise ValueError("Invalid LiDAR yaw.")
    path_on_robot = PurePosixPath(station["nav"]["map_path"])
    if (not path_on_robot.is_relative_to("/share/auron") or ".." in path_on_robot.parts
            or path_on_robot.suffix not in (".yaml", ".yml")):
        raise ValueError("Use the verified robot-side map YAML path under /share/auron.")
    for name, values in station["nav"]["checkpoints"].items():
        if (not re.fullmatch(r"[A-Za-z0-9_-]+", name)
                or not all(type(values[key]) in (int, float) and math.isfinite(values[key])
                           for key in ("x", "y", "yaw_deg"))):
            raise ValueError(f"Invalid navigation checkpoint: {name}.")
    return station


def remaining(deadline, stopped):
    if stopped():
        raise Interrupted("Operator stopped the exercise.")
    seconds = deadline - monotonic()
    if seconds <= 0:
        raise TimeoutError("Robot operation reached its deadline.")
    return seconds


def packet(socket, deadline, stopped, matches):
    while True:
        socket.settimeout(min(0.25, remaining(deadline, stopped)))
        try:
            message = json.loads(socket.recv())
        except WebSocketTimeoutException:
            continue
        if message.get("op") == "status" and message.get("level") == "error":
            raise RuntimeError(message.get("msg", "rosbridge reported an error."))
        if matches(message):
            return message


class Robot:
    def __init__(self, station, stopped: Callable[[], bool] = lambda: False):
        self.station = station
        self.stopped = stopped

    def connect(self, deadline):
        return closing(create_connection(self.station["url"], timeout=min(
            2, remaining(deadline, self.stopped)
        )))

    def service(self, name, service_type, args, deadline):
        request_id = str(uuid4())
        with self.connect(deadline) as socket:
            auron.send(socket, op="call_service", service=name, type=service_type, id=request_id,
                 args=args, timeout=remaining(deadline, self.stopped))
            response = packet(socket, deadline, self.stopped, lambda message:
                              message.get("id") == request_id and message.get("op") == "service_response")
        if response.get("result") is not True:
            raise RuntimeError(f"{name} call failed: {response.get('values')}")
        return response["values"]

    def read(self, topic, deadline):
        # The live occupancy grid can publish as slowly as once every five seconds.
        deadline = min(deadline, monotonic() + (7 if topic == "/map" else 5))
        with self.connect(deadline) as socket:
            options = {}
            if topic == "/map":
                options["qos"] = {"durability": "transient_local", "reliability": "reliable"}
            auron.send(socket, op="subscribe", topic=topic, queue_length=1, **options)
            return packet(socket, deadline, self.stopped, lambda message:
                          message.get("op") == "publish" and message.get("topic") == topic)["msg"]

    def status(self, deadline):
        deadline = min(deadline, monotonic() + 5)
        with self.connect(deadline) as socket:
            clock = auron.robot_clock(socket)
            auron.send(socket, op="subscribe", topic=STATUS, queue_length=1)

            def fresh_status(message):
                if message.get("op") != "publish" or message.get("topic") != STATUS:
                    return False
                now, stamp = clock(), message["msg"]["stamp"]
                elapsed = now["sec"] - stamp["sec"] + (now["nanosec"] - stamp["nanosec"]) / 1e9
                return -0.2 <= elapsed <= 0.75

            return packet(socket, deadline, self.stopped, fresh_status)["msg"]

    def require_ready(self, mode, deadline):
        status = self.status(deadline)
        if (status.get("active_mode"), status.get("requested_mode"), status.get("state"),
            status.get("nav_ready")) != (mode, mode, "idle", True):
            raise RuntimeError(f"Auron is not ready in {mode}: {status.get('last_error') or status}")
        return status

    def mode(self, mode, build_request):
        if self.station.get("enabled") is not True:
            raise RuntimeError("Use an instructor-enabled station profile.")
        if mode not in ("mapping", "nav"):
            raise ValueError("Choose mapping or nav.")
        map_path = self.station["nav"]["map_path"] if mode == "nav" else ""
        request = build_request(mode, map_path)
        if request != {"mode": mode, "map_path": map_path}:
            raise ValueError("The request must contain the selected mode and saved map path.")
        try:
            response = self.service(SWITCH, "auron_interfaces/srv/SwitchRobotMode",
                                    request, monotonic() + 35)
        except (TimeoutError, OSError, WebSocketException) as error:
            raise RuntimeError("Switch response missing. Check status before trying again.") from error
        if response.get("success") is not True:
            raise RuntimeError(f"Switch rejected: {response.get('message')}")
        deadline = monotonic() + 5
        while True:
            status = self.status(deadline)
            if status.get("state") == "error":
                raise RuntimeError(f"Mode switch failed: {status.get('last_error')}")
            if (status.get("active_mode"), status.get("requested_mode"), status.get("state")) == (
                    mode, mode, "idle"):
                return status
            sleep(min(0.10, remaining(deadline, self.stopped)))

    def require_enabled(self):
        if self.station.get("enabled") is not True:
            raise RuntimeError("Use an instructor-enabled station profile.")

    def action(self, name, action_type, args, deadline, during=None):
        goal_id = str(uuid4())
        with self.connect(deadline) as socket:
            def matching(message, operations):
                return (message.get("id") == goal_id and message.get("action") == name
                        and message.get("op") in operations)

            def cancel():
                try:
                    socket.settimeout(1)
                    auron.send(socket, op="cancel_action_goal", id=goal_id, action=name)
                    result = packet(socket, monotonic() + 3, lambda: False,
                                    lambda msg: matching(msg, {"action_result"}))
                    if result.get("status") in TERMINAL and result.get("result") is True:
                        return result
                except (OSError, ValueError, RuntimeError, WebSocketException):
                    pass
                raise UnknownStop(f"{name} termination unconfirmed. Use the independent stop.")

            try:
                remaining(deadline, self.stopped)
                auron.send(socket, op="send_action_goal", id=goal_id, action=name,
                     action_type=action_type, args=args, feedback=during is not None)
                result = packet(socket, deadline, self.stopped, lambda msg:
                                matching(msg, {"action_result", "action_feedback"}))
                if result["op"] == "action_feedback":
                    during()
            except (KeyboardInterrupt, OSError, ValueError, RuntimeError, WebSocketException):
                cancel()
                raise

            if result["op"] == "action_feedback":
                if cancel()["status"] == 6:
                    raise RuntimeError("Assisted teleop aborted during the movement pulse.")
                return
            if result.get("status") not in TERMINAL:
                cancel()
                raise RuntimeError(f"{name} rejected the action: {result.get('values')}")
            if during is not None:
                raise RuntimeError("Assisted teleop ended before the movement pulse.")
            values = result.get("values") or {}
            if result.get("status") != 4 or result.get("result") is not True or values.get("error_code", 0) != 0:
                raise RuntimeError(f"{name} did not succeed: status={result.get('status')}, {values}")
            return {"status": "succeeded", "nav2": values}

    def drive(self, direction, deadline):
        self.require_enabled()
        if direction == "stop":
            with self.connect(deadline) as socket:
                stamp = auron.robot_clock(socket)
                auron.send(socket, op="advertise", topic=TELEOP, type=auron.VELOCITY_TYPE)
                auron.publish_twist(socket, TELEOP, 0, 0, stamp())
            return {"command": "stop", "zero_sent": True}

        config = self.station["mapping"]
        linear, angular = {
            "forward": (config["linear_m_s"], 0),
            "left": (0, config["turn_rad_s"]),
            "right": (0, -config["turn_rad_s"]),
        }[direction]

        self.require_ready("mapping", deadline)

        def pulse():
            # Check mode again after the action becomes active.
            self.require_ready("mapping", deadline)
            with self.connect(deadline) as velocity:
                stamp = auron.robot_clock(velocity)
                auron.send(velocity, op="advertise", topic=TELEOP, type=auron.VELOCITY_TYPE)
                end = monotonic() + config["pulse_s"]
                try:
                    while monotonic() < end:
                        velocity.settimeout(min(0.25, remaining(deadline, self.stopped)))
                        auron.publish_twist(velocity, TELEOP, linear, angular, stamp())
                        sleep(min(0.05, max(0, end - monotonic())))
                finally:
                    velocity.settimeout(0.5)
                    auron.publish_twist(velocity, TELEOP, 0, 0, stamp())

        self.action(ASSIST, "nav2_msgs/action/AssistedTeleop",
                    {"time_allowance": {"sec": 10, "nanosec": 0}},
                    min(deadline, monotonic() + 7), during=pulse)
        return {"command": direction, "zero_sent": True}

    def save_map(self, name):
        self.require_enabled()
        if not re.fullmatch(r"[A-Za-z0-9_-]+", name):
            raise ValueError("Use a unique map name with letters, numbers, hyphens or underscores.")
        base = f"/share/auron/{name}"
        self.require_ready("mapping", monotonic() + 5)
        values = self.service("/slam_toolbox/save_map", "slam_toolbox/srv/SaveMap",
                              {"name": {"data": base}}, monotonic() + 20)
        if values.get("result") != 0:
            raise RuntimeError(f"Map save failed: {values}")
        return {"map_path": base + ".yaml", "result": values["result"]}

    def navigate(self, name, build_pose, deadline):
        self.require_enabled()
        checkpoints = self.station["nav"]["checkpoints"]
        if name not in checkpoints:
            raise ValueError(f"Unknown checkpoint {name!r}. Valid names: {', '.join(checkpoints)}.")
        point = checkpoints[name]
        pose = build_pose(point["x"], point["y"], point["yaw_deg"])
        expected = reference_pose(point["x"], point["y"], point["yaw_deg"])
        if pose != expected:
            raise ValueError("Check the pose frame, position, and quaternion before sending a goal.")
        self.require_ready("nav", deadline)
        result = self.action(NAVIGATE, "nav2_msgs/action/NavigateToPose", {"pose": pose},
                             min(deadline, monotonic() + 30))
        return {"checkpoint": name, "goal_pose": pose, **result}


def reference_switch(mode, map_path):
    return {"mode": mode, "map_path": map_path}


def reference_pose(x, y, yaw_deg):
    half_yaw = math.radians(yaw_deg) / 2
    return {
        "header": {"frame_id": "map"},
        "pose": {
            "position": {"x": x, "y": y, "z": 0.0},
            "orientation": {"x": 0.0, "y": 0.0, "z": math.sin(half_yaw), "w": math.cos(half_yaw)},
        },
    }
