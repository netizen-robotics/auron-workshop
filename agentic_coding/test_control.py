# unittest compares actual outputs with expected values: https://docs.python.org/3/library/unittest.html
import unittest

from agentic_coding.control import clamp_speed, velocity_for


class SpeedLimitTests(unittest.TestCase):
    def test_speed_inside_limit(self):
        self.assertEqual(clamp_speed(0.0, 0.5), 0.0)
        self.assertEqual(clamp_speed(0.25, 0.5), 0.25)
        self.assertEqual(clamp_speed(-0.25, 0.5), -0.25)

    def test_exact_limits(self):
        self.assertEqual(clamp_speed(0.5, 0.5), 0.5)
        self.assertEqual(clamp_speed(-0.5, 0.5), -0.5)

    # Test an over-limit request in each direction, including a different supplied limit.
    def test_forward_above_limit(self):
        self.assertEqual(velocity_for("forward", 0.8), (0.5, 0.0))
        self.assertEqual(clamp_speed(0.8, 0.3), 0.3)

    def test_reverse_above_limit(self):
        self.assertEqual(velocity_for("reverse", 0.8), (-0.5, 0.0))
        self.assertEqual(clamp_speed(-0.8, 0.3), -0.3)

    def test_custom_limit(self):
        self.assertEqual(clamp_speed(0.2, 0.3), 0.2)
        self.assertEqual(clamp_speed(-0.3, 0.3), -0.3)

    def test_left_and_right(self):
        self.assertEqual(velocity_for("left", 0.3), (0.0, 1.0))
        self.assertEqual(velocity_for("right", 0.3), (0.0, -1.0))

    def test_stop(self):
        self.assertEqual(velocity_for("stop", 0.3), (0.0, 0.0))

    def test_invalid_request(self):
        for speed in (-0.3, float("nan"), float("inf")):
            with self.subTest(speed=speed), self.assertRaises(ValueError):
                velocity_for("forward", speed)


if __name__ == "__main__":
    unittest.main()
