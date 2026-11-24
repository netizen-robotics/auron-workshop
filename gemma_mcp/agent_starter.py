"""Fill in the tool selection step. The shared runner handles confirmation."""

from gemma_mcp.agent import main


def select_tool(reply):
    """Return (tool_name, arguments) only when exactly one valid call exists."""
    # TODO: Find reply["tool_calls"]. Check that exactly one call was requested.
    # TODO: Read its "function" object. Return its "name" and "arguments" dict.
    # Return None for a missing or malformed call.
    return None


if __name__ == "__main__":
    main(select_tool)
