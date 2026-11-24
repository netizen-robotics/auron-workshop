"""Build and send one map-frame goal to a named Auron checkpoint."""

import argparse
from importlib import import_module
import math
from time import monotonic

workshop = import_module("11_slam_teleop.workshop")


def build_pose(x, y, yaw_deg):
    """Return a PoseStamped dictionary in the map frame."""
    # Position is in metres. Compute sin and cos of half the heading in radians.
    raise NotImplementedError("Complete build_pose. See the goal message in the lab guide.")


def main(pose_builder=build_pose):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("checkpoint")
    parser.add_argument("--station", default="thursday.station.json")
    args = parser.parse_args()

    def navigate(robot):
        return robot.navigate(args.checkpoint, pose_builder, monotonic() + 35)

    workshop.run(parser, args.station, navigate)


if __name__ == "__main__":
    main()
