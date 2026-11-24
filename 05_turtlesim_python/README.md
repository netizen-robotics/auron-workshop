# 05 · Control Turtlesim with Python

[Workshop topic index](../README.md#topics)

Run the commands from the checkout root in the workshop Dev Container. Start [Topic 04](../04_turtlesim_web/README.md) first.

Keep the browser open on `turtle1`. Use a **second** Dev Container terminal.

1. Run a native `rclpy` subscriber. In [read_turtle_pose.py](read_turtle_pose.py), find the topic, message type, and callback. Compare output with the browser pose.

   ```bash
   python -m 05_turtlesim_python.read_turtle_pose
   ```

2. Select `cmd_vel` in the browser. Publish a bounded movement pulse. The driver repeats the command briefly, then sends zero. Compare the live velocity stream and `pose` afterwards.

   ```bash
   python -m 02_agentic_coding.control forward 0.3 --turtlesim
   ```

3. Predict the path of one forward pulse, one left turn, and a second forward pulse. Read pose before and after. Try the route near the middle of the canvas with room to move.

   ```bash
   python -m 05_turtlesim_python.read_turtle_pose
   python -m 05_turtlesim_python.drive_sequence
   python -m 05_turtlesim_python.read_turtle_pose
   ```

4. Finish with the read-only rosbridge client. Read the same turtle pose through the WebSocket. From the workshop network, use the instructor-supplied Auron address to read odometry while the robot is stationary.

   ```bash
   python -m 05_turtlesim_python.read_pose turtle --url ws://127.0.0.1:9090
   python -m 05_turtlesim_python.read_pose auron --url ws://AURON_IP:9090
   ```

   Compare `turtlesim/msg/Pose` (`x`, `y`, `theta`) with `nav_msgs/msg/Odometry` (position, yaw derived from a quaternion, and frame names). Use `--topic` if the instructor supplies a namespaced odometry topic. The movement examples target local turtlesim only.
