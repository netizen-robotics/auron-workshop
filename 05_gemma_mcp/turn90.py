"""Supervised verification of Auron's guarded velocity-only 90 degree turn."""
from importlib import import_module
import argparse
import asyncio
from contextlib import closing
import json
from math import atan2, cos, degrees, radians, sin
from pathlib import Path
import sys
from time import monotonic, sleep
from typing import Literal

# MCP transports the reviewed goal to the instructor demo: https://github.com/modelcontextprotocol/python-sdk
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.server.fastmcp import FastMCP
from websocket import create_connection, WebSocketTimeoutException

from .agent import TOOLS, select_tool
from .gemma import ask
from .mcp_read import call

auron = import_module("04_auron_robotics.auron")


def yaw(q):
    x,y,z,w = (q[key] for key in "xyzw")
    return atan2(2*(w*z+x*y), 1-2*(y*y+z*z))


# Wrap the heading difference so crossing ±π does not look like a full revolution.
def signed_delta(current, previous):
    return atan2(sin(current-previous),cos(current-previous))


def ready(station):
    status = auron.subscribe_once(station, "/robot_mode_status")
    return status["state"] == "idle" and status["active_mode"] == status["requested_mode"] == "manual" and status["nav_ready"]


def turn(station):
    plan = auron.motion_plan(station, "left")
    topic = plan["topic"]
    if not ready(station) or auron.topics(station).get(topic) != auron.VELOCITY_TYPE:
        raise RuntimeError("Manual mode or TwistStamped input is unavailable.")
    with closing(create_connection(station["url"], timeout=2)) as socket:
        stamp = auron.robot_clock(socket)
        auron.send(socket, op="subscribe", topic="/odom", id="turn-odometry", queue_length=1)
        auron.send(socket, op="advertise", topic=topic, type=auron.VELOCITY_TYPE)
        socket.settimeout(0.24)
        started = None
        deadline = monotonic() + 4
        previous = None
        total = 0.0
        goal = radians(90)
        reason = "turn deadline"
        try:
            while monotonic() < deadline:
                try:
                    packet = json.loads(socket.recv())
                except WebSocketTimeoutException:
                    if started is None:
                        continue
                    reason = "odometry stalled"
                    break
                if packet.get("op") == "status" and packet.get("level") == "error":
                    raise RuntimeError(packet.get("msg"))
                if packet.get("op") != "publish" or packet.get("topic") != "/odom":
                    continue
                data = packet["msg"]
                current = yaw(data["pose"]["pose"]["orientation"])
                if previous is not None:
                    total += signed_delta(current, previous)
                previous = current
                now = monotonic()
                if started is None:
                    started = now
                    deadline = now + 14
                if total >= goal:
                    reason = "reached 90 degrees"
                    break
                if total < -radians(4) or (now - started >= 2.0 and total < radians(2)):
                    reason = "odometry shows insufficient left progress"
                    break
                rate = min(plan["angular_z_rad_s"], max(0.10, (goal - total) * 1.4))
                auron.publish_twist(socket, topic, 0.0, rate, stamp())
        finally:
            for _ in range(3):
                auron.publish_twist(socket, topic, 0.0, 0.0, stamp())
                sleep(0.06)
        return {"reason": reason, "heading_change_before_stop_deg": degrees(total), "zero_sent": True}


def serve(station):
    server = FastMCP("Authorized Auron turn rehearsal")
    used = False

    @server.tool()
    def move_auron(command: Literal["left"]) -> dict:
        """Run the single operator-approved velocity-only left turn to 90 degrees."""
        nonlocal used
        if used or command != "left":
            raise ValueError("One approved left turn only.")
        used = True
        return turn(station)

    server.run(transport="stdio")


async def run(profile):
    proposal = select_tool(ask([{"role":"user","content":"Turn left"}], tools=TOOLS))
    if proposal != ("move_auron", {"command":"left"}):
        raise RuntimeError(f"Unexpected Gemma proposal: {proposal}")
    station = auron.load_station(profile)
    plan = auron.motion_plan(station,"left")
    print(json.dumps({**plan, "seconds": None, "target_deg": 90, "timeout_s": 14},indent=2))
    if input("Full turn area clear and spotter ready with the independent stop? Enter TURN90: ") != "TURN90":
        return
    args = StdioServerParameters(command=sys.executable,
        args=["-m", f"{__package__}.turn90", str(Path(profile).resolve()), "--serve"],
        cwd=Path(__file__).resolve().parents[1])
    async with stdio_client(args) as (reader, writer):
        async with ClientSession(reader, writer) as session:
            await session.initialize()
            await call(session, "move_auron", {"command": "left"})


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("profile")
    p.add_argument("--serve",action="store_true")
    a = p.parse_args()
    if a.serve:
        serve(auron.load_station(a.profile))
    else:
        asyncio.run(run(a.profile))
