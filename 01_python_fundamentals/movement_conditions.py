"""Choose the sign of the velocity from a movement label."""

movement = "reverse"
speed = 0.3

# The sign gives direction. The branches assign one velocity for the selected label.
# Python if statements: https://docs.python.org/3/tutorial/controlflow.html#if-statements
if movement == "forward":
    velocity = speed
elif movement == "reverse":
    velocity = -speed
else:
    velocity = 0.0

print(f"{movement}: linear velocity = {velocity:.2f}")
