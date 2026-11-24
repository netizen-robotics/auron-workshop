"""Reference implementation for the OpenCode exercise."""


def clamp_speed(requested: float, limit: float) -> float:
    """Keep a signed speed between -limit and +limit."""
    # Cap the positive end first, then raise anything below -limit to the lower bound.
    return max(-limit, min(requested, limit))
