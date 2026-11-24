# 11 · Switch Modes and Drive in SLAM

[Workshop topic index](../README.md#topics)

Complete the [dashboard practice](../10_mapping_dashboard/README.md) first. Use the checkout root in your host terminal.

## Set up

Run these commands in a host terminal from the repository root. Use the [host Python setup](../README.md#host-python-for-topics-0613) and local Ollama model from Wednesday.

```sh
source .venv/bin/activate
cp 11_slam_teleop/station.example.json thursday.station.json
```

On PowerShell, activate with `.\.venv\Scripts\Activate.ps1` and copy the profile with `Copy-Item 11_slam_teleop/station.example.json thursday.station.json`.

The instructor supplies your robot’s rosbridge URL and verifies the map, checkpoints, and motion settings. The example profile is disabled and its coordinates are placeholders. Once your station file is ready, run:

```sh
python -m 11_slam_teleop.starter status
```

## Switch modes and drive

Open [starter.py](starter.py) and complete `build_switch(mode, map_path)`. Return a dictionary with the two string fields `mode` and `map_path`. The robot receives `mapping` with an empty map path, or `nav` with the verified saved YAML path. Use OpenCode to review your function before running it.

```sh
python -m 11_slam_teleop.starter mode mapping
python -m 11_slam_teleop.starter status
python -m 11_slam_teleop.starter teleop
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
python -m 11_slam_teleop.starter save-map team-03-terminal
```

Use the [reference solution](solution.py) by replacing `11_slam_teleop.starter` with `11_slam_teleop.solution`. Continue to [Topic 12](../12_navigation_goal/README.md).
