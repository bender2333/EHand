from ehand.models.modbus_slave import ModbusSlave, compute_crc16, verify_crc16


def build_frame(pdu: bytes) -> bytes:
    lo, hi = compute_crc16(pdu)
    return pdu + bytes([lo, hi])


def test_modbus_slave() -> None:
    slave = ModbusSlave(
        "rs485",
        {
            "slave_id": 1,
            "holding_registers": {"100": 1234, "101": 5678},
            "coils": {"10": True, "11": False},
        },
    )

    # 1. Read holding register (FC 03): read 2 regs starting at 100
    req_pdu = bytes([1, 3, 0, 100, 0, 2])
    req_frame = build_frame(req_pdu)
    rep, flags, lat = slave.process_rx(req_frame, [])
    assert rep is not None
    assert verify_crc16(rep) is True
    # Reply: [1, 3, byte_count=4, 1234(0x04D2), 5678(0x162E)]
    assert rep[:3] == bytes([1, 3, 4])
    assert rep[3:7] == bytes([0x04, 0xD2, 0x16, 0x2E])
    print("Modbus FC03 Read OK")

    # 2. Write single register (FC 06): write 9999 to reg 200
    req_pdu = bytes([1, 6, 0, 200, 0x27, 0x0F])
    req_frame = build_frame(req_pdu)
    rep, flags, lat = slave.process_rx(req_frame, [])
    assert rep is not None
    assert slave.holding_registers[200] == 9999
    print("Modbus FC06 Write OK")

    # 3. Read back written register
    req_pdu = bytes([1, 3, 0, 200, 0, 1])
    req_frame = build_frame(req_pdu)
    rep, flags, lat = slave.process_rx(req_frame, [])
    assert rep is not None
    assert rep[3:5] == bytes([0x27, 0x0F])
    print("Modbus Readback OK")

    # 4. Injections: bad_crc
    rep, flags, lat = slave.process_rx(req_frame, [{"channel": "rs485", "kind": "bad_crc"}])
    assert rep is not None
    assert verify_crc16(rep) is False
    assert len(flags) == 1
    assert flags[0]["kind"] == "injected_bad_crc"
    print("Modbus Injected Bad CRC OK")

    # 5. Injections: no_reply
    rep, flags, lat = slave.process_rx(req_frame, [{"channel": "rs485", "kind": "no_reply"}])
    assert rep is None
    print("Modbus Injected No Reply OK")

    # 6. Injections: late_reply
    rep, flags, lat = slave.process_rx(req_frame, [{"channel": "rs485", "kind": "late_reply", "params": {"ms": 150}}])
    assert rep is not None
    assert lat >= 150000
    print("Modbus Injected Late Reply OK")

    # 7. Injections: wrong_slave_id
    rep, flags, lat = slave.process_rx(req_frame, [{"channel": "rs485", "kind": "wrong_slave_id", "params": {"id": 99}}])
    assert rep is not None
    assert rep[0] == 99
    print("Modbus Injected Wrong Slave ID OK")

    print("ALL MODBUS SLAVE TESTS PASSED!")


if __name__ == "__main__":
    test_modbus_slave()
