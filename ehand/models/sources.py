import time
from typing import Any, Dict, List, Optional, Tuple


class SwitchSource:
    def __init__(self, channel_name: str, config: Dict[str, Any]):
        self.channel_name = channel_name
        self.state = config.get("initial_state", "open").lower()
        self.bounce_ms = float(config.get("bounce_ms", 0.0))

    def set_state(self, new_state: str) -> List[Dict[str, Any]]:
        old_state = self.state
        self.state = new_state.lower()
        events = []
        now_us = int(time.time() * 1_000_000)

        # Contact bounce simulation if configured
        if self.bounce_ms > 0:
            bounce_us = int(self.bounce_ms * 1000)
            events.append({
                "time_us": now_us,
                "event": "bounce_start",
                "state": "bouncing",
            })
            now_us += bounce_us

        events.append({
            "time_us": now_us,
            "event": "state_changed",
            "old_state": old_state,
            "new_state": self.state,
        })
        return events


class PulseSource:
    def __init__(self, channel_name: str, config: Dict[str, Any]):
        self.channel_name = channel_name
        self.frequency_hz = float(config.get("frequency_hz", 100.0))
        self.duty_cycle = float(config.get("duty_cycle", 0.5))
        self.enabled = bool(config.get("enabled", True))
        self.total_pulses_emitted = 0

    def set_frequency(self, freq_hz: float) -> None:
        self.frequency_hz = max(0.1, freq_hz)

    def emit_pulses(self, count: int) -> List[Dict[str, Any]]:
        events = []
        period_us = int((1.0 / self.frequency_hz) * 1_000_000)
        high_us = int(period_us * self.duty_cycle)
        low_us = period_us - high_us

        now_us = int(time.time() * 1_000_000)
        for i in range(count):
            events.append({"time_us": now_us, "level": 1, "pulse_idx": self.total_pulses_emitted + i + 1})
            now_us += high_us
            events.append({"time_us": now_us, "level": 0, "pulse_idx": self.total_pulses_emitted + i + 1})
            now_us += low_us

        self.total_pulses_emitted += count
        return events
