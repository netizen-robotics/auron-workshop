# Auron station worksheet

Station ________   Pair ________   Date ________

Record one sample for each fitted sensor. Use the topic list to add streams specific to this robot. Topic names below are starting points to check against the installed runtime. If a stream is absent, record what is missing and ask the instructor.

| Sensor or feedback | Topic to verify | Fields and units to find | Topic type, sample and frame |
| --- | --- | --- | --- |
| LiDAR | `/scan` | nearest valid range (m), scan angle (rad) | |
| Base IMU | `/imu/calibrated` | acceleration (m/s²), angular velocity (rad/s) | |
| Wheel or joint feedback | `/joint_states` | wheel position (rad), wheel speed (rad/s) if published | |
| Battery | `/battery_level_broadcaster/battery_state` | voltage (V), percentage if the driver supplies it | |
| Odometry | `/odom` | X and Y (m), forward speed (m/s), reference frame | |
| Depth camera | `/camera/depth/image_raw` | width and height (px), encoding | |
| RGB camera | `/camera/color/image_raw/compressed` | dimensions (px), capture timestamp and visible object | |
| Camera accelerometer | `/camera/accel/sample` | acceleration (m/s²) | |
| Camera gyroscope | `/camera/gyro/sample` | angular velocity (rad/s) | |
| Other fitted stream | | | |

| Exercise | Starting reading | Command or tool and arguments | Observed outcome and final reading |
| --- | --- | --- | --- |
| Direct velocity | | | |
| MCP battery read | | | |
| Rejected agent proposal | | | |
| Approved agent command | | | |
| Gemma 4 image description | Image filename | | One verified detail and one uncertain claim |
