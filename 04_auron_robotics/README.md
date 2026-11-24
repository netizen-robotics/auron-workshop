# Auron Robotics

[Workshop topic index](../README.md#topics)

Work in pairs at your assigned physical Auron. One student operates the laptop and one watches the robot and the practice area. Switch roles after the direct ROS exercise. The instructor prepares Auron in manual mode with the supported assisted-teleop path ready and checks an independent stop.

See the [host Python setup](../README.md#host-python-for-topics-0613). Run the commands from the checkout root.

## 06 · Robot Control and Sensing

```text
python -m 04_auron_robotics.auron topics
python -m 04_auron_robotics.auron inventory
python -m 04_auron_robotics.auron read battery
python -m 04_auron_robotics.auron read odometry
```

Run `python -m 04_auron_robotics.auron read NAME` for each fitted sensor listed in the [worksheet](sensor-worksheet.md). Add any extra fitted streams from the topic list to `station.json` with the instructor. Record a field, its unit, and its reading. Note the topic type and frame where available.

On the rehearsal Auron, the base IMU was on `/imu/calibrated`. The camera published separate accelerometer and gyroscope streams. The wheel message reported position and left its velocity array empty. Use the reported battery voltage for the direct and MCP comparison.

After the instructor verifies the assigned robot, manual mode, teleop path, motion limits, and independent stop, execute these **one at a time**. Read odometry before the first command and after each move.

```text
python -m 04_auron_robotics.auron move forward
python -m 04_auron_robotics.auron move left
python -m 04_auron_robotics.auron move stop
```

Review the robot URL, topic, type, linear velocity in m/s, angular velocity in rad/s, and pulse duration. Enter `MOVE` only when the spotter confirms the area is clear. The helper sends a bounded pulse and attempts to publish a zero command even if sending is interrupted. Verify the actual stop on the robot. The spotter keeps the independent stop available.

With Auron stationary, capture one RGB frame from its verified compressed color topic.

```text
python -m 04_auron_robotics.auron capture auron-rgb.jpg
```

Open the saved image and record its timestamp, dimensions, and one visible object. The capture command keeps existing files. Use a new filename for each later capture.
