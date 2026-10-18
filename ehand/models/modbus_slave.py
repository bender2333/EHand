import struct
import time
from typing import Any, Dict, List, Optional, Tuple


def compute_crc16(data: bytes) -> Tuple[int, int]:
    """Calculate Modbus CRC16. Returns (low_byte, high_byte)."""
    crc = 0xFFFF
    for b in data:
        crc ^= b
        for _ in range(8):
            if crc & 1:
                crc = (crc >> 1) ^ 0xA001
            else:
                crc >>= 1
    return crc & 0xFF, (crc >> 8) & 0xFF


def verify_crc16(frame: bytes) -> bool:
    if len(frame) < 3:
        return False
    payload = frame[:-2]
    expected_low, expected_high = compute_crc16(payload)
    return frame[-2] == expected_low and frame[-1] == expected_high


class ModbusSlave:
    def __init__(self, channel_name: str, config: Dict[str, Any]):
        self.channel_name = channel_name
        self.slave_id = config.get("slave_id", 1)
        self.holding_registers: Dict[int, int] = {}
        for addr_str, val in config.get("holding_registers", {}).items():
            self.holding_registers[int(addr_str)] = int(val)
        self.coils: Dict[int, bool] = {}
        for addr_str, val in config.get("coils", {}).items():
            self.coils[int(addr_str)] = bool(val)

    def _build_exception(self, fc: int, code: int) -> bytes:
        pdu = bytes([self.slave_id, fc | 0x80, code])
        c_lo, c_hi = compute_crc16(pdu)
        return pdu + bytes([c_lo, c_hi])

    def process_rx(self, frame: bytes, injections: List[Dict[str, Any]]) -> Tuple[Optional[bytes], List[Dict[str, Any]], int]:
        fact_flags: List[Dict[str, Any]] = []
        latency_us = 2000  # nominal 2ms slave turnaround

        if len(frame) < 4:
            return None, fact_flags, latency_us

        # 1. CRC check on incoming frame
        if not verify_crc16(frame):
            fact_flags.append({
                "id": f"flag_crc_{int(time.time()*1e6)}",
                "kind": "crc_mismatch",
                "detail": f"Master frame CRC mismatch: {frame.hex()}",
            })
            return None, fact_flags, latency_us

        slave_addr = frame[0]
        # Ignore broadcast or frame meant for other slaves
        if slave_addr == 0 or slave_addr != self.slave_id:
            return None, fact_flags, latency_us

        fc = frame[1]
        payload = frame[2:-2]
        reply_pdu: Optional[bytes] = None

        # 2. Process function code
        if fc == 0x03:  # Read Holding Registers
            if len(payload) != 4:
                reply_pdu = bytes([self.slave_id, fc | 0x80, 0x03])
            else:
                start_addr, count = struct.unpack(">HH", payload)
                if count < 1 or count > 125:
                    reply_pdu = bytes([self.slave_id, fc | 0x80, 0x03])
                else:
                    byte_count = count * 2
                    reg_bytes = bytearray([self.slave_id, fc, byte_count])
                    for a in range(start_addr, start_addr + count):
                        val = self.holding_registers.get(a, 0)
                        reg_bytes.extend(struct.pack(">H", val))
                    reply_pdu = bytes(reg_bytes)

        elif fc == 0x06:  # Write Single Register
            if len(payload) != 4:
                reply_pdu = bytes([self.slave_id, fc | 0x80, 0x03])
            else:
                addr, val = struct.unpack(">HH", payload)
                self.holding_registers[addr] = val
                reply_pdu = bytes([self.slave_id, fc]) + payload

        elif fc == 0x10:  # Write Multiple Registers
            if len(payload) < 5:
                reply_pdu = bytes([self.slave_id, fc | 0x80, 0x03])
            else:
                start_addr, count, byte_count = struct.unpack(">HHB", payload[:5])
                if byte_count != count * 2 or len(payload[5:]) != byte_count:
                    reply_pdu = bytes([self.slave_id, fc | 0x80, 0x03])
                else:
                    vals = struct.unpack(f">{count}H", payload[5:])
                    for i, v in enumerate(vals):
                        self.holding_registers[start_addr + i] = v
                    reply_pdu = bytes([self.slave_id, fc]) + struct.pack(">HH", start_addr, count)

        elif fc == 0x01:  # Read Coils
            if len(payload) != 4:
                reply_pdu = bytes([self.slave_id, fc | 0x80, 0x03])
            else:
                start_addr, count = struct.unpack(">HH", payload)
                byte_count = (count + 7) // 8
                res = bytearray([self.slave_id, fc, byte_count])
                bits = bytearray(byte_count)
                for i in range(count):
                    if self.coils.get(start_addr + i, False):
                        bits[i // 8] |= (1 << (i % 8))
                res.extend(bits)
                reply_pdu = bytes(res)

        elif fc == 0x05:  # Write Single Coil
            if len(payload) != 4:
                reply_pdu = bytes([self.slave_id, fc | 0x80, 0x03])
            else:
                addr, val = struct.unpack(">HH", payload)
                if val == 0xFF00:
                    self.coils[addr] = True
                    reply_pdu = bytes([self.slave_id, fc]) + payload
                elif val == 0x0000:
                    self.coils[addr] = False
                    reply_pdu = bytes([self.slave_id, fc]) + payload
                else:
                    reply_pdu = bytes([self.slave_id, fc | 0x80, 0x03])

        else:
            # Illegal function
            reply_pdu = bytes([self.slave_id, fc | 0x80, 0x01])

        # 3. Apply active Injections
        for inj in injections:
            if inj.get("channel") != self.channel_name:
                continue
            kind = inj.get("kind")
            params = inj.get("params", {})

            if kind == "no_reply":
                return None, fact_flags, latency_us
            elif kind == "late_reply":
                delay_ms = float(params.get("ms", 100))
                latency_us += int(delay_ms * 1000)
            elif kind == "wrong_slave_id":
                fake_id = int(params.get("id", self.slave_id + 1))
                if reply_pdu:
                    reply_pdu = bytes([fake_id]) + reply_pdu[1:]
            elif kind == "exception_code":
                code = int(params.get("code", 0x02))
                reply_pdu = bytes([self.slave_id, fc | 0x80, code])

        # 4. Finalize CRC and reply frame
        c_lo, c_hi = compute_crc16(reply_pdu)
        for inj in injections:
            if inj.get("channel") == self.channel_name and inj.get("kind") == "bad_crc":
                c_lo ^= 0xFF
                fact_flags.append({
                    "id": f"flag_bad_crc_{int(time.time()*1e6)}",
                    "kind": "injected_bad_crc",
                    "detail": "Slave emitted intentional bad CRC",
                })

        reply_frame = reply_pdu + bytes([c_lo, c_hi])
        return reply_frame, fact_flags, latency_us
