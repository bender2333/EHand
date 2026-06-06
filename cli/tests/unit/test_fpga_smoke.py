from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]


class FpgaSmokeTests(unittest.TestCase):
    def test_ap_top_has_declared_clock_and_reset_ports(self) -> None:
        rtl = (ROOT / "fpga" / "rtl" / "top" / "ap_top.v").read_text(encoding="utf-8")
        testbench = (ROOT / "fpga" / "sim" / "ap_top_tb.v").read_text(encoding="utf-8")

        self.assertIn("module ap_top", rtl)
        self.assertIn("input wire i_clk", rtl)
        self.assertIn("input wire i_rst_n", rtl)
        self.assertIn(".i_clk(i_clk)", testbench)
        self.assertIn(".i_rst_n(i_rst_n)", testbench)
        self.assertIn("AP_TOP_SMOKE_PASS", testbench)


if __name__ == "__main__":
    unittest.main()
