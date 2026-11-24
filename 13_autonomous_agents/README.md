# 13 · Run Autonomous SLAM and Navigation Missions

[Workshop topic index](../README.md#topics)

Reuse the same profile from [Topic 11](../11_slam_teleop/README.md). Complete the goal-building function in [Topic 12](../12_navigation_goal/README.md) before running the navigation mission.

Use the same Gemma model and single-tool selection from Wednesday. Open [mission.py](mission.py) and trace how the agent reads an observation through MCP, selects one tool, checks its result, and decides whether to continue. Change the mission wording and compare its choices. The spotter clears the bay before each run. Launch once and observe the run without approving individual steps.

### SLAM

After ending all navigation, start a fresh Mapping run. Leave dashboard **Auto mapping** off. Observe the map before starting the agent.

```sh
python -m 11_slam_teleop.starter mode mapping
python -m 11_slam_teleop.starter status
python -m 13_autonomous_agents.mapping "Map the nearby area. Move forward when clear and turn if needed."
```

In the log, find the LiDAR clearances, observed map cells, selected movement and odometry change. Find the mission’s completion reason. Compare the map with what you saw before the run and save it under a new name with `python -m 11_slam_teleop.starter save-map YOUR-TEAM-MAP`.

### Navigation

Use the terminal lab’s saved map and its verified checkpoints. Switch to Navigation, set the initial pose, and confirm readiness as in [Topic 12](../12_navigation_goal/README.md).

```sh
python -m 13_autonomous_agents.navigation "Visit checkpoint A, then B, then finish."
```

Record the order Gemma selected, the result for each goal, and the arrivals you saw. Compare the requested route with the completed route. The agent gets the checkpoint names from the station and the program gets their coordinates from the profile. An unavailable observation, invalid request, failed move or mission limit ends the run. If Ctrl+C cannot confirm cancellation, use the independent stop.

| Exercise | Show the instructor |
| --- | --- |
| Terminal SLAM | Ready Mapping status, a completed pulse and the saved map name |
| Terminal Navigation | The goal pose, action result and observed arrival |
| Autonomous SLAM | Observations, movement choice, odometry change and saved map |
| Autonomous Navigation | Requested route, selected goals, action results and observed arrivals |

## Instructor rehearsal

- From the repository root, run `python -B -m unittest 13_autonomous_agents.test_workshop` for the mocked controls and MCP checks.
- Record the robot and deployed image. Confirm the actual dashboard controls and check the independent stop. Leave auto mapping disabled and ensure the dashboard and terminal are never driving simultaneously.
- On the assigned robot, verify /robot_mode_status, both mode switches, AssistedTeleop feedback and cancellation through rosbridge, TwistStamped input, the LiDAR frame and quadrant alignment, the live occupancy grid, and save/reopen of the YAML. Measure the pulse and observe the stop, including on disconnect. A rosbridge action must report a terminal result after cancellation.
- Mark the starting pose and nearby free-space checkpoints on the exact saved map. Rehearse the direct goal, an interruption, and both Gemma missions with the sample prompts. Record model choices, actual stops and arrivals. Enable the student profile after those checks.
