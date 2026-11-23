"""Reference implementation for the OpenCode exercise."""


def clamp_speed(requested: float, limit: float) -> float:
    """Keep a signed speed between -limit and +limit."""
    return max(-limit, min(requested, limit))
