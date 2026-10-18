from ehand.hardware.pcie_bridge import PcieBridge, EXPECTED_SIGNATURE


def test_pcie_bridge() -> None:
    bridge = PcieBridge()
    try:
        sig = bridge.get_signature()
        print(f"Read FPGA BAR0 signature: 0x{sig:08X}")
        assert sig == EXPECTED_SIGNATURE, f"Expected 0x{EXPECTED_SIGNATURE:08X}, got 0x{sig:08X}"
        assert bridge.is_connected() is True
        print("PCIe BAR0 Bridge to GW5AT-138 FPGA VERIFIED on real hardware!")
    finally:
        bridge.close()


if __name__ == "__main__":
    test_pcie_bridge()
