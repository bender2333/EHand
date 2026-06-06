"""Mock transport stub — full-device software simulation (architecture §5.3).

Drives a MockModel entirely in software for upper-layer development without
hardware. Implemented after the SPI mock loop (T-11).
"""

from __future__ import annotations

from typing import Any, Iterator

from agentprobe.transport.base import DeviceInfo


class MockTransport:
    def __init__(self, model: dict[str, Any] | None = None) -> None:
        self._model = model

    def info(self) -> DeviceInfo:
        raise NotImplementedError("MockTransport is implemented after the SPI mock loop (T-11).")

    def request(self, msg: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError("MockTransport is implemented after the SPI mock loop (T-11).")

    def stream_events(self) -> Iterator[dict[str, Any]]:
        raise NotImplementedError("MockTransport is implemented after the SPI mock loop (T-11).")
        yield  # pragma: no cover - keeps this a generator

    def close(self) -> None:
        return None
