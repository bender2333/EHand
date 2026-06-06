"""USB transport stub — real hardware path (architecture §5.3, §9).

Implemented in T-06 (single-board bring-up). Until then it declares itself
unavailable so the engine falls back to replay/mock.
"""

from __future__ import annotations

from typing import Any, Iterator, Protocol

from agentprobe.transport.base import DeviceInfo
from agentprobe.protocol import _generated as protocol


class ControlClient(Protocol):
    def request(self, msg: dict[str, Any]) -> dict[str, Any]:
        ...


class UsbTransport:
    def __init__(self, serial: str | None = None, control_client: ControlClient | None = None) -> None:
        self._serial = serial
        self._control_client = control_client

    def info(self) -> DeviceInfo:
        if self._control_client is None:
            return DeviceInfo(
                {
                    "status": "unknown",
                    "error_code": protocol.ERR_TRANSPORT_ERROR,
                    "verdict": "USB control transport is not connected",
                }
            )

        response = self._control_client.request(
            {
                "message_type": protocol.MSG_DEVICE_STATUS_REQUEST,
                "serial": self._serial,
            }
        )
        if response.get("message_type") != protocol.MSG_DEVICE_STATUS_RESPONSE:
            return DeviceInfo(
                {
                    "status": "unknown",
                    "error_code": protocol.ERR_TRANSPORT_ERROR,
                    "verdict": "USB device status response had an unexpected message type",
                }
            )
        return DeviceInfo(response)

    def request(self, msg: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError("UsbTransport is implemented in T-06 (single-board loop).")

    def stream_events(self) -> Iterator[dict[str, Any]]:
        raise NotImplementedError("UsbTransport is implemented in T-06 (single-board loop).")
        yield  # pragma: no cover - keeps this a generator

    def close(self) -> None:
        return None
