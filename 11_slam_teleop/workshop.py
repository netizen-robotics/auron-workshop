"""Shared station setup and interruption handling for the Thursday labs."""

import json
import signal
from threading import Event

from websocket import WebSocketException

from .robot import Robot, station_profile


def run(parser, station, operation, *, cooperative=True):
    stopped = Event()
    previous_handler = signal.getsignal(signal.SIGINT)
    if cooperative:
        # Give a running Nav2 action time to cancel before closing its socket.
        signal.signal(signal.SIGINT, lambda *_: stopped.set())
    try:
        robot = Robot(station_profile(station), stopped.is_set)
        result = operation(robot)
        print(json.dumps(result, indent=2))
        return result
    except (EOFError, KeyboardInterrupt, OSError, ValueError, KeyError, TypeError,
            RuntimeError, ExceptionGroup, WebSocketException) as error:
        parser.exit(1, f"Stopped: {describe_error(error)}\n")
    finally:
        signal.signal(signal.SIGINT, previous_handler)


def describe_error(error):
    if isinstance(error, ExceptionGroup):
        return "; ".join(describe_error(child) for child in error.exceptions)
    return str(error) or type(error).__name__
