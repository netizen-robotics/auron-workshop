# Auron Workshop

Follow Topics 01–05 on Tuesday, 06–09 on Wednesday, and 10–13 on Thursday. The slide ranges match the workshop decks. Use the commands in each guide for the current numbered folder names.

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

Activate `.venv` with `source .venv/bin/activate` on macOS or Linux, or `.venv\Scripts\Activate.ps1` in PowerShell. From the checkout root, copy [station.example.json](06_auron_robotics/station.example.json) to `station.json`. Use the instructor's rosbridge URL and the topic names verified at your station. Ask the instructor to prepare the station configuration before enabling movement. The Thursday guide uses its own station file with the same Python environment.

## Topics

| Topic | Workshop slides |
| --- | --- |
| [01 · Python Fundamentals](01_python_fundamentals/README.md#01--python-fundamentals) | Tuesday 5–8 |
| [02 · Agentic Coding with OpenCode Desktop](02_agentic_coding/README.md#02--agentic-coding-with-opencode-desktop) | Tuesday 9–16 |
| [03 · ROS 2 Basic Concepts](03_ros2_turtlesim/README.md#03--ros-2-basic-concepts) | Tuesday 17–23 |
| [04 · Turtlesim Web Lab](03_ros2_turtlesim/README.md#04--turtlesim-web-lab) | Tuesday 24–31 |
| [05 · Control Turtlesim with Python](03_ros2_turtlesim/README.md#05--control-turtlesim-with-python) | Tuesday 32–36 |
| [06 · Robot Control and Sensing](06_auron_robotics/README.md#06--robot-control-and-sensing) | Wednesday 3–8 |
| [07 · Connect Auron to ROS MCP](07_gemma_mcp/README.md#07--connect-auron-to-ros-mcp) | Wednesday 9–12 |
| [08 · LLMs, Ollama and Gemma 4](07_gemma_mcp/README.md#08--llms-ollama-and-gemma-4) | Wednesday 13–16 |
| [09 · Build a Python Agent](07_gemma_mcp/README.md#09--build-a-python-agent) | Wednesday 17–25 |
| [10 · Map and Navigate in the Dashboard](10_mapping_navigation/README.md#10--map-and-navigate-in-the-dashboard) | Thursday 45 |
| [11 · Switch Modes and Drive in SLAM](10_mapping_navigation/README.md#11--switch-modes-and-drive-in-slam) | Thursday 46–47 |
| [12 · Program and Send a Nav2 Goal](10_mapping_navigation/README.md#12--program-and-send-a-nav2-goal) | Thursday 48 |
| [13 · Run Autonomous SLAM and Navigation Missions](10_mapping_navigation/README.md#13--run-autonomous-slam-and-navigation-missions) | Thursday 49–50 |

## 01 · Python Fundamentals

Predict and run three small Python programs. [Open the guide](01_python_fundamentals/README.md#01--python-fundamentals).

## 02 · Agentic Coding with OpenCode Desktop

Review a plan and diff, then verify a signed-speed clamp with eight tests. [Open the guide](02_agentic_coding/README.md#02--agentic-coding-with-opencode-desktop).

## 03 · ROS 2 Basic Concepts

Identify nodes and follow commands and feedback through ROS. [Open the guide](03_ros2_turtlesim/README.md#03--ros-2-basic-concepts).

## 04 · Turtlesim Web Lab

Inspect topics, services, actions and parameters in the browser. [Open the guide](03_ros2_turtlesim/README.md#04--turtlesim-web-lab).

## 05 · Control Turtlesim with Python

Subscribe to pose, send a bounded pulse and drive a route in turtlesim. [Open the guide](03_ros2_turtlesim/README.md#05--control-turtlesim-with-python).

## 06 · Robot Control and Sensing

Read sensor values, capture an RGB frame and practise supervised velocity control. [Open the guide](06_auron_robotics/README.md#06--robot-control-and-sensing).

## 07 · Connect Auron to ROS MCP

Discover tools and read a live sensor through MCP. [Open the guide](07_gemma_mcp/README.md#07--connect-auron-to-ros-mcp).

## 08 · LLMs, Ollama and Gemma 4

Run Gemma 4 locally and see when it needs live robot data. [Open the guide](07_gemma_mcp/README.md#08--llms-ollama-and-gemma-4).

## 09 · Build a Python Agent

Complete the tool-selection starter and compare camera images with odometry. [Open the guide](07_gemma_mcp/README.md#09--build-a-python-agent).

## 10–13 · Mapping, Navigation and Autonomous Agents

Map with the dashboard, switch robot modes from Python, drive in SLAM with a terminal menu, and send a Nav2 goal. Then run both autonomous missions with the Wednesday agent tools. [Open the Thursday guide](10_mapping_navigation/README.md).

## Reference and troubleshooting

- The Dev Container supplies Python, ROS 2 Jazzy, turtlesim, rosbridge, Nav2, and SLAM Toolbox. Inspect the navigation and mapping interfaces with `ros2 interface show nav2_msgs/action/NavigateToPose` and `ros2 interface show slam_toolbox/srv/SaveMap`.
- Run `ros2 node list` and `ros2 topic list` to inspect the ROS graph while turtlesim runs. The local simulator needs ports 6080 and 9090 available on the laptop. If the browser loses its connection, check the startup terminal.
- Wednesday and Thursday use the host Python environment to connect to the assigned robot.
- Maintainers can rebuild the runtime from [the Dockerfile](.devcontainer/Dockerfile) with `docker build -t auron-workshop:local .devcontainer`.
