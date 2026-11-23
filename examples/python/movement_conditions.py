"""Choose the sign of the velocity from a movement label."""

movement = "reverse"
speed = 0.3

if movement == "forward":
    velocity = speed
elif movement == "reverse":
    velocity = -speed
else:
    velocity = 0.0

print(f"{movement}: linear velocity = {velocity:.2f}")
