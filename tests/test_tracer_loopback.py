import os
import pty
import subprocess
import time

from ehand.hardware.uart import UartPort
from ehand.models.serial_peer import SerialPeer
from ehand.periphery import add_injection, load_periphery_file, save_active_periphery
from ehand.service import EHandService
from ehand.timeline import add_mark, get_timeline_summary, get_transactions_detail


def test_tracer_loopback() -> None:
    # 1. Setup virtual PTY pair (master = target board, slave = ehand port)
    master_fd, slave_fd = pty.openpty()
    import tty
    tty.setraw(master_fd)
    tty.setraw(slave_fd)
    slave_name = os.ttyname(slave_fd)

    # 2. Configure periphery
    cfg = {
        "name": "tracer_test",
        "channel": {
            "uart1": {
                "type": "serial_peer",
                "port": slave_name,
                "baud": 9600,
                "replies": [{"match": "PING\n", "response": "PONG\n"}],
            }
        },
    }
    save_active_periphery(cfg)
    m = add_mark("tracer_start")
    print(f"Mark created: {m['mark']}")

    # 3. Create service and uart port
    uart = UartPort(port=slave_name, baud=9600)
    model = SerialPeer("uart1", cfg["channel"]["uart1"])
    svc = EHandService(port_override=slave_name)

    # Turn 1: Normal PING -> PONG
    os.write(master_fd, b"PING\n")
    time.sleep(0.05)
    handled = svc.run_one_turn(uart, model)
    assert handled is True
    reply = os.read(master_fd, 100)
    assert reply == b"PONG\n"
    print("Turn 1 PASS: Normal PING -> PONG")

    # Turn 2: Injected delay
    add_injection("uart1", "delay", {"ms": 50.0})
    t_send = time.time()
    os.write(master_fd, b"PING\n")
    time.sleep(0.05)
    handled = svc.run_one_turn(uart, model)
    assert handled is True
    reply = os.read(master_fd, 100)
    dt_ms = (time.time() - t_send) * 1000.0
    assert reply == b"PONG\n"
    assert dt_ms >= 45.0
    print(f"Turn 2 PASS: Injected delay, measured {dt_ms:.1f}ms")

    # Turn 3: Injected corruption
    add_injection("uart1", "corrupt", {})
    os.write(master_fd, b"PING\n")
    time.sleep(0.05)
    handled = svc.run_one_turn(uart, model)
    assert handled is True
    reply = os.read(master_fd, 100)
    assert reply != b"PONG\n"
    print(f"Turn 3 PASS: Injected corruption, received {reply}")

    # 4. Check Timeline Summary
    summary_res = get_timeline_summary(since_mark="tracer_start")
    s = summary_res["summary"]
    print("Summary:", s["counts"])
    assert s["counts"]["transactions"] == 3
    assert s["counts"]["fact_flags"] == 1
    assert s["fact_flags"][0]["kind"] == "injected_corruption"

    # 5. Check Transaction Detail
    tx_res = get_transactions_detail(since_mark="tracer_start", channel="uart1")
    txs = tx_res["transactions"]
    assert len(txs) == 3
    assert txs[0]["request"]["ascii"] == "PING\n"
    assert txs[0]["reply"]["ascii"] == "PONG\n"

    # Clean up
    uart.close()
    os.close(master_fd)
    os.close(slave_fd)
    print("ALL TRACER LOOPBACK VERIFICATIONS PASSED!")


if __name__ == "__main__":
    test_tracer_loopback()
