"""Send a fixed forward, left, forward route to the local turtlesim."""

from importlib import import_module
from .turtlesim_driver import send_sequence

control = import_module("02_agentic_coding.control")


def main() -> None:
    # Convert each movement into the (forward speed, turn rate) pair expected by the publisher.
    route = []
    for movement in ("forward", "left", "forward"):
        linear, angular = control.velocity_for(movement, 0.3)
        print(f"{movement}: linear.x={linear:.2f} angular.z={angular:.2f}")
        route.append((linear, angular))
    send_sequence(route)


if __name__ == "__main__":
    try:
        main()
    except (RuntimeError, ValueError) as error:
        raise SystemExit(str(error)) from error
