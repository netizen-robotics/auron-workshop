# Gemma 4 and ROS MCP

[Workshop topic index](../README.md#topics)

Use the [host Python setup](../README.md#host-python-for-topics-0609) on your laptop. Run all Python commands from the checkout root.

## 07 · Connect Auron to ROS MCP

**Model Context Protocol (MCP)** lets a program discover and call tools using a standard interface. [auron_mcp.py](auron_mcp.py) exposes selected Auron operations. It runs locally and connects to Auron through rosbridge. The robot's rosapi supplies topic discovery.

```text
python -m 05_gemma_mcp.mcp_read
python -m 05_gemma_mcp.mcp_read --sensor battery
```

Compare the MCP tool name, input and result with `python -m 04_auron_robotics.auron read battery`. Find the same topic and battery fields. The read-only tool discovery starts before the language model is introduced.

## 08 · LLMs, Ollama and Gemma 4

An **LLM** is a large language model that generates a response using the prompt and context it receives. **Gemma 4** is the model and **Ollama** is the tool that downloads and runs it. Install and start [Ollama](https://ollama.com/download) on the laptop. If the Linux service is inactive, run `ollama serve` in a separate terminal.

```text
ollama --version
ollama pull gemma4:e2b
ollama list
ollama run gemma4:e2b
```

Ask **“What is Auron's current battery reading?”** Identify the live data the model would need. Enter `/bye` to return to the shell. Pre-download the model before class. Pair up at a prepared station if needed.

## 09 · Build a Python Agent

An **agent** is a program that uses a model to decide when to request a tool. Open [agent_starter.py](agent_starter.py) and complete `select_tool`. Ollama returns a list at `reply["tool_calls"]`, and each entry contains a `function`. Return the function name and arguments only for one valid call. Return `None` for missing, malformed, or multiple calls. Compare with [the reference solution](agent.py).

```text
python -m 05_gemma_mcp.agent_starter "What is Auron's current battery reading?"
python -m 05_gemma_mcp.agent_starter "Go over there"
python -m 05_gemma_mcp.agent_starter "Move forward"
```

Compare the live battery value with the earlier answer. For the ambiguous request, verify Auron stays stationary. For the explicit request, first reject at the prompt and verify it stays still. Then review and approve one pulse under supervision. Read odometry before and after. Repeat with `"Turn left"` and `"Stop"` as directed by the instructor. The reference runner accepts those three exact workshop phrases, with optional trailing punctuation.

With Auron stationary, capture a new frame and describe it.

```text
python -m 04_auron_robotics.auron capture auron-rgb-final.jpg
python -m 05_gemma_mcp.describe_scene auron-rgb-final.jpg
```

Compare the description with the frame. Mark one correct object and location, and one claim you cannot verify. The vision script uses the image through local Ollama and has no ROS connection.

### Compare camera and odometry

At the supervised station, save a first image while Auron is stationary. Ask Gemma 4 what the image suggests before reviewing any movement proposal.

```text
python -m 04_auron_robotics.auron capture before.jpg
python -m 05_gemma_mcp.vision_examples advise before.jpg
python -m 05_gemma_mcp.agent "Read the current odometry from Auron."
```

Read the advice and point out what the camera cannot see. The spotter checks the practice area and the operator independently decides whether to approve the separate agent prompt. After the instructor-approved pulse and stop, record odometry again and capture the second image.

```text
python -m 05_gemma_mcp.agent "Read the current odometry from Auron."
python -m 04_auron_robotics.auron capture after.jpg
python -m 05_gemma_mcp.vision_examples compare before.jpg after.jpg
```

Find X and Y in the `odom` frame and forward speed in the twist data. Compare the measured change with the visible difference in the two frames. Both vision examples send image data only to local Ollama. The agent and its approval prompt handle any movement separately.

## Instructor demonstration · Odometry-guided left turn

Run this demonstration with the instructor’s enabled station file, the assisted-teleop path ready, and a spotter holding the independent stop. Check the full area the robot will turn through. The example caps the requested turn rate at the station setting and stops on reaching 90° in odometry. It also stops on missing or insufficient odometry or at its 14-second limit.

```text
python -m 05_gemma_mcp.turn90 station.json
```

Record `/odom` before and after, and check that Auron settles after the zero command. Watch the robot during the entire turn.

## Instructor rehearsal

Confirm the installed robot advertises the listed topic types. The current source uses `/cmd_vel_teleop` with `geometry_msgs/msg/TwistStamped`. The helper uses the robot clock from `/rosapi/get_time` to stamp commands for the motion gate. Confirm manual readiness and the assisted-teleop path in the installed release before sharing an enabled station file. Use a dedicated practice area, one active control publisher and one assigned operator per robot. Check the stop under normal operation and loss of connection before the class. Raw bridge access belongs on the controlled workshop network.

Verify the worksheet against the fitted sensors and mark unavailable streams. Test RGB capture from the actual camera. Rehearse the approved, rejected and ambiguous paths with Gemma 4 E2B, then retain one authentic screenshot of each teaching step. A successful tool result records dispatch. Students confirm actual motion and stop at the station.
