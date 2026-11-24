"""Switch Auron modes and drive from the terminal in Mapping mode."""

import argparse
import json
from time import monotonic

from .workshop import run

KEYS = {"w": "forward", "a": "left", "d": "right", "s": "stop"}


def build_switch(mode, map_path):
    """Return the two string fields for the SwitchRobotMode request."""
    raise NotImplementedError("Complete build_switch. The expected keys are mode and map_path.")


def teleop(robot):
    robot.require_enabled()
    robot.require_ready("mapping", monotonic() + 5)
    print("w forward · a left · d right · s stop · q quit. Press Enter after each key.")
    while True:
        key = input("Drive> ").strip().lower()
        if key == "q":
            return robot.drive("stop", monotonic() + 5)
        if key in KEYS:
            print(json.dumps(robot.drive(KEYS[key], monotonic() + 10)))
        else:
            print("Choose w, a, d, s or q.")


def main(switch_builder=build_switch):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--station", default="thursday.station.json")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("status")
    modes = commands.add_parser("mode")
    modes.add_argument("mode", choices=("mapping", "nav"))
    commands.add_parser("teleop")
    save = commands.add_parser("save-map")
    save.add_argument("name")
    args = parser.parse_args()

    def operate(robot):
        match args.command:
            case "status":
                return robot.status(monotonic() + 5)
            case "mode":
                return robot.mode(args.mode, switch_builder)
            case "teleop":
                return teleop(robot)
            case "save-map":
                return robot.save_map(args.name)

    run(parser, args.station, operate, cooperative=args.command != "teleop")


if __name__ == "__main__":
    main()
