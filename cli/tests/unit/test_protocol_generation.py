from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from agentprobe.protocol import _generated as protocol

from cli.tools import generate_protocol


class ProtocolGenerationTests(unittest.TestCase):
    def test_generated_python_constants_expose_terminal_states_and_error_codes(self) -> None:
        self.assertEqual(protocol.PROTOCOL_VERSION, "0.2.0")
        self.assertEqual(protocol.TERMINAL_UNKNOWN, "unknown")
        self.assertEqual(protocol.TERMINAL_APPROVAL_PENDING, "approval_pending")
        self.assertEqual(protocol.ERR_UNKNOWN_DEVICE_IDENTITY, 103)
        self.assertEqual(protocol.ERR_APPROVAL_REQUIRED, 105)
        self.assertEqual(protocol.ERR_SAFETY_REFUSED, 106)

    def test_python_constants_are_generated_from_protocol_toml(self) -> None:
        with TemporaryDirectory() as temp:
            output = Path(temp) / "_generated.py"

            generate_protocol.write_python_constants(
                generate_protocol.load_protocol(),
                output,
            )

            spec = importlib.util.spec_from_file_location("generated_under_test", output)
            self.assertIsNotNone(spec)
            self.assertIsNotNone(spec.loader)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

        self.assertEqual(module.PROTOCOL_VERSION, "0.2.0")
        self.assertEqual(module.TERMINAL_UNKNOWN, "unknown")
        self.assertEqual(module.ERR_UNKNOWN_DEVICE_IDENTITY, 103)

    def test_firmware_shared_header_uses_generated_protocol_constants(self) -> None:
        shared_header = (generate_protocol.ROOT / "firmware" / "include" / "ap_shared.h").read_text(
            encoding="utf-8"
        )

        self.assertIn('#include "ap_protocol_generated.h"', shared_header)
        self.assertNotIn("AP_ERR_UNKNOWN_DEVICE_IDENTITY =", shared_header)

    def test_generated_firmware_header_exposes_device_status_message_types(self) -> None:
        header = (
            generate_protocol.ROOT / "firmware" / "include" / "ap_protocol_generated.h"
        ).read_text(encoding="utf-8")

        self.assertIn("AP_MSG_DEVICE_STATUS_REQUEST = 0x0001", header)
        self.assertIn("AP_MSG_DEVICE_STATUS_RESPONSE = 0x8001", header)


if __name__ == "__main__":
    unittest.main()
