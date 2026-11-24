# 07 · Connect Auron to ROS MCP

[Workshop topic index](../README.md#topics)

Use the [host Python setup](../README.md#host-python-for-topics-0613). Run the commands from the checkout root.

**Model Context Protocol (MCP)** lets a program discover and call tools using a standard interface. [auron_mcp.py](auron_mcp.py) exposes selected Auron operations. It runs locally and connects to Auron through rosbridge. The robot's rosapi supplies topic discovery.

```text
python -m 07_ros_mcp.mcp_read
python -m 07_ros_mcp.mcp_read --sensor battery
```

Compare the MCP tool name, input and result with `python -m 06_auron_robotics.auron read battery`. Find the same topic and battery fields. The read-only tool discovery starts before the language model is introduced.
