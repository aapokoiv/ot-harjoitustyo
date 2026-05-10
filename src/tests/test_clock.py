import unittest
from unittest.mock import patch

from chess.clock import ClockState


class TestClock(unittest.TestCase):
    def test_set_remaining_clamps_negative_values_to_zero(self):
        clock = ClockState(initial_seconds=60)

        clock.set_remaining(white_time_ms=-50, black_time_ms=1250)

        self.assertEqual(clock.remaining_ms["w"], 0)
        self.assertEqual(clock.remaining_ms["b"], 1250)

    def test_pause_returns_zero_elapsed_when_clock_not_running(self):
        clock = ClockState(initial_seconds=60)

        result = clock.pause()

        self.assertEqual(result, {"timed_out": False, "elapsed_ms": 0})

    def test_pause_subtracts_elapsed_time_from_active_side(self):
        clock = ClockState(initial_seconds=10)

        with patch.object(ClockState, "_now_ms", side_effect=[1000, 1600]):
            clock.start("b")
            result = clock.pause()

        self.assertEqual(result, {"timed_out": False, "elapsed_ms": 600})
        self.assertEqual(clock.remaining_ms["b"], 9400)
        self.assertFalse(clock.running)
        self.assertIsNone(clock.last_started_at_ms)

    def test_apply_move_adds_increment_and_starts_next_side(self):
        clock = ClockState(initial_seconds=10, increment_seconds=2)

        with patch.object(ClockState, "_now_ms", side_effect=[1000, 1600, 1600]):
            clock.start("w")
            result = clock.apply_move("b")

        self.assertEqual(result, {
            "timed_out": False,
            "elapsed_ms": 600,
            "white_time_ms": 11400,
            "black_time_ms": 10000,
        })
        self.assertEqual(clock.active_side, "b")
        self.assertTrue(clock.running)

    def test_apply_move_returns_timeout_without_starting_next_side(self):
        clock = ClockState(initial_seconds=1)

        with patch.object(ClockState, "_now_ms", side_effect=[1000, 2200]):
            clock.start("w")
            result = clock.apply_move("b")

        self.assertEqual(result, {
            "timed_out": True,
            "elapsed_ms": 1200,
            "loser": "w",
            "white_time_ms": 0,
            "black_time_ms": 1000,
        })
        self.assertFalse(clock.running)
        self.assertEqual(clock.active_side, "w")

    def test_check_timeout_stops_running_clock_when_time_is_up(self):
        clock = ClockState(initial_seconds=1)

        with patch.object(ClockState, "_now_ms", side_effect=[1000, 2500]):
            clock.start("b")
            loser = clock.check_timeout()

        self.assertEqual(loser, "b")
        self.assertEqual(clock.remaining_ms["b"], 0)
        self.assertFalse(clock.running)

    def test_get_display_remaining_ms_uses_elapsed_time_only_for_active_side(self):
        clock = ClockState(initial_seconds=10)

        with patch.object(ClockState, "_now_ms", side_effect=[1000, 1450]):
            clock.start("w")
            white_remaining = clock.get_display_remaining_ms("w")

        black_remaining = clock.get_display_remaining_ms("b")

        self.assertEqual(white_remaining, 9550)
        self.assertEqual(black_remaining, 10000)
