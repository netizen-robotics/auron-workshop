"""Convert a workshop movement request into a velocity command."""

import argparse
import math

LINEAR_LIMIT = 0.50
TURN_RATE = 1.00


def clamp_speed(requested: float, limit: float) -> float:
    """Keep a signed speed between -limit and +limit."""
    # Starter behavior. Complete this function during the OpenCode lab.
    return requested


def velocity_for(movement: str, speed: float) -> tuple[float, float]:
    """Return (linear.x, angular.z) for one movement."""
    if not math.isfinite(speed) or speed < 0:
        raise ValueError("Speed must be a finite, non-negative number.")
    if movement == "forward":
        return clamp_speed(speed, LINEAR_LIMIT), 0.0
    if movement == "reverse":
        return clamp_speed(-speed, LINEAR_LIMIT), 0.0
    if movement == "left":
        return 0.0, TURN_RATE
    if movement == "right":
        return 0.0, -TURN_RATE
    if movement == "stop":
        return 0.0, 0.0
    raise ValueError(f"Unknown movement: {movement}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("movement", choices=("forward", "reverse", "left", "right", "stop"))
    parser.add_argument("speed", type=float, nargs="?", default=0.3)
    parser.add_argument("--turtlesim", action="store_true", help="Send one pulse to local turtlesim")
    args = parser.parse_args()

    try:
        linear, angular = velocity_for(args.movement, args.speed)
        print(f"linear.x={linear:.2f} angular.z={angular:.2f}")
        if args.turtlesim:
            from turtlesim_driver import send_pulse

            send_pulse(linear, angular)
    except (RuntimeError, ValueError) as error:
        parser.exit(1, f"{error}\n")


if __name__ == "__main__":
    main()
