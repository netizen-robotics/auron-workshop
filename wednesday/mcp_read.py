"""Call a ROS MCP tool directly from Python before using a language model."""

import argparse
import asyncio
from contextlib import asynccontextmanager
import json
from pathlib import Path
import sys

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


@asynccontextmanager
async def auron_tools(station, permit=None):
    script = Path(__file__).with_name("auron_mcp.py")
    args = [str(script), "--station", str(Path(station).resolve())]
    if permit:
        args.extend(["--permit", permit])
    server = StdioServerParameters(command=sys.executable, args=args)
    async with stdio_client(server) as (reader, writer):
        async with ClientSession(reader, writer) as session:
            await session.initialize()
            yield session


async def call(session, tool, arguments):
    print(f"MCP tool: {tool}\nInput: {json.dumps(arguments)}")
    result = await session.call_tool(tool, arguments)
    if result.isError:
        raise RuntimeError(" ".join(item.text for item in result.content if item.type == "text"))
    data = result.structuredContent
    if data is None:
        data = json.loads("".join(item.text for item in result.content if item.type == "text"))
    print("Result:", json.dumps(data, indent=2))
    return data


async def inspect(station, sensor):
    async with auron_tools(station) as session:
        print("Tools:", ", ".join(tool.name for tool in (await session.list_tools()).tools))
        if sensor:
            await call(session, "read_auron_sensor", {"sensor": sensor})
        else:
            await call(session, "list_topics", {})


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--station", default="station.json")
    parser.add_argument("--sensor")
    args = parser.parse_args()
    try:
        asyncio.run(inspect(args.station, args.sensor))
    except (OSError, ValueError, RuntimeError, ExceptionGroup) as error:
        parser.exit(1, f"{error}\n")
