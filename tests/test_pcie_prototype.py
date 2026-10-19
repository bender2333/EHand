import subprocess
import time

from ehand.hardware.pcie_bridge import PcieBridge, EXPECTED_SIGNATURE


def test_pcie_hardware_registers() -> None:
    bridge = PcieBridge()
    try:
        sig = bridge.get_signature()
        assert (sig & 0xFFFF0000) == EXPECTED_SIGNATURE, f"Unexpected signature: 0x{sig:08X}"
        print(f"[OK] Signature verified: 0x{sig:08X}")

        # Test writing pattern to channel switch register (offset 0x04)
        test_patterns = [0x00010001, 0x12345678, 0x55AA55AA, 0x00000000]
        for pattern in test_patterns:
            bridge.write32(0x04, pattern)
            readback = bridge.read32(0x04)
            assert readback == pattern, f"Mismatch at 0x04: wrote 0x{pattern:08X}, read 0x{readback:08X}"
        print(f"[OK] BAR0 0x04 register write/read verified across all patterns")

        # Test writing pattern to interrupt enable register (offset 0x08)
        for pattern in [0x00000001, 0x000000FF, 0x00000000]:
            bridge.write32(0x08, pattern)
            readback = bridge.read32(0x08)
            assert readback == pattern, f"Mismatch at 0x08: wrote 0x{pattern:08X}, read 0x{readback:08X}"
        print(f"[OK] BAR0 0x08 register write/read verified across all patterns")

    finally:
        bridge.close()


def test_pcie_dma_hardware() -> None:
    # Run official DMA round-trip test binary
    res = subprocess.run(
        ["/root/.hermes/cache/scratch/test_gw_ioctl"],
        capture_output=True,
        text=True,
        check=True,
    )
    assert "timeout count: 0" in res.stdout, f"DMA test failed: {res.stdout}"
    assert "Speed:" in res.stdout, f"DMA test no speed reported: {res.stdout}"
    print(f"[OK] PCIe SGDMA hardware loopback verified:\n{res.stdout.strip()}")


if __name__ == "__main__":
    print("=== Running PCIe Hardware Prototype Tests ===")
    test_pcie_hardware_registers()
    test_pcie_dma_hardware()
    print("=== ALL PCIE HARDWARE PROTOTYPE CHECKS PASSED ===")
