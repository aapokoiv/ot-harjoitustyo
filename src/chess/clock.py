import time

### Used AI to refactor this into its own component from game.py
class ClockState:
    """Track chess clock state for both sides.

    Attributes:
        increment_ms (int): Increment added after each completed move.
        remaining_ms (dict[str, int]): Remaining time per side in milliseconds.
        active_side (str): Side whose clock is currently running.
        running (bool): Whether the clock is currently counting down.
        last_started_at_ms (int | None): Monotonic timestamp of the current run.
    """

    def __init__(self, initial_seconds: int, increment_seconds: int = 0):
        """Create a new clock state.

        Args:
            initial_seconds (int): Starting time per side in seconds.
            increment_seconds (int): Increment added after each move.
        """
        self.increment_ms = int(increment_seconds * 1000)
        base_ms = int(initial_seconds * 1000)
        self.remaining_ms = {
            "w": base_ms,
            "b": base_ms,
        }
        self.active_side = "w"
        self.running = False
        self.last_started_at_ms = None

    def set_remaining(self, *, white_time_ms: int, black_time_ms: int):
        """Replace the stored remaining time for both sides."""
        self.remaining_ms["w"] = max(0, int(white_time_ms))
        self.remaining_ms["b"] = max(0, int(black_time_ms))

    def start(self, side: str):
        """Start or resume the clock for (side)."""
        self.active_side = side
        self.running = True
        self.last_started_at_ms = self._now_ms()

    def pause(self):
        """Pause the active clock and return elapsed timing information.

        Returns:
            dict: Timing result containing (timed_out), (elapsed_ms) and
                on timeout, (loser).
        """
        if not self.running:
            return {"timed_out": False, "elapsed_ms": 0}
        elapsed_ms = self._elapsed_since_start()
        self.remaining_ms[self.active_side] -= elapsed_ms
        self.running = False
        self.last_started_at_ms = None
        if self.remaining_ms[self.active_side] <= 0:
            self.remaining_ms[self.active_side] = 0
            return {
                "timed_out": True,
                "elapsed_ms": elapsed_ms,
                "loser": self.active_side,
            }
        return {
            "timed_out": False,
            "elapsed_ms": elapsed_ms,
        }

    def apply_move(self, next_side: str):
        """Apply move completion, increment the mover, and start (next_side).

        Returns:
            dict: Timing result containing timeout status, elapsed time and the
                updated remaining clock values.
        """
        pause_result = self.pause()
        mover = self.active_side
        if pause_result["timed_out"]:
            return {
                "timed_out": True,
                "elapsed_ms": pause_result["elapsed_ms"],
                "loser": mover,
                "white_time_ms": self.remaining_ms["w"],
                "black_time_ms": self.remaining_ms["b"],
            }
        self.remaining_ms[mover] += self.increment_ms
        self.start(next_side)
        return {
            "timed_out": False,
            "elapsed_ms": pause_result["elapsed_ms"],
            "white_time_ms": self.remaining_ms["w"],
            "black_time_ms": self.remaining_ms["b"],
        }

    def check_timeout(self):
        """Return the side that has flagged, or (None) if time remains."""
        if not self.running:
            return None
        side = self.active_side
        if self.get_display_remaining_ms(side) > 0:
            return None
        self.remaining_ms[side] = 0
        self.running = False
        self.last_started_at_ms = None
        return side

    def get_display_remaining_ms(self, side: str):
        """Return remaining time for UI display.

        For the active side this includes elapsed time since the last start.
        """
        if not self.running or side != self.active_side:
            return self.remaining_ms[side]
        return max(0, self.remaining_ms[side] - self._elapsed_since_start())

    def _elapsed_since_start(self):
        if self.last_started_at_ms is None:
            return 0
        return max(0, self._now_ms() - self.last_started_at_ms)

    @staticmethod
    def _now_ms():
        return int(time.monotonic() * 1000)
