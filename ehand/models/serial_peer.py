import time
from typing import Any, Dict, List, Optional, Tuple


class SerialPeer:
    def __init__(self, channel_name: str, config: Dict[str, Any]):
        self.channel_name = channel_name
        self.baud = config.get("baud", 9600)
        self.parity = config.get("parity", "none")
        self.stop_bits = config.get("stop_bits", 1)
        self.echo = config.get("echo", False)
        self.replies: Dict[bytes, bytes] = {}
        for r in config.get("replies", []):
            req = r.get("match", "").encode("utf-8")
            resp = r.get("response", "").encode("utf-8")
            if req:
                self.replies[req] = resp

    def process_rx(self, data: bytes, injections: List[Dict[str, Any]]) -> Tuple[Optional[bytes], List[Dict[str, Any]], int]:
        """Process incoming request bytes, apply active injections, return (reply_bytes, fact_flags, latency_us)."""
        fact_flags: List[Dict[str, Any]] = []
        reply: Optional[bytes] = None
        latency_us = 1000  # nominal 1ms turnaround

        # Check matched response or echo
        if self.echo:
            reply = data
        elif data in self.replies:
            reply = self.replies[data]
        else:
            # check line-based matching if newline in data
            for match_key, resp in self.replies.items():
                if match_key in data:
                    reply = resp
                    break

        if reply is None:
            return None, fact_flags, latency_us

        # Apply Injections
        for inj in injections:
            if inj.get("channel") != self.channel_name:
                continue
            kind = inj.get("kind")
            params = inj.get("params", {})
            if kind == "drop":
                return None, fact_flags, latency_us
            elif kind == "delay":
                delay_ms = params.get("ms", 50)
                latency_us += int(delay_ms * 1000)
            elif kind == "corrupt":
                if len(reply) > 0:
                    reply = bytes([reply[0] ^ 0xFF]) + reply[1:]
                    fact_flags.append({
                        "id": f"flag_corrupt_{int(time.time()*1e6)}",
                        "kind": "injected_corruption",
                        "detail": "Reply byte corrupted by active injection",
                    })
            elif kind == "truncate":
                reply = reply[: max(1, len(reply) // 2)]

        return reply, fact_flags, latency_us
