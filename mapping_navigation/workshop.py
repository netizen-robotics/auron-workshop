"""Command-line entry point shared by the student and reference programs."""

import argparse
import asyncio
import json
import signal
from threading import Event
from time import monotonic

from mapping_navigation.robot import Robot, station_profile
from gemma_mcp.gemma import MODEL
from mapping_navigation.mission import run_mission
from websocket import WebSocketException

KEYS = {"w": "forward", "a": "left", "d": "right", "s": "stop"}


def teleop(robot):
    robot.require_enabled()
    robot.require_ready("mapping", monotonic() + 5)
    print("w forward · a left · d right · s stop · q quit. Press Enter after each key.")
    while not robot.stopped():
        key = input("Drive> ").strip().lower()
        if key == "q":
            return robot.drive("stop", monotonic() + 5)
        if key in KEYS:
            print(json.dumps(robot.drive(KEYS[key], monotonic() + 10)))
        else:
            print("Choose w, a, d, s or q.")


def main(build_switch, build_pose):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--station", default="thursday.station.json")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("status")
    modes = commands.add_parser("mode")
    modes.add_argument("mode", choices=("mapping", "nav"))
    commands.add_parser("teleop")
    save = commands.add_parser("save-map")
    save.add_argument("name")
    goal = commands.add_parser("goal")
    goal.add_argument("checkpoint")
    agent = commands.add_parser("agent")
    agent.add_argument("mode", choices=("mapping", "nav"))
    agent.add_argument("task")
    agent.add_argument("--model", default=MODEL)
    args = parser.parse_args()
    stopped = Event()
    # Let an active action finish cancellation before tearing down its socket.
    previous_handler = signal.signal(signal.SIGINT, lambda *_: stopped.set())
    try:
        robot = Robot(station_profile(args.station), stopped.is_set)
        match args.command:
            case "status":
                value = robot.status(monotonic() + 5)
            case "mode":
                value = robot.mode(args.mode, build_switch)
            case "teleop":
                # No motion is active between menu prompts.
                signal.signal(signal.SIGINT, previous_handler)
                value = teleop(robot)
            case "save-map":
                value = robot.save_map(args.name)
            case "goal":
                value = robot.navigate(args.checkpoint, build_pose, monotonic() + 35)
            case "agent":
                value = asyncio.run(run_mission(robot, args.mode, args.task, build_pose, args.model))
        print(json.dumps(value, indent=2))
        if args.command == "agent" and not value["steps"]:
            parser.exit(1, "Mission ended without a completed movement. Inspect the result.\n")
    except (EOFError, KeyboardInterrupt, OSError, ValueError, KeyError, TypeError,
            RuntimeError, ExceptionGroup, WebSocketException) as error:
        parser.exit(1, f"Stopped: {describe_error(error)}\n")
    finally:
        signal.signal(signal.SIGINT, previous_handler)


def describe_error(error):
    if isinstance(error, ExceptionGroup):
        return "; ".join(describe_error(child) for child in error.exceptions)
    return str(error) or type(error).__name__
