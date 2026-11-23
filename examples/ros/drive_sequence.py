"""Send a fixed forward, left, forward route to the local turtlesim."""

from control import velocity_for
from turtlesim_driver import send_sequence


def main() -> None:
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
