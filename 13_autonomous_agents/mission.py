"""Give Wednesday's Gemma agent a bounded mapping or navigation mission."""

from importlib import import_module
import asyncio
import json
import math
from queue import Empty, Queue
from threading import Thread
from time import monotonic

from mcp.server.fastmcp import FastMCP
from mcp.shared.memory import create_connected_server_and_client_session

robot_controls = import_module("11_slam_teleop.robot")
Interrupted = robot_controls.Interrupted
remaining = robot_controls.remaining

agent = import_module("09_python_agent.agent")
gemma = import_module("08_gemma_ollama.gemma")
mcp_read = import_module("07_ros_mcp.mcp_read")


def lidar_summary(scan, yaw_deg, frame):
    if scan["header"]["frame_id"] != frame:
        raise ValueError("LiDAR frame differs from the verified station frame.")
    start, step = scan["angle_min"], scan["angle_increment"]
    if (not math.isfinite(start) or not math.isfinite(step)
            or step == 0 or abs(step) * len(scan["ranges"]) < 1.9 * math.pi):
        raise ValueError("The mapping exercise requires a calibrated full-circle LiDAR scan.")
    yaw = math.radians(yaw_deg)
    front, left, right, rear = [], [], [], []
    for index, distance in enumerate(scan["ranges"]):
        if (type(distance) not in (int, float) or not math.isfinite(distance)
                or not scan["range_min"] <= distance <= scan["range_max"]):
            continue
        angle = math.remainder(start + index * step + yaw, math.tau)
        if abs(angle) <= math.pi / 4 + 1e-9:
            front.append(distance)
        elif abs(angle) >= 3 * math.pi / 4 - 1e-9:
            rear.append(distance)
        elif angle > 0:
            left.append(distance)
        else:
            right.append(distance)
    if not all((front, left, right, rear)):
        raise ValueError("LiDAR data is missing from one or more quadrants.")
    return {name: min(samples) for name, samples in
            (("front_m", front), ("left_m", left), ("right_m", right), ("rear_m", rear))}


def mapping_observation(robot, deadline):
    config = robot.station["mapping"]
    clearances = lidar_summary(robot.read("/scan", deadline), config["scan_yaw_deg"],
                               config["scan_frame"])
    grid = robot.read("/map", deadline)
    cells = grid["data"]
    area = grid["info"]["width"] * grid["info"]["height"]
    if grid["header"]["frame_id"] != "map" or not cells or len(cells) != area:
        raise ValueError("No valid map-frame occupancy grid from SLAM.")
    mapped = sum(value >= 0 for value in cells)
    if not mapped:
        raise ValueError("SLAM has yet to observe any cells.")
    return {"clearance": clearances, "observed_cells": mapped,
            "grid_cells": area, "allowed_moves": allowed_moves(config, clearances)}


def allowed_moves(config, clearance):
    moves = []
    if (clearance["front_m"] >= config["front_clearance_m"]
            and min(clearance.values()) >= config["turn_clearance_m"]):
        moves.append("forward")
    if min(clearance.values()) >= config["turn_clearance_m"]:
        moves.extend(("left", "right"))
    return moves


def odometry(robot, deadline):
    pose = robot.read("/odom", deadline)["pose"]["pose"]
    point, q = pose["position"], pose["orientation"]
    if not all(math.isfinite(value) for value in (point["x"], point["y"], *q.values())):
        raise ValueError("Odometry contains nonfinite values.")
    heading = math.atan2(2 * (q["w"] * q["z"] + q["x"] * q["y"]),
                         1 - 2 * (q["y"] ** 2 + q["z"] ** 2))
    return point["x"], point["y"], heading


def verified_step(robot, direction, deadline):
    config = robot.station["mapping"]
    before = odometry(robot, deadline)
    clearance = lidar_summary(robot.read("/scan", deadline), config["scan_yaw_deg"],
                              config["scan_frame"])
    if direction not in allowed_moves(config, clearance):
        raise RuntimeError("Current LiDAR readings prevent that mapping move.")
    result = robot.drive(direction, deadline)
    observe_until = min(deadline, monotonic() + 2)
    while True:
        after = odometry(robot, observe_until)
        distance = math.hypot(after[0] - before[0], after[1] - before[1])
        turn = math.remainder(after[2] - before[2], math.tau)
        if ((direction == "forward" and distance >= 0.005)
                or (direction == "left" and turn >= 0.02)
                or (direction == "right" and turn <= -0.02)):
            return {**result, "odom_distance_m": round(distance, 3),
                    "odom_turn_deg": round(math.degrees(turn), 1)}
        if monotonic() >= observe_until:
            raise RuntimeError("Odometry did not confirm the requested mapping movement.")


