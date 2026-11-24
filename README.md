# Auron Workshop

Follow Topics 01–05 on Tuesday, 06–09 on Wednesday, and 10–13 on Thursday. Each topic has its own folder. Run commands from the repository root unless a guide says otherwise.

## Get set up once

### Dev Container for Topics 01–05

1. Install [Git](https://git-scm.com/downloads). Install and start Docker Desktop (or Docker Engine on Linux). Run `docker version` in a host terminal and check for a **Server** section. [Docker setup](https://docs.docker.com/get-docker/)
2. Install VS Code, its **Dev Containers** extension, and OpenCode Desktop. [VS Code Dev Containers](https://code.visualstudio.com/docs/devcontainers/containers) · [OpenCode Desktop](https://opencode.ai/download)
3. Clone the repository. Open the cloned folder in VS Code and choose **Dev Containers: Reopen in Container**. Allow time for the first image download. The Dev Container pulls the versioned [runtime image](https://gallery.ecr.aws/netizen-robotics/auron-workshop) from Amazon ECR Public. Docker selects AMD64 or ARM64 automatically. Participants can pull it without an AWS account.

   ```bash
   git clone https://github.com/netizen-robotics/auron-workshop.git
   cd auron-workshop
   ```

4. Open a **new VS Code terminal** after VS Code reconnects. Verify the runtime.

   ```bash
   echo "$ROS_DISTRO"
   python --version
   which python
   ```

   Expect `jazzy` and `/opt/auron-venv/bin/python`. Files you edit are saved in the cloned folder on your laptop.

### Host Python for Topics 06–13

Install [uv](https://docs.astral.sh/uv/getting-started/installation/) and open the workshop checkout in your editor. Run these commands in a **host terminal**. This lab connects to the robot through its existing rosbridge.

```text
uv venv --python 3.12
uv pip install -r requirements.txt
```

Activate `.venv` with `source .venv/bin/activate` on macOS or Linux, or `.\.venv\Scripts\Activate.ps1` in PowerShell. For Wednesday, copy the [example station profile](06_auron_robotics/station.example.json) from the checkout root.

```sh
cp 06_auron_robotics/station.example.json station.json
```

In PowerShell, run `Copy-Item 06_auron_robotics/station.example.json station.json`.

Use the instructor's rosbridge URL and the topic names verified at your station. Ask the instructor to prepare the station configuration before enabling movement. The Thursday guide uses its own station file with the same Python environment.

## Topics

| Topic | Folder |
| --- | --- |
| 01 · Python Fundamentals | [`01_python_fundamentals`](01_python_fundamentals/README.md) |
| 02 · Agentic Coding with OpenCode Desktop | [`02_agentic_coding`](02_agentic_coding/README.md) |
| 03 · ROS 2 Basic Concepts | [`03_ros2_basics`](03_ros2_basics/README.md) |
| 04 · Turtlesim Web Lab | [`04_turtlesim_web`](04_turtlesim_web/README.md) |
| 05 · Control Turtlesim with Python | [`05_turtlesim_python`](05_turtlesim_python/README.md) |
| 06 · Robot Control and Sensing | [`06_auron_robotics`](06_auron_robotics/README.md) |
| 07 · Connect Auron to ROS MCP | [`07_ros_mcp`](07_ros_mcp/README.md) |
| 08 · LLMs, Ollama and Gemma 4 | [`08_gemma_ollama`](08_gemma_ollama/README.md) |
| 09 · Build a Python Agent | [`09_python_agent`](09_python_agent/README.md) |
| 10 · Map and Navigate in the Dashboard | [`10_mapping_dashboard`](10_mapping_dashboard/README.md) |
| 11 · Switch Modes and Drive in SLAM | [`11_slam_teleop`](11_slam_teleop/README.md) |
| 12 · Program and Send a Nav2 Goal | [`12_navigation_goal`](12_navigation_goal/README.md) |
| 13 · Run Autonomous SLAM and Navigation Missions | [`13_autonomous_agents`](13_autonomous_agents/README.md) |

## Reference and troubleshooting

- The Dev Container supplies Python, ROS 2 Jazzy, turtlesim, rosbridge, Nav2, and SLAM Toolbox. Inspect the navigation and mapping interfaces with `ros2 interface show nav2_msgs/action/NavigateToPose` and `ros2 interface show slam_toolbox/srv/SaveMap`.
- Run `ros2 node list` and `ros2 topic list` to inspect the ROS graph while turtlesim runs. The local simulator needs ports 6080 and 9090 available on the laptop. If the browser loses its connection, check the startup terminal.
- Wednesday and Thursday use the host Python environment to connect to the assigned robot.
- Maintainers can rebuild the runtime from [the Dockerfile](.devcontainer/Dockerfile) with `docker build -t auron-workshop:local .devcontainer`.
