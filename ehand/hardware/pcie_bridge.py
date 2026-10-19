import mmap
import os
import struct
import subprocess
from typing import Optional

BAR0_DEFAULT_ADDR = 0xB1000000
BAR0_SIZE = 65536
EXPECTED_SIGNATURE = 0xABCD0000


class PcieBridge:
    def __init__(self, pci_slot: str = "01:00.0", bar0_addr: int = BAR0_DEFAULT_ADDR):
        self.pci_slot = pci_slot
        self.bar0_addr = bar0_addr
        self.fd: Optional[int] = None
        self.mm: Optional[mmap.mmap] = None
        self._ensure_pci_enabled()
        self._map()

    def _ensure_pci_enabled(self) -> None:
        """Enable Memory Space & Bus Master in PCI command register."""
        sysfs_enable = f"/sys/bus/pci/devices/0000:{self.pci_slot}/enable"
        if os.path.exists(sysfs_enable):
            try:
                with open(sysfs_enable, "w") as f:
                    f.write("1\n")
            except Exception:
                pass
        try:
            subprocess.run(
                ["setpci", "-s", self.pci_slot, "COMMAND=0x0002"],
                check=False,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except Exception:
            pass

    def _map(self) -> None:
        try:
            self.fd = os.open("/dev/mem", os.O_RDWR | os.O_SYNC)
            self.mm = mmap.mmap(
                self.fd,
                BAR0_SIZE,
                mmap.MAP_SHARED,
                mmap.PROT_READ | mmap.PROT_WRITE,
                offset=self.bar0_addr,
            )
        except Exception as e:
            if self.fd is not None:
                os.close(self.fd)
                self.fd = None
            raise RuntimeError(f"Failed to map FPGA BAR0 at 0x{self.bar0_addr:08X}: {e}")

    def read32(self, offset: int) -> int:
        if self.mm is None:
            raise RuntimeError("PCIe BAR0 not mapped")
        if offset < 0 or offset + 4 > BAR0_SIZE:
            raise IndexError("Offset out of BAR0 range")
        return struct.unpack("<I", self.mm[offset : offset + 4])[0]

    def write32(self, offset: int, value: int) -> None:
        if self.mm is None:
            raise RuntimeError("PCIe BAR0 not mapped")
        if offset < 0 or offset + 4 > BAR0_SIZE:
            raise IndexError("Offset out of BAR0 range")
        self.mm[offset : offset + 4] = struct.pack("<I", value & 0xFFFFFFFF)

    def get_signature(self) -> int:
        return self.read32(0x00)

    def is_connected(self) -> bool:
        try:
            sig = self.get_signature()
            return (sig & 0xFFFF0000) == EXPECTED_SIGNATURE
        except Exception:
            return False

    def close(self) -> None:
        if self.mm is not None:
            self.mm.close()
            self.mm = None
        if self.fd is not None:
            os.close(self.fd)
            self.fd = None
