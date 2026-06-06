"""Transport implementations.

- ReplayTransport: canonical fixture replay (implemented in daemon.replay_transport).
- UsbTransport: real hardware over the USB composite device (stub; T-06+).
- MockTransport: full-device software simulation (stub; later).
"""

from __future__ import annotations

from agentprobe.transport.base import DeviceInfo, Transport

__all__ = ["Transport", "DeviceInfo"]
