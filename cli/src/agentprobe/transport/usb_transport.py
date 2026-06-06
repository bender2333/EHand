"""USB transport stub — real hardware path (architecture §5.3, §9).

Implemented in T-06 (single-board bring-up). Until then it declares itself
unavailable so the engine falls back to replay/mock.
"""

from __future__ import annotations

from typing import Any, Iterator

from agentprobe.transport.base import DeviceInfo


class UsbTransport:
    def __init__(self, serial: str | None = None) -> None:
        self._serial = serial

    def info(self) -> DeviceInfo:
        raise NotImplementedError("UsbTransport is implemented in T-06 (single-board loop).")

    def request(self, msg: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError("UsbTransport is implemented in T-06 (single-board loop).")

    def stream_events(self) -> Iterator[dict[str, Any]]:
        raise NotImplementedError("UsbTransport is implemented in T-06 (single-board loop).")
        yield  # pragma: no cover - keeps this a generator

    def close(self) -> None:
        return None
