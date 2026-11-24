"""Describe each step of a route and add up the movement time."""


# The function returns a formatted string. The loop decides when to print it.
# Python functions: https://docs.python.org/3/tutorial/controlflow.html#defining-functions
def describe_step(movement: str, seconds: float) -> str:
    return f"{movement} for {seconds:.1f} s"


route = [("forward", 1.0), ("left", 0.5), ("forward", 1.0)]
total_seconds = 0.0
# Unpack each (movement, duration) pair and accumulate its time.
for movement, seconds in route:
    print(describe_step(movement, seconds))
    total_seconds += seconds
print(f"Total: {total_seconds:.1f} s")
