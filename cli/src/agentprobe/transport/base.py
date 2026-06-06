"""Transport abstraction (architecture §5.3).

USB / Replay / Mock transports share one interface. Replay parity (P3) means
the replay transport produces the same upper-layer structure as USB so that
closed-loop logic can be exercised with no hardware.
"""

from __future__ import annotations

from typing import Any, Iterator, Protocol, runtime_checkable


class DeviceInfo(dict):
    """Device identity/status surface returned by a transport."""


@runtime_checkable
class Transport(Protocol):
    """Common contract for all transports."""

    def info(self) -> DeviceInfo:
        """Return device identity/version/role/status."""
        ...

    def request(self, msg: dict[str, Any]) -> dict[str, Any]:
        """Control plane: send a request, get a response (reliable, ms-scale)."""
        ...

    def stream_events(self) -> Iterator[dict[str, Any]]:
        """Observation plane: yield events (high-throughput, loss-tolerant)."""
        ...

    def close(self) -> None:
        """Release any underlying resources."""
        ...
