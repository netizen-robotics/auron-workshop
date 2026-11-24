# 12 · Program and Send a Nav2 Goal

[Workshop topic index](../README.md#topics)

Use the saved map and `thursday.station.json` from [Topic 11](../11_slam_teleop/README.md). Run commands from the repository root.

In [starter.py](starter.py), complete `build_pose(x, y, yaw_deg)`. Return a dictionary with `header.frame_id` set to `map`, and `pose.position` with `x`, `y`, and zero `z`. Put the heading quaternion in `pose.orientation`. Its `x` and `y` are zero, its `z` is the sine of half the heading, and its `w` is the cosine. Convert the heading from degrees to radians first.

```sh
python -m 11_slam_teleop.starter mode nav
```

In the dashboard, use **Set initial pose** at Auron’s actual location and drag in its facing direction. If the dashboard needs the map selected, reopen the **same saved map** and then set the pose. Verify the displayed pose and heading. Use `status` below and wait for `active_mode` and `requested_mode` to be `nav`, `state` to be `idle`, and `nav_ready` to be `true`. Confirm with the instructor that checkpoint A matches free space on this exact map.

```sh
python -m 11_slam_teleop.starter status
python -m 12_navigation_goal.starter A
```

Find the checkpoint, goal pose and result in the output. Record both the Nav2 outcome and the arrival you actually observed. Ctrl+C requests cancellation from the terminal. If action termination remains unconfirmed, use the independent stop and tell the instructor. A goal sent from the terminal may not appear as an active dashboard goal.

To compare your functions, replace the goal command’s module with `python -m 12_navigation_goal.solution`. See [solution.py](solution.py). [Nav2 goal interface](https://api.nav2.org/actions/jazzy/navigatetopose.html) · [ROS 2 rosbridge actions](https://github.com/RobotWebTools/rosbridge_suite/blob/ros2/ROSBRIDGE_PROTOCOL.md#45-action-operations)

Continue to [Topic 13](../13_autonomous_agents/README.md).
