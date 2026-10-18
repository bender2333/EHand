import os
import tempfile
import time
from ehand.models.serial_peer import SerialPeer
from ehand.periphery import (
    add_injection,
    get_active_injections,
    get_active_periphery,
    save_active_injections,
    save_active_periphery,
)
from ehand.timeline import (
    add_mark,
    get_timeline_summary,
    get_transactions_detail,
    record_transaction,
)


def run_checks() -> None:
    # 1. Timeline check
    with tempfile.NamedTemporaryFile(suffix=".db") as tmp_db:
        db_path = tmp_db.name
        m1 = add_mark("mark_alpha", db_path=db_path)
        assert m1["mark"] == "mark_alpha"

        record_transaction(
            tx_id="tx_test_1",
            channel="uart1",
            start_time_us=int(time.time() * 1e6),
            duration_us=5000,
            req_hex="50494E47",
            req_ascii="PING",
            reply_hex="504F4E47",
            reply_ascii="PONG",
            latency_us=1200,
            injections=[],
            fact_flags=[],
            db_path=db_path,
        )

        sum_res = get_timeline_summary(since_mark="mark_alpha", db_path=db_path)
        summary = sum_res["summary"]
        assert summary["counts"]["transactions"] == 1
        assert summary["counts"]["fact_flags"] == 0

        detail_res = get_transactions_detail(since_mark="mark_alpha", db_path=db_path)
        txs = detail_res["transactions"]
        assert len(txs) == 1
        assert txs[0]["tx_id"] == "tx_test_1"
        assert txs[0]["request"]["ascii"] == "PING"
        assert txs[0]["reply"]["ascii"] == "PONG"

    # 2. SerialPeer model check
    peer = SerialPeer(
        "uart1",
        {
            "baud": 9600,
            "replies": [{"match": "HELLO", "response": "WORLD"}],
        },
    )
    # normal match
    rep, flags, lat = peer.process_rx(b"HELLO", [])
    assert rep == b"WORLD"
    assert len(flags) == 0

    # injection: delay
    rep, flags, lat = peer.process_rx(b"HELLO", [{"channel": "uart1", "kind": "delay", "params": {"ms": 100}}])
    assert rep == b"WORLD"
    assert lat >= 100000

    # injection: drop
    rep, flags, lat = peer.process_rx(b"HELLO", [{"channel": "uart1", "kind": "drop"}])
    assert rep is None

    # injection: corrupt
    rep, flags, lat = peer.process_rx(b"HELLO", [{"channel": "uart1", "kind": "corrupt"}])
    assert rep != b"WORLD"
    assert len(flags) == 1
    assert flags[0]["kind"] == "injected_corruption"

    print("ALL EHAND SELF-CHECKS PASSED!")


if __name__ == "__main__":
    run_checks()
