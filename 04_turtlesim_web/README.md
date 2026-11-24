# 04 · Turtlesim Web Lab

[Workshop topic index](../README.md#topics)

Run the commands from the checkout root in the workshop Dev Container.

Start the simulator in the Dev Container, and leave this terminal running.

```bash
bash 04_turtlesim_web/start-turtlesim.sh
```

Open [Turtlesim Web Lab](http://localhost:6080/) in your laptop's browser. Wait for **Connected to local rosbridge** and select **turtle1**.

| Tab | Try this | Observe |
| --- | --- | --- |
| **Topics** | Select `cmd_vel`, hold **Forward** or ↑, then release. Select `pose`. | Compare `linear.x` during movement and on release with the new pose `x`. The topic list shows the message types and directions. |
| **Services** | Choose **Set pen**, apply a new color, then drive. | Compare the request with its response, and check the trail color. |
| **Actions** | Send a `rotate_absolute` goal at 1.57 rad. When it completes, try −1.5 rad and select **Cancel rotation** while turning. | Compare feedback during rotation with the final results. |
| **Parameters** | Change one background channel to a different integer from 0 to 255. Then restore the original value. | Compare the value, type, response, and visible background. |

For more practice, inspect `color_sensor` while crossing a trail or enable `holonomic` in Parameters and try **Q** and **E** to strafe in Topics.
