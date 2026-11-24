"""Reference answer for the Nav2 goal pose."""

from importlib import import_module

from .starter import main

robot_controls = import_module("11_slam_teleop.robot")

if __name__ == "__main__":
    main(robot_controls.reference_pose)
