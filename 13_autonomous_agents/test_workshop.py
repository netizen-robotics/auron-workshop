"""Verify the Thursday controls and MCP mission loops without a physical robot."""

from collections import deque
from contextlib import nullcontext, redirect_stdout
from copy import deepcopy
from importlib import import_module
import io
import json
import math
from pathlib import Path
from time import monotonic
import unittest
from unittest.mock import Mock, patch

from websocket import WebSocketConnectionClosedException

from . import mission
from .mission import lidar_summary, run_mission

robot = import_module("11_slam_teleop.robot")
workshop = import_module("11_slam_teleop.workshop")
ASSIST, NAVIGATE, STATUS, SWITCH = robot.ASSIST, robot.NAVIGATE, robot.STATUS, robot.SWITCH
Robot, UnknownStop = robot.Robot, robot.UnknownStop
reference_pose, reference_switch = robot.reference_pose, robot.reference_switch
describe_error = workshop.describe_error

EXAMPLE = json.loads(Path(robot.__file__).with_name("station.example.json").read_text())
READY = {"active_mode": "mapping", "requested_mode": "mapping", "state": "idle", "nav_ready": True}


def station():
    return dict(deepcopy(EXAMPLE), enabled=True)


def scan(distance=1):
    return {"header": {"frame_id": "laser_link"}, "angle_min": -math.pi,
            "angle_increment": math.tau / 360, "range_min": 0.1, "range_max": 10,
            "ranges": [distance] * 360}


def odom(x=0):
    return {"pose": {"pose": {"position": {"x": x, "y": 0},
            "orientation": {"x": 0, "y": 0, "z": 0, "w": 1}}}}


def choose(name, **arguments):
    return {"tool_calls": [{"function": {"name": name, "arguments": arguments}}]}


class Socket:
    def __init__(self, *responses):
        self.responses = deque(responses)
        self.sent = []

    def send(self, message):
        self.sent.append(json.loads(message))

    def recv(self):
        item = self.responses.popleft()
        if isinstance(item, BaseException):
            raise item
        first = self.sent[0]
        return json.dumps({"id": first["id"], "action": first["action"], **item})

    def settimeout(self, timeout):
        pass


