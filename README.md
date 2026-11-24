# Auron Workshop · Tuesday lab

Wednesday participants can open the [Physical Auron and Gemma 4 lab](wednesday/README.md).

Learn Python, review a change in OpenCode Desktop, and control ROS 2 Jazzy turtlesim. Edit the same Git folder in VS Code and OpenCode Desktop. Run the commands in the VS Code Dev Container terminal.

## Get set up once

1. Install and start Docker Desktop (or Docker Engine on Linux). Run `docker version` in a host terminal and check for a **Server** section. [Docker setup](https://docs.docker.com/get-docker/)
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

## 1. Run three small Python programs

Predict the output, run each program, then edit one value and run it again.

| Run | Expected output | Change to try |
| --- | --- | --- |
| `python examples/python/velocity_values.py` | `Predicted distance: 0.80 units` | Change `seconds` to `3.0`. |
| `python examples/python/movement_conditions.py` | `reverse: linear velocity = -0.30` | Change `movement` to `"forward"`. |
| `python examples/python/route_functions.py` | `forward for 1.0 s`, `left for 0.5 s`, `forward for 1.0 s`, `Total: 2.5 s` | Add a right turn to the end of `route`. |

## 2. Practise agentic coding with OpenCode Desktop

OpenCode can inspect the project and edit its files. Review the plan and changes, then run the tests to verify the result.

1. Run the previews and tests in the VS Code Dev Container. Predict the correct signed speeds given a limit of `0.50`.

   ```bash
   python control.py forward 0.8
   python control.py reverse 0.8
   python -m unittest -v
   ```

   Expect `0.80` and `-0.80` in the starter previews, and two failures, `test_forward_above_limit` and `test_reverse_above_limit`.

2. Open the cloned folder in **OpenCode Desktop**. Choose **Plan** mode and ask:

   > Read control.py and test_control.py. Explain the two failing tests. Plan a change to clamp_speed that uses its supplied limit and preserves the sign. Keep the tests unchanged. Wait for review.

3. Review the plan, apply the edit with **Build**, and review the diff with `git diff -- control.py`. Rerun all three commands. Expect eight passing tests and previews with `0.50` and `-0.50`. These previews only print commands.
4. If you need to catch up, use the [reference implementation](solutions/clamp_speed.py) to replace just the `clamp_speed` function in `control.py`, then rerun the tests.

## 3. Connect the ROS 2 concepts in the browser

A node is one participant in ROS. The browser uses a WebSocket to talk to the rosbridge node, which exchanges ROS messages with the turtlesim node. A velocity command on `/turtle1/cmd_vel` asks for movement. Pose feedback on `/turtle1/pose` reports the position and heading the simulator observed.

Start the simulator in the Dev Container, and leave this terminal running.

```bash
bash .devcontainer/start-turtlesim.sh
```

Open [Turtlesim Web Lab](http://localhost:6080/) in your laptop's browser. Wait for **Connected to local rosbridge** and select **turtle1**.

| Tab | Try this | Observe |
| --- | --- | --- |
| **Topics** | Select `cmd_vel`, hold **Forward** or ↑, then release. Select `pose`. | Compare `linear.x` during movement and on release with the new pose `x`. The topic list shows the message types and directions. |
| **Services** | Choose **Set pen**, apply a new color, then drive. | Compare the request with its response, and check the trail color. |
| **Actions** | Send a `rotate_absolute` goal at 1.57 rad. When it completes, try −1.5 rad and select **Cancel rotation** while turning. | Compare feedback during rotation with the final results. |
| **Parameters** | Change one background channel to a different integer from 0 to 255. Then restore the original value. | Compare the value, type, response, and visible background. |

For more practice, inspect `color_sensor` while crossing a trail or enable `holonomic` in Parameters and try **Q** and **E** to strafe in Topics.

## 4. Control turtlesim with Python

Keep the browser open on `turtle1`. Use a **second** Dev Container terminal.

1. Run a native `rclpy` subscriber. In [read_turtle_pose.py](examples/ros/read_turtle_pose.py), find the topic, message type, and callback. Compare output with the browser pose.

   ```bash
   python -m examples.ros.read_turtle_pose
   ```

2. Select `cmd_vel` in the browser. Publish a bounded movement pulse. The driver repeats the command briefly, then sends zero. Compare the live velocity stream and `pose` afterwards.

   ```bash
   python control.py forward 0.3 --turtlesim
   ```

3. Predict the path of one forward pulse, one left turn, and a second forward pulse. Read pose before and after. Try the route near the middle of the canvas with room to move.

   ```bash
   python -m examples.ros.read_turtle_pose
   python -m examples.ros.drive_sequence
   python -m examples.ros.read_turtle_pose
   ```

4. Finish with the read-only rosbridge client. Read the same turtle pose through the WebSocket. From the workshop network, use the instructor-supplied Auron address to read odometry while the robot is stationary.

   ```bash
   python read_pose.py turtle --url ws://127.0.0.1:9090
   python read_pose.py auron --url ws://AURON_IP:9090
   ```

   Compare `turtlesim/msg/Pose` (`x`, `y`, `theta`) with `nav_msgs/msg/Odometry` (position, yaw derived from a quaternion, and frame names). Use `--topic` if the instructor supplies a namespaced odometry topic. The movement examples target local turtlesim only.

## Reference and troubleshooting

- The Dev Container supplies Python, ROS 2 Jazzy, turtlesim, rosbridge, Nav2, and SLAM Toolbox. Inspect the navigation and mapping interfaces with `ros2 interface show nav2_msgs/action/NavigateToPose` and `ros2 interface show slam_toolbox/srv/SaveMap`.
- Run `ros2 node list` and `ros2 topic list` to inspect the ROS graph while turtlesim runs. The local simulator needs ports 6080 and 9090 available on the laptop. If the browser loses its connection, check the startup terminal.
- Reuse this Dev Container and the tested clamp on Wednesday. The instructor provides the Wednesday ROS MCP guide.
- Maintainers can rebuild the runtime from [the Dockerfile](.devcontainer/Dockerfile) with `docker build -t auron-workshop:local .devcontainer`.
