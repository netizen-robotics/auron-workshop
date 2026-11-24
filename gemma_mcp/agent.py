"""Reference solution for a local Gemma 4 agent with one reviewed MCP tool call."""

import argparse
import asyncio
import re

from auron_robotics.auron import confirmed, load_station, motion_plan
from gemma_mcp.gemma import MODEL, ask
from gemma_mcp.mcp_read import auron_tools, call

CONTROL_REQUESTS = {"move forward": "forward", "turn left": "left", "stop": "stop"}
# These schemas tell Ollama which tool names and arguments the model may propose.
TOOLS = [
    {"type": "function", "function": {
        "name": "read_auron_sensor",
        "description": "Read live Auron battery or odometry. Use battery for questions about current charge.",
        "parameters": {"type": "object", "required": ["sensor"], "additionalProperties": False,
                       "properties": {"sensor": {"type": "string", "enum": ["battery", "odometry"]}}}
    }},
    {"type": "function", "function": {
        "name": "move_auron",
        "description": "Propose exactly one workshop preset for a clear request. It needs human approval.",
        "parameters": {"type": "object", "required": ["command"], "additionalProperties": False,
                       "properties": {"command": {"type": "string", "enum": ["forward", "left", "stop"]}}}
    }},
]


def select_tool(reply):
    """Extract a single named tool and arguments, leaving execution to the caller."""
    calls = reply.get("tool_calls", [])
    if not isinstance(calls, list) or len(calls) != 1 or not isinstance(calls[0], dict):
        return None
    function = calls[0].get("function")
    if (not isinstance(function, dict) or not isinstance(function.get("name"), str)
            or not isinstance(function.get("arguments"), dict)):
        return None
    return function["name"], function["arguments"]


async def run(station_path, model, request, choose_tool):
    station = load_station(station_path)
    messages = [
        {"role": "system", "content": "You assist beginners with physical Auron. Use one tool at most. "
         "Read live data for current sensor questions. Propose movement only for an explicit "
         "forward, left, or stop request. Ask for clarification if the request is ambiguous."},
        {"role": "user", "content": request},
    ]
    reply = ask(messages, model=model, tools=TOOLS)
    selection = choose_tool(reply)
    if selection is None:
        if reply.get("content"):
            print(reply["content"])
        print("No single tool selected. For motion, use 'Move forward', 'Turn left' or 'Stop'.")
        return
    tool, arguments = selection
    if tool == "read_auron_sensor" and arguments in ({"sensor": "battery"}, {"sensor": "odometry"}):
        async with auron_tools(station_path) as session:
            await call(session, tool, arguments)
        return

    # Check the original request and the proposed preset before asking for human approval.
    command = CONTROL_REQUESTS.get(re.sub(r"[.!?]+$", "", request.strip().casefold()))
    if tool != "move_auron" or command is None or arguments != {"command": command}:
        print("No movement sent. A single explicit workshop command is required.")
        return

    print("Proposed MCP tool: move_auron")
    if not confirmed(motion_plan(station, command)):
        print("Cancelled. No movement sent.")
        return
    # This server process accepts just the reviewed movement preset for one call.
    async with auron_tools(station_path, permit=command) as session:
        await call(session, tool, arguments)


def main(choose_tool=select_tool):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("request")
    parser.add_argument("--station", default="station.json")
    parser.add_argument("--model", default=MODEL)
    args = parser.parse_args()
    try:
        asyncio.run(run(args.station, args.model, args.request, choose_tool))
    except (OSError, EOFError, ValueError, KeyError, RuntimeError, ExceptionGroup) as error:
        parser.exit(1, f"{error}\n")


if __name__ == "__main__":
    main()
