"""Estimate how far a turtle moves at a constant speed."""

speed = 0.4
seconds = 2.0
# Speed is distance per second. Multiplying by seconds gives total distance.
# Python numbers and arithmetic: https://docs.python.org/3/tutorial/introduction.html#numbers
distance = speed * seconds
print(f"Predicted distance: {distance:.2f} units")
