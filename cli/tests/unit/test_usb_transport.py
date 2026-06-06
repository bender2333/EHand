from __future__ import annotations

import unittest

from agentprobe.protocol import _generated as protocol
from agentprobe.transport.usb_transport import UsbTransport


class RecordingControlClient:
    def __init__(self, response: dict[str, object]) -> None:
        self.response = response
        self.requests: list[dict[str, object]] = []

    def request(self, msg: dict[str, object]) -> dict[str, object]:
        self.requests.append(msg)
        return self.response


class UsbTransportTests(unittest.TestCase):
    def test_info_parses_device_status_response_from_control_client(self) -> None:
        response = {
            "message_type": protocol.MSG_DEVICE_STATUS_RESPONSE,
            "status": "ok",
            "error_code": protocol.ERR_OK,
            "identity": {
                "role": "golden",
                "device_id": "golden-001",
                "serial": "SER-golden-001",
                "firmware_version": "fw-0.2.0",
                "bitstream_version": "bit-0.2.0",
            },
        }
        client = RecordingControlClient(response)

        info = UsbTransport(control_client=client).info()

        self.assertEqual(client.requests[0]["message_type"], protocol.MSG_DEVICE_STATUS_REQUEST)
        self.assertEqual(info["status"], "ok")
        self.assertEqual(info["error_code"], protocol.ERR_OK)
        self.assertEqual(info["identity"]["role"], "golden")

    def test_info_without_control_client_is_unknown_not_success(self) -> None:
        info = UsbTransport().info()

        self.assertEqual(info["status"], "unknown")
        self.assertEqual(info["error_code"], protocol.ERR_TRANSPORT_ERROR)
        self.assertNotEqual(info["verdict"], "ok")


if __name__ == "__main__":
    unittest.main()