class RobotTests(unittest.TestCase):
    def setUp(self):
        self.robot = Robot(station())

    def test_switch_waits_for_matching_mode_and_preserves_pose_step(self):
        self.robot.service = Mock(return_value={"success": True})
        pose_pending = dict(READY, active_mode="nav", requested_mode="nav", nav_ready=False)
        self.robot.status = Mock(side_effect=[dict(READY, state="switching"), pose_pending])
        self.assertEqual(self.robot.mode("nav", reference_switch), pose_pending)
        self.assertEqual(self.robot.service.call_args.args[:3], (
            SWITCH, "auron_interfaces/srv/SwitchRobotMode",
            {"mode": "nav", "map_path": EXAMPLE["nav"]["map_path"]},
        ))
        with self.assertRaisesRegex(RuntimeError, "not ready"):
            self.robot.status = Mock(return_value=pose_pending)
            self.robot.require_ready("nav", monotonic() + 1)

    def test_switch_mapping_has_no_map_path(self):
        self.robot.service = Mock(return_value={"success": True})
        self.robot.status = Mock(return_value=READY)
        self.robot.mode("mapping", reference_switch)
        self.assertEqual(self.robot.service.call_args.args[2], {"mode": "mapping", "map_path": ""})

    def test_stale_mode_status_is_ignored(self):
        def message(seconds):
            return {"op": "publish", "topic": STATUS,
                    "msg": {**READY, "stamp": {"sec": seconds, "nanosec": 0}}}
        socket = Mock()
        socket.recv.side_effect = map(json.dumps, [message(96), message(100)])
        self.robot.connect = Mock(return_value=nullcontext(socket))
        with patch.object(robot.auron, "robot_clock", return_value=lambda: {"sec": 100, "nanosec": 0}):
            self.assertEqual(self.robot.status(monotonic() + 1)["stamp"]["sec"], 100)

    def test_assisted_pulse_sends_zero_and_cancels(self):
        action = Socket({"op": "action_feedback"}, {"op": "action_result", "status": 5, "result": True})
        velocity = Mock()
        self.robot.connect = Mock(side_effect=[nullcontext(action), nullcontext(velocity)])
        self.robot.status = Mock(return_value=READY)
        self.robot.station["mapping"]["pulse_s"] = 0.001
        with patch.object(robot.auron, "robot_clock", return_value=lambda: {"sec": 1, "nanosec": 0}):
            self.assertTrue(self.robot.drive("right", monotonic() + 1)["zero_sent"])
        self.assertEqual(action.sent[0]["action"], ASSIST)
        wire = [json.loads(record.args[0]) for record in velocity.send.call_args_list]
        self.assertLess(wire[1]["msg"]["twist"]["angular"]["z"], 0)
        self.assertEqual(wire[-1]["msg"]["twist"]["angular"]["z"], 0)
        self.assertEqual(action.sent[-1]["op"], "cancel_action_goal")

    def test_mode_mismatch_and_unknown_checkpoint_dispatch_nothing(self):
        self.robot.status = Mock(return_value=READY)
        self.robot.action = Mock()
        with self.assertRaisesRegex(ValueError, "Unknown checkpoint"):
            self.robot.navigate("Garage", reference_pose, monotonic() + 1)
        with self.assertRaisesRegex(RuntimeError, "not ready"):
            self.robot.navigate("A", reference_pose, monotonic() + 1)
        self.robot.action.assert_not_called()

    def test_goal_pose_and_result(self):
        self.robot.status = Mock(return_value=dict(READY, active_mode="nav", requested_mode="nav"))
        action = Socket({"op": "action_result", "status": 4, "result": True, "values": {"error_code": 0}})
        self.robot.connect = Mock(return_value=nullcontext(action))
        result = self.robot.navigate("B", reference_pose, monotonic() + 1)
        self.assertEqual(result["status"], "succeeded")
        self.assertEqual(action.sent[0]["action"], NAVIGATE)
        pose = action.sent[0]["args"]["pose"]
        self.assertEqual(pose["header"]["frame_id"], "map")
        self.assertAlmostEqual(pose["pose"]["orientation"]["z"], math.sqrt(0.5))
        self.assertAlmostEqual(pose["pose"]["orientation"]["w"], math.sqrt(0.5))

    def test_aborted_goal_is_not_success(self):
        socket = Socket({"op": "action_result", "status": 6, "result": True, "values": {"error_code": 4}})
        self.robot.connect = Mock(return_value=nullcontext(socket))
        with self.assertRaisesRegex(RuntimeError, "did not succeed"):
            self.robot.action(NAVIGATE, "nav", {}, monotonic() + 1)

    def test_interrupt_cancels_goal(self):
        socket = Socket(KeyboardInterrupt(), {"op": "action_result", "status": 5, "result": True})
        self.robot.connect = Mock(return_value=nullcontext(socket))
        with self.assertRaises(KeyboardInterrupt):
            self.robot.action(NAVIGATE, "nav", {}, monotonic() + 1)
        self.assertEqual(socket.sent[1]["id"], socket.sent[0]["id"])
        self.assertEqual(socket.sent[1]["op"], "cancel_action_goal")

    def test_disconnect_reports_unknown_stop(self):
        failure = WebSocketConnectionClosedException("connection lost")
        socket = Socket(failure, failure)
        self.robot.connect = Mock(return_value=nullcontext(socket))
        with self.assertRaisesRegex(UnknownStop, "termination unconfirmed"):
            self.robot.action(NAVIGATE, "nav", {}, monotonic() + 1)
        self.assertEqual(socket.sent[1]["op"], "cancel_action_goal")

    def test_goal_timeout_requests_cancellation(self):
        socket = Socket({"op": "action_result", "status": 5, "result": True})
        self.robot.connect = Mock(return_value=nullcontext(socket))
        with patch.object(robot, "packet", side_effect=[TimeoutError("goal timed out"),
                                                {"status": 5, "result": True}]):
            with self.assertRaisesRegex(TimeoutError, "goal timed out"):
                self.robot.action(NAVIGATE, "nav", {}, monotonic() + 1)
        self.assertEqual(socket.sent[1]["op"], "cancel_action_goal")

    def test_save_map_uses_a_team_path(self):
        self.robot.status = Mock(return_value=READY)
        self.robot.service = Mock(return_value={"result": 0})
        with self.assertRaises(ValueError):
            self.robot.save_map("../map")
        self.assertEqual(self.robot.save_map("practice")["map_path"], "/share/auron/practice.yaml")
        self.assertEqual(self.robot.service.call_args.args[2], {"name": {"data": "/share/auron/practice"}})


class MissionTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.robot = Robot(station())
        self.robot.require_ready = Mock(side_effect=lambda mode, deadline: dict(READY, active_mode=mode))
        self.robot.drive = Mock(return_value={"zero_sent": True})
        self.robot.navigate = Mock(side_effect=lambda name, pose, deadline: {"checkpoint": name, "status": "succeeded"})
        self.odom_updates = iter([odom(), odom(0.03), odom(0.03), odom(0.06)])

        def read(topic, deadline):
            if topic == "/map":
                return {"header": {"frame_id": "map"}, "info": {"width": 2, "height": 2},
                        "data": [-1, 0, 0, 100]}
            if topic == "/scan":
                return scan()
            if topic == "/odom":
                return next(self.odom_updates)
            raise AssertionError(topic)

        self.robot.read = Mock(side_effect=read)

    async def run_agent(self, mode, *decisions):
        with redirect_stdout(io.StringIO()):
            return await run_mission(self.robot, mode, "Practice mission", reference_pose,
                                     ask_model=Mock(side_effect=decisions))

    async def test_mapping_observes_moves_and_finishes(self):
        result = await self.run_agent("mapping", choose("mapping_move", direction="forward"), choose("finish"))
        self.assertEqual((result["ended"], result["steps"]), ("agent_finished", 1))
        self.assertAlmostEqual(result["results"][0]["odom_distance_m"], 0.03)
        self.robot.drive.assert_called_once()

    async def test_navigation_visits_two_points_autonomously(self):
        result = await self.run_agent("nav", choose("navigation_goal", checkpoint="B"),
                                      choose("navigation_goal", checkpoint="A"))
        self.assertEqual(result["ended"], "checkpoints_complete")
        self.assertEqual([entry["checkpoint"] for entry in result["results"]], ["B", "A"])

    async def test_step_limit(self):
        self.robot.station["mapping"]["max_steps"] = 1
        result = await self.run_agent("mapping", choose("mapping_move", direction="forward"))
        self.assertEqual((result["ended"], result["steps"]), ("step_limit", 1))

    async def test_timeout_blocks_dispatch(self):
        with patch.object(mission, "choose", side_effect=TimeoutError):
            result = await self.run_agent("mapping", choose("mapping_move", direction="forward"))
        self.assertEqual((result["ended"], result["steps"]), ("time_limit", 0))
        self.robot.drive.assert_not_called()

    async def test_model_cannot_invent_coordinates_or_issue_multiple_calls(self):
        for reply in (choose("navigation_goal", checkpoint="Garage"), {"tool_calls": [{}, {}]}):
            with self.assertRaises(ExceptionGroup) as failure:
                await self.run_agent("nav", reply)
            self.assertRegex(describe_error(failure.exception), "mission|Mission")
        self.robot.navigate.assert_not_called()

    async def test_missing_observation_ends_run(self):
        self.robot.read = Mock(side_effect=TimeoutError("Missing live observation"))
        with self.assertRaises(ExceptionGroup) as failure:
            await self.run_agent("mapping", {})
        self.assertIn("Missing live observation", describe_error(failure.exception))
        self.robot.drive.assert_not_called()

    async def test_failed_goal_does_not_continue(self):
        self.robot.navigate.side_effect = RuntimeError("Nav2 aborted")
        with self.assertRaises(ExceptionGroup) as failure:
            await self.run_agent("nav", choose("navigation_goal", checkpoint="A"),
                                 choose("navigation_goal", checkpoint="B"))
        self.assertIn("Nav2 aborted", describe_error(failure.exception))
        self.robot.navigate.assert_called_once()

    def test_scan_missing_quadrant_is_rejected(self):
        incomplete = scan()
        incomplete["ranges"][140:225] = [None] * 85
        incomplete["ranges"][135:140] = [None] * 5
        incomplete["ranges"][225] = None
        with self.assertRaisesRegex(ValueError, "missing"):
            lidar_summary(incomplete, 0, "laser_link")


if __name__ == "__main__":
    unittest.main()
