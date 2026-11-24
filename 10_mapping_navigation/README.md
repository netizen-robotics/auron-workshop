# Thursday · Mapping, Navigation and Autonomous Agents

Work with your assigned Auron in the marked bay. One student operates the laptop and one watches the floor and keeps the independent stop available. Use one control program at a time.

## 10 · Map and Navigate in the Dashboard

Create a map in the dashboard’s **Map** menu and drive the marked area manually. Stop and save the map under a unique name. Reopen it in Navigation, use **Set initial pose** to match the robot’s actual position and heading, and wait for readiness. Use **Set goal pose** to choose a nearby point in free space. Observe the arrival and locate **Stop navigation** before switching to the terminal lab.

## Set up

Run these commands in a host terminal from the repository root. Use the [host Python setup](../README.md#host-python-for-topics-0613) and local Ollama model from Wednesday.

```sh
source .venv/bin/activate
cp 10_mapping_navigation/station.example.json thursday.station.json
```

On PowerShell, activate with `.venv\Scripts\Activate.ps1` and copy the profile with `Copy-Item 10_mapping_navigation/station.example.json thursday.station.json`.

The instructor supplies your robot’s rosbridge URL and verifies the map, checkpoints, and motion settings. The example profile is disabled and its coordinates are placeholders. Once your station file is ready, run:

```sh
python -m 10_mapping_navigation.starter status
```

## 11 · Switch Modes and Drive in SLAM

Open [starter.py](starter.py) and complete `build_switch(mode, map_path)`. Return a dictionary with the two string fields `mode` and `map_path`. The robot receives `mapping` with an empty map path, or `nav` with the verified saved YAML path. Use OpenCode to review your function before running it.

```sh
python -m 10_mapping_navigation.starter mode mapping
python -m 10_mapping_navigation.starter status
python -m 10_mapping_navigation.starter teleop
```

Check that `active_mode` and `requested_mode` both say `mapping`, `state` is `idle`, and `nav_ready` is `true` before driving. The status field also reports motion readiness in Mapping mode.

| Key, then Enter | Auron command |
| --- | --- |
| `w` | Forward |
| `a` | Turn left |
| `d` | Turn right |
| `s` | Send zero velocity |
| `q` | Send zero velocity and leave the menu |

Observe the live map while driving. Verify that Auron stops after each pulse. Quit the menu when finished. Save under a new team name, substituting your own name below, and verify the map appears in the dashboard. Copy the returned robot-side YAML path into `nav.map_path` in `thursday.station.json`.

```sh
python -m 10_mapping_navigation.starter save-map team-03-terminal
```

## 12 · Program and Send a Nav2 Goal

In [starter.py](starter.py), complete `build_pose(x, y, yaw_deg)`. Return a dictionary with `header.frame_id` set to `map`, and `pose.position` with `x`, `y`, and zero `z`. Put the heading quaternion in `pose.orientation`. Its `x` and `y` are zero, its `z` is the sine of half the heading, and its `w` is the cosine. Convert the heading from degrees to radians first.

```sh
python -m 10_mapping_navigation.starter mode nav
```

In the dashboard, use **Set initial pose** at Auron’s actual location and drag in its facing direction. If the dashboard needs the map selected, reopen the **same saved map** and then set the pose. Verify the displayed pose and heading. Use `status` below and wait for `active_mode` and `requested_mode` to be `nav`, `state` to be `idle`, and `nav_ready` to be `true`. Confirm with the instructor that checkpoint A matches free space on this exact map.

```sh
python -m 10_mapping_navigation.starter status
python -m 10_mapping_navigation.starter goal A
```

Find the checkpoint, goal pose and result in the output. Record both the Nav2 outcome and the arrival you actually observed. Ctrl+C requests cancellation from the terminal. If action termination remains unconfirmed, use the independent stop and tell the instructor. A goal sent from the terminal may not appear as an active dashboard goal.

To compare your functions, run the same commands with `python -m 10_mapping_navigation.solution`. See [solution.py](solution.py). [Nav2 goal interface](https://api.nav2.org/actions/jazzy/navigatetopose.html) · [ROS 2 rosbridge actions](https://github.com/RobotWebTools/rosbridge_suite/blob/ros2/ROSBRIDGE_PROTOCOL.md#45-action-operations)

## 13 · Run Autonomous SLAM and Navigation Missions

Use the same Gemma model and single-tool selection from Wednesday. Open [mission.py](mission.py) and trace how the agent reads an observation through MCP, selects one tool, checks its result, and decides whether to continue. Change the mission wording and compare its choices. The spotter clears the bay before each run. Launch once and observe the run without approving individual steps.

### SLAM

After ending all navigation, start a fresh Mapping run. Leave dashboard **Auto mapping** off. Observe the map before starting the agent.

```sh
python -m 10_mapping_navigation.starter mode mapping
python -m 10_mapping_navigation.starter status
python -m 10_mapping_navigation.starter agent mapping "Map the nearby area. Move forward when clear and turn if needed."
```

In the log, find the LiDAR clearances, observed map cells, selected movement and odometry change. Find the mission’s completion reason. Compare the map with what you saw before the run and save it under a new name with `save-map`.

### Navigation

Use the terminal lab’s saved map and its verified checkpoints. Switch to Navigation, set the initial pose, and confirm readiness as in Topic 12.

```sh
python -m 10_mapping_navigation.starter agent nav "Visit checkpoint A, then B, then finish."
```

Record the order Gemma selected, the result for each goal, and the arrivals you saw. Compare the requested route with the completed route. The agent gets the checkpoint names from the station and the program gets their coordinates from the profile. An unavailable observation, invalid request, failed move or mission limit ends the run. If Ctrl+C cannot confirm cancellation, use the independent stop.

| Exercise | Show the instructor |
| --- | --- |
| Terminal SLAM | Ready Mapping status, a completed pulse and the saved map name |
| Terminal Navigation | The goal pose, action result and observed arrival |
| Autonomous SLAM | Observations, movement choice, odometry change and saved map |
| Autonomous Navigation | Requested route, selected goals, action results and observed arrivals |

## Instructor rehearsal

- From the repository root, run `python -B -m unittest 10_mapping_navigation.test_workshop` for the mocked controls and MCP checks.
- Record the robot and deployed image. Confirm the actual dashboard controls and check the independent stop. Leave auto mapping disabled and ensure the dashboard and terminal are never driving simultaneously.
- On the assigned robot, verify /robot_mode_status, both mode switches, AssistedTeleop feedback and cancellation through rosbridge, TwistStamped input, the LiDAR frame and quadrant alignment, the live occupancy grid, and save/reopen of the YAML. Measure the pulse and observe the stop, including on disconnect. A rosbridge action must report a terminal result after cancellation.
- Mark the starting pose and nearby free-space checkpoints on the exact saved map. Rehearse the direct goal, an interruption, and both Gemma missions with the sample prompts. Record model choices, actual stops and arrivals. Enable the student profile after those checks.
