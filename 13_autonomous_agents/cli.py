"""Run either autonomous exercise using the common mission loop."""

import argparse
import asyncio
from importlib import import_module

from .mission import run_mission

workshop = import_module("11_slam_teleop.workshop")
goals = import_module("12_navigation_goal.starter")
gemma = import_module("08_gemma_ollama.gemma")


def main(mode, description):
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument("task")
    parser.add_argument("--station", default="thursday.station.json")
    parser.add_argument("--model", default=gemma.MODEL)
    args = parser.parse_args()

    def start(robot):
        return asyncio.run(run_mission(robot, mode, args.task, goals.build_pose, args.model))

    result = workshop.run(parser, args.station, start)
    if not result["steps"]:
        parser.exit(1, "Mission ended without a completed movement. Inspect the result.\n")
