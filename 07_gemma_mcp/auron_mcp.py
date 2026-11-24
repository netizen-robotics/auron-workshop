"""Expose the workshop's Auron operations as local MCP tools."""

from importlib import import_module
import argparse
from typing import Literal

# FastMCP exposes Python functions as tools: https://github.com/modelcontextprotocol/python-sdk
from mcp.server.fastmcp import FastMCP

auron = import_module("06_auron_robotics.auron")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--station", required=True)
    parser.add_argument("--permit", choices=("forward", "left", "stop"))
    args = parser.parse_args()
    station = auron.load_station(args.station)
    server = FastMCP("Auron Workshop")

    @server.tool()
    def list_topics() -> dict:
        """List ROS topics and message types from this Auron."""
        return auron.topics(station)

    @server.tool()
    def read_auron_sensor(sensor: str) -> dict:
        """Read one sample from a named sensor in the station inventory."""
        return auron.read_sensor(station, sensor)

    if args.permit:
        permitted = args.permit

        @server.tool()
        def move_auron(command: Literal["forward", "left", "stop"]) -> dict:
            """Execute the single workshop velocity preset already approved by the operator."""
            nonlocal permitted
            if command != permitted:
                raise ValueError("The operator did not approve this command.")
            permitted = None
            return auron.move(station, command)

    server.run(transport="stdio")


if __name__ == "__main__":
    main()
