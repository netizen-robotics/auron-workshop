"""Complete these two functions, then run the Thursday robot exercises."""

import math

from .workshop import main


def build_switch(mode, map_path):
    """Return the two string fields for the SwitchRobotMode request."""
    raise NotImplementedError("Complete build_switch. The expected keys are mode and map_path.")


def build_pose(x, y, yaw_deg):
    """Return a PoseStamped dictionary in the map frame."""
    # Position is in metres. Compute sin and cos of half the heading in radians.
    raise NotImplementedError("Complete build_pose. See the goal message in the lab guide.")


if __name__ == "__main__":
    main(build_switch, build_pose)