def create_tools(robot, mode, deadline, visited, build_pose):
    server = FastMCP("Thursday Auron Workshop")

    @server.tool()
    def observe() -> dict:
        """Read the robot state and current mission observations."""
        status = robot.require_ready(mode, deadline)
        if mode == "mapping":
            return {"mode": status["active_mode"], **mapping_observation(robot, deadline)}
        return {"mode": status["active_mode"], "odom": odometry(robot, deadline),
                "remaining_checkpoints": [name for name in robot.station["nav"]["checkpoints"]
                                          if name not in visited]}

    @server.tool()
    def mapping_move(direction: str) -> dict:
        """Make one short mapping movement from the observed allowed moves."""
        if mode != "mapping" or direction not in ("forward", "left", "right"):
            raise ValueError("Invalid mapping move.")
        return verified_step(robot, direction, deadline)

    @server.tool()
    def navigation_goal(checkpoint: str) -> dict:
        """Send a single navigation goal to an unvisited station checkpoint."""
        if mode != "nav" or checkpoint in visited:
            raise ValueError("Invalid or already visited checkpoint.")
        result = robot.navigate(checkpoint, build_pose, deadline)
        visited.append(checkpoint)
        return result

    return server


def model_tools(mode, options):
    action, argument = (("mapping_move", "direction") if mode == "mapping"
                        else ("navigation_goal", "checkpoint"))
    return [
        {"type": "function", "function": {"name": action,
         "description": f"Choose one allowed {argument} from the latest robot observations.",
         "parameters": {"type": "object", "additionalProperties": False, "required": [argument],
                        "properties": {argument: {"type": "string", "enum": options}}}}},
        {"type": "function", "function": {"name": "finish", "description": "End the mission.",
         "parameters": {"type": "object", "additionalProperties": False, "properties": {}}}},
    ], action, argument


async def choose(messages, model, tools, deadline, stopped, ask_model):
    # Keep the shared Ollama helper. A late reply has no robot capability.
    response = Queue()

    def request():
        try:
            response.put((True, ask_model(messages, model=model, tools=tools)))
        except Exception as error:
            response.put((False, error))

    Thread(target=request, daemon=True).start()
    while True:
        pause = min(0.10, remaining(deadline, stopped))
        try:
            ok, value = response.get_nowait()
        except Empty:
            await asyncio.sleep(pause)
            continue
        if not ok:
            raise value
        return value


async def run_mission(robot, mode, task, build_pose, model=gemma.MODEL, ask_model=gemma.ask):
    robot.require_enabled()
    config = robot.station[mode]
    deadline = monotonic() + config["mission_s"]
    visited = []
    results = []
    server = create_tools(robot, mode, deadline, visited, build_pose)
    reason = "step_limit"
    async with create_connected_server_and_client_session(server) as session:
        for _ in range(config["max_steps"]):
            if robot.stopped():
                raise Interrupted("Operator stopped the mission.")
            if monotonic() >= deadline:
                reason = "time_limit"
                break
            observation = await mcp_read.call(session, "observe", {})
            options = observation["allowed_moves" if mode == "mapping" else "remaining_checkpoints"]
            if not options:
                reason = "no_clear_move" if mode == "mapping" else "checkpoints_complete"
                break
            tools, action, argument = model_tools(mode, options)
            messages = [
                {"role": "system", "content": "Choose exactly one offered tool. Use the latest "
                 "observations and prior results. Choose finish if the task is complete or you "
                 "cannot continue. A mapping move adds observations to SLAM. A navigation goal "
                 "requests a checkpoint on the existing map."},
                {"role": "user", "content": json.dumps({"task": task, "observation": observation,
                 "prior_results": results, "steps_remaining": config["max_steps"] - len(results)})},
            ]
            try:
                reply = await choose(messages, model, tools, deadline, robot.stopped, ask_model)
            except TimeoutError:
                reason = "time_limit"
                break
            selected = agent.select_tool(reply) if isinstance(reply, dict) else None
            if selected == ("finish", {}):
                reason = "agent_finished"
                break
            if selected is None:
                raise RuntimeError("Expected exactly one valid tool call. Mission ended.")
            tool, arguments = selected
            if tool != action or set(arguments) != {argument} or arguments[argument] not in options:
                raise RuntimeError("Agent proposed a tool or argument outside this mission.")
            remaining(deadline, robot.stopped)
            results.append(await mcp_read.call(session, tool, arguments))
        if mode == "nav" and results and len(visited) == len(config["checkpoints"]):
            reason = "checkpoints_complete"
    return {"mode": mode, "ended": reason, "steps": len(results), "results": results}
