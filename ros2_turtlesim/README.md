# ROS 2 and Turtlesim

[Workshop topic index](../README.md#topics)

Run the shell commands from the checkout root in the Dev Container.

## 03 · ROS 2 Basic Concepts

A node is one participant in ROS. The browser uses a WebSocket to talk to the rosbridge node, which exchanges ROS messages with the turtlesim node. A velocity command on `/turtle1/cmd_vel` asks for movement. Pose feedback on `/turtle1/pose` reports the position and heading the simulator observed.

| ROS concept | Example in this lab |
| --- | --- |
| Node | `turtlesim` runs the simulator. |
| Topic | `/turtle1/pose` streams position and heading. |
| Service | `/turtle1/set_pen` accepts a request and returns a response. |
| Action | `/turtle1/rotate_absolute` accepts a goal, reports feedback and returns a result. |
| Parameter | `background_r` sets the red component of the simulator background. |

Draw the path for a command and for the feedback it produces. Continue to [Topic 04](#04--turtlesim-web-lab) to see both streams in the browser.

## 04 · Turtlesim Web Lab

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

## 05 · Control Turtlesim with Python

Keep the browser open on `turtle1`. Use a **second** Dev Container terminal.

1. Run a native `rclpy` subscriber. In [read_turtle_pose.py](read_turtle_pose.py), find the topic, message type, and callback. Compare output with the browser pose.

   ```bash
   python -m ros2_turtlesim.read_turtle_pose
   ```

2. Select `cmd_vel` in the browser. Publish a bounded movement pulse. The driver repeats the command briefly, then sends zero. Compare the live velocity stream and `pose` afterwards.

   ```bash
   python -m agentic_coding.control forward 0.3 --turtlesim
   ```

3. Predict the path of one forward pulse, one left turn, and a second forward pulse. Read pose before and after. Try the route near the middle of the canvas with room to move.

   ```bash
   python -m ros2_turtlesim.read_turtle_pose
   python -m ros2_turtlesim.drive_sequence
   python -m ros2_turtlesim.read_turtle_pose
   ```

4. Finish with the read-only rosbridge client. Read the same turtle pose through the WebSocket. From the workshop network, use the instructor-supplied Auron address to read odometry while the robot is stationary.

   ```bash
   python -m ros2_turtlesim.read_pose turtle --url ws://127.0.0.1:9090
   python -m ros2_turtlesim.read_pose auron --url ws://AURON_IP:9090
   ```

   Compare `turtlesim/msg/Pose` (`x`, `y`, `theta`) with `nav_msgs/msg/Odometry` (position, yaw derived from a quaternion, and frame names). Use `--topic` if the instructor supplies a namespaced odometry topic. The movement examples target local turtlesim only.
