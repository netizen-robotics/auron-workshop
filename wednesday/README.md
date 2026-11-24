# Wednesday lab · Physical Auron and Gemma 4

Work in pairs at your assigned physical Auron. One student operates the laptop and one watches the robot and the practice area. Switch roles after the direct ROS exercise. The instructor prepares Auron in manual mode with the supported assisted-teleop path ready and checks an independent stop.

## Set up the laptop

From the workshop checkout, open the `wednesday` folder on the laptop.

Install [uv](https://docs.astral.sh/uv/getting-started/installation/) and open this folder in your editor. Run these commands in a **host terminal**. This lab connects to the robot through its existing rosbridge.

```text
uv venv --python 3.12
uv pip install -r requirements.txt
```

Activate `.venv` with `source .venv/bin/activate` on macOS or Linux, or `.venv\Scripts\Activate.ps1` in PowerShell. Copy [station.example.json](station.example.json) to `station.json`. Use the instructor's rosbridge URL and the topic names verified at your station. Ask the instructor to prepare the station configuration before enabling movement.

## 1. Read and control Auron directly from Python

```text
python auron.py topics
python auron.py inventory
python auron.py read battery
python auron.py read odometry
```

Run `python auron.py read NAME` for each fitted sensor listed in the [worksheet](sensor-worksheet.md). Add any extra fitted streams from the topic list to `station.json` with the instructor. Record a field, its unit, and its reading. Note the topic type and frame where available.

On the rehearsal Auron, the base IMU was on `/imu/calibrated`. The camera published separate accelerometer and gyroscope streams. The wheel message reported position and left its velocity array empty. Use the reported battery voltage for the direct and MCP comparison.

After the instructor verifies the assigned robot, manual mode, teleop path, motion limits, and independent stop, execute these **one at a time**. Read odometry before the first command and after each move.

```text
python auron.py move forward
python auron.py move left
python auron.py move stop
```

Review the robot URL, topic, type, linear velocity in m/s, angular velocity in rad/s, and pulse duration. Enter `MOVE` only when the spotter confirms the area is clear. The helper sends a bounded pulse and attempts to publish a zero command even if sending is interrupted. Verify the actual stop on the robot. The spotter keeps the independent stop available.

With Auron stationary, capture one RGB frame from its verified compressed color topic.

```text
python auron.py capture auron-rgb.jpg
```

Open the saved image and record its timestamp, dimensions, and one visible object. The capture command keeps existing files. Use a new filename for each later capture.

## 2. Read a sensor through ROS MCP

**Model Context Protocol (MCP)** lets a program discover and call tools using a standard interface. [auron_mcp.py](auron_mcp.py) exposes selected Auron operations. It runs locally and connects to Auron through rosbridge. The robot's rosapi supplies topic discovery.

```text
python mcp_read.py
python mcp_read.py --sensor battery
```

Compare the MCP tool name, input and result with `python auron.py read battery`. Find the same topic and battery fields. The read-only tool discovery starts before the language model is introduced.

## 3. Use Gemma 4 locally

An **LLM** is a large language model that generates a response using the prompt and context it receives. **Gemma 4** is the model and **Ollama** is the tool that downloads and runs it. Install and start [Ollama](https://ollama.com/download) on the laptop. If the Linux service is inactive, run `ollama serve` in a separate terminal.

```text
ollama --version
ollama pull gemma4:e2b
ollama list
ollama run gemma4:e2b
```

Ask **“What is Auron's current battery reading?”** Identify the live data the model would need. Enter `/bye` to return to the shell. Pre-download the model before class. Pair up at a prepared station if needed.

## 4. Build a Python agent and describe the scene

An **agent** is a program that uses a model to decide when to request a tool. Open [agent_starter.py](agent_starter.py) and complete `select_tool`. Ollama returns a list at `reply["tool_calls"]`, and each entry contains a `function`. Return the function name and arguments only for one valid call. Return `None` for missing, malformed, or multiple calls. Compare with [the reference solution](agent.py).

```text
python agent_starter.py "What is Auron's current battery reading?"
python agent_starter.py "Go over there"
python agent_starter.py "Move forward"
```

Compare the live battery value with the earlier answer. For the ambiguous request, verify Auron stays stationary. For the explicit request, first reject at the prompt and verify it stays still. Then review and approve one pulse under supervision. Read odometry before and after. Repeat with `"Turn left"` and `"Stop"` as directed by the instructor. The reference runner accepts those three exact workshop phrases, with optional trailing punctuation.

With Auron stationary, capture a new frame and describe it.

```text
python auron.py capture auron-rgb-final.jpg
python describe_scene.py auron-rgb-final.jpg
```

Compare the description with the frame. Mark one correct object and location, and one claim you cannot verify. The vision script uses the image through local Ollama and has no ROS connection.

### Compare camera and odometry

At the supervised station, save a first image while Auron is stationary. Ask Gemma 4 what the image suggests before reviewing any movement proposal.

```text
python auron.py capture before.jpg
python vision_examples.py advise before.jpg
python agent.py "Read the current odometry from Auron."
```

Read the advice and point out what the camera cannot see. The spotter checks the practice area and the operator independently decides whether to approve the separate agent prompt. After the instructor-approved pulse and stop, record odometry again and capture the second image.

```text
python agent.py "Read the current odometry from Auron."
python auron.py capture after.jpg
python vision_examples.py compare before.jpg after.jpg
```

Find X and Y in the `odom` frame and forward speed in the twist data. Compare the measured change with the visible difference in the two frames. Both vision examples send image data only to local Ollama. The agent and its approval prompt handle any movement separately.

## Instructor demonstration · Odometry-guided left turn

Run this demonstration with the instructor’s enabled station file, the assisted-teleop path ready, and a spotter holding the independent stop. Check the full area the robot will turn through. The example caps the requested turn rate at the station setting and stops on reaching 90° in odometry. It also stops on missing or insufficient odometry or at its 14-second limit.

```text
python turn90.py station.json
```

Record `/odom` before and after, and check that Auron settles after the zero command. Watch the robot during the entire turn.

## Instructor rehearsal

Confirm the installed robot advertises the listed topic types. The current source uses `/cmd_vel_teleop` with `geometry_msgs/msg/TwistStamped`. The helper uses the robot clock from `/rosapi/get_time` to stamp commands for the motion gate. Confirm manual readiness and the assisted-teleop path in the installed release before sharing an enabled station file. Use a dedicated practice area, one active control publisher and one assigned operator per robot. Check the stop under normal operation and loss of connection before the class. Raw bridge access belongs on the controlled workshop network.

Verify the worksheet against the fitted sensors and mark unavailable streams. Test RGB capture from the actual camera. Rehearse the approved, rejected and ambiguous paths with Gemma 4 E2B, then retain one authentic screenshot of each teaching step. A successful tool result records dispatch. Students confirm actual motion and stop at the station.
