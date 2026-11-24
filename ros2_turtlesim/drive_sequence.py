"""Send a fixed forward, left, forward route to the local turtlesim."""

from agentic_coding.control import velocity_for
from ros2_turtlesim.turtlesim_driver import send_sequence


def main() -> None:
    # Convert each movement into the (forward speed, turn rate) pair expected by the publisher.
    route = []
    for movement in ("forward", "left", "forward"):
        linear, angular = velocity_for(movement, 0.3)
        print(f"{movement}: linear.x={linear:.2f} angular.z={angular:.2f}")
        route.append((linear, angular))
    send_sequence(route)


if __name__ == "__main__":
    try:
        main()
    except (RuntimeError, ValueError) as error:
        raise SystemExit(str(error)) from error
