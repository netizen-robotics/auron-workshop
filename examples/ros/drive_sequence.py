"""Send a fixed forward, left, forward route to the local turtlesim."""

from control import velocity_for
from turtlesim_driver import send_pulse


def main() -> None:
    for movement in ("forward", "left", "forward"):
        linear, angular = velocity_for(movement, 0.3)
        print(f"{movement}: linear.x={linear:.2f} angular.z={angular:.2f}", flush=True)
        send_pulse(linear, angular)


if __name__ == "__main__":
    try:
        main()
    except (RuntimeError, ValueError) as error:
        raise SystemExit(str(error)) from error
