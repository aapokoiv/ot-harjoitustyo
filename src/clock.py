import time
class ClockState:
    def __init__(self, initial_seconds: int, increment_seconds: int = 0):
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
        self.remaining_ms["w"] = max(0, int(white_time_ms))
        self.remaining_ms["b"] = max(0, int(black_time_ms))

    def start(self, side: str):
        self.active_side = side
        self.running = True
        self.last_started_at_ms = self._now_ms()
        
    def pause(self):
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
