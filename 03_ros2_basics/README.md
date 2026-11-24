# 03 · ROS 2 Basic Concepts

[Workshop topic index](../README.md#topics)

A node is one participant in ROS. The browser uses a WebSocket to talk to the rosbridge node, which exchanges ROS messages with the turtlesim node. A velocity command on `/turtle1/cmd_vel` asks for movement. Pose feedback on `/turtle1/pose` reports the position and heading the simulator observed.

| ROS concept | Example in this lab |
| --- | --- |
| Node | `turtlesim` runs the simulator. |
| Topic | `/turtle1/pose` streams position and heading. |
| Service | `/turtle1/set_pen` accepts a request and returns a response. |
| Action | `/turtle1/rotate_absolute` accepts a goal, reports feedback and returns a result. |
| Parameter | `background_r` sets the red component of the simulator background. |

Draw the path for a command and for the feedback it produces. Continue to [Topic 04](../04_turtlesim_web/README.md) to see both streams in the browser.
