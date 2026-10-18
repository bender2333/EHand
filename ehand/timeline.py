import os
import sqlite3
import time
from typing import Any, Dict, List, Optional

DB_DIR = os.path.expanduser("~/.ehand")
DB_PATH = os.path.join(DB_DIR, "timeline.db")


def get_db(db_path: str = DB_PATH) -> sqlite3.Connection:
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS marks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE,
            timestamp_us INTEGER,
            created_at REAL
        );
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp_us INTEGER,
            channel TEXT,
            direction TEXT,
            data BLOB,
            flags TEXT
        );
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS transactions (
            id TEXT PRIMARY KEY,
            channel TEXT,
            start_time_us INTEGER,
            duration_us INTEGER,
            req_hex TEXT,
            req_ascii TEXT,
            reply_hex TEXT,
            reply_ascii TEXT,
            latency_us INTEGER,
            injections_json TEXT,
            fact_flags_json TEXT
        );
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS fact_flags (
            id TEXT PRIMARY KEY,
            timestamp_us INTEGER,
            channel TEXT,
            kind TEXT,
            detail TEXT
        );
        """
    )
    conn.commit()
    return conn


def add_mark(name: str, db_path: str = DB_PATH) -> Dict[str, Any]:
    conn = get_db(db_path)
    now_us = int(time.time() * 1_000_000)
    now_s = time.time()
    with conn:
        conn.execute(
            "INSERT OR REPLACE INTO marks (name, timestamp_us, created_at) VALUES (?, ?, ?);",
            (name, now_us, now_s),
        )
    return {"mark": name, "timestamp_us": now_us, "time_iso": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(now_s))}


def record_transaction(
    tx_id: str,
    channel: str,
    start_time_us: int,
    duration_us: int,
    req_hex: str,
    req_ascii: str,
    reply_hex: str,
    reply_ascii: str,
    latency_us: int,
    injections: List[Dict[str, Any]],
    fact_flags: List[Dict[str, Any]],
    db_path: str = DB_PATH,
) -> None:
    import json
    conn = get_db(db_path)
    with conn:
        conn.execute(
            """
            INSERT OR REPLACE INTO transactions 
            (id, channel, start_time_us, duration_us, req_hex, req_ascii, reply_hex, reply_ascii, latency_us, injections_json, fact_flags_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """,
            (
                tx_id,
                channel,
                start_time_us,
                duration_us,
                req_hex,
                req_ascii,
                reply_hex,
                reply_ascii,
                latency_us,
                json.dumps(injections),
                json.dumps(fact_flags),
            ),
        )
        for flag in fact_flags:
            conn.execute(
                """
                INSERT OR REPLACE INTO fact_flags (id, timestamp_us, channel, kind, detail)
                VALUES (?, ?, ?, ?, ?);
                """,
                (
                    flag.get("id", f"flag_{int(time.time()*1e6)}"),
                    flag.get("timestamp_us", start_time_us),
                    channel,
                    flag.get("kind", "unknown"),
                    flag.get("detail", ""),
                ),
            )


def get_timeline_summary(since_mark: Optional[str] = None, db_path: str = DB_PATH) -> Dict[str, Any]:
    import json
    conn = get_db(db_path)
    min_us = 0
    if since_mark:
        cur = conn.execute("SELECT timestamp_us FROM marks WHERE name = ?;", (since_mark,))
        row = cur.fetchone()
        if row:
            min_us = row[0]

    cur = conn.execute("SELECT name, timestamp_us, created_at FROM marks WHERE timestamp_us >= ? ORDER BY timestamp_us ASC;", (min_us,))
    marks = [{"name": r[0], "time_ms": r[1] / 1000.0} for r in cur.fetchall()]

    cur = conn.execute("SELECT COUNT(*), COUNT(DISTINCT channel) FROM transactions WHERE start_time_us >= ?;", (min_us,))
    tx_count, ch_count = cur.fetchone()

    cur = conn.execute("SELECT id, timestamp_us, channel, kind, detail FROM fact_flags WHERE timestamp_us >= ? ORDER BY timestamp_us ASC;", (min_us,))
    flags = [
        {
            "id": r[0],
            "time_ms": r[1] / 1000.0,
            "channel": r[2],
            "kind": r[3],
            "detail": r[4],
        }
        for r in cur.fetchall()
    ]

    now_us = int(time.time() * 1_000_000)
    duration_ms = (now_us - min_us) / 1000.0 if min_us > 0 else 0.0

    return {
        "summary": {
            "since_mark": since_mark,
            "duration_ms": duration_ms,
            "marks": marks,
            "counts": {
                "channels": ch_count or 0,
                "transactions": tx_count or 0,
                "fact_flags": len(flags),
            },
            "fact_flags": flags,
        }
    }


def get_transactions_detail(since_mark: Optional[str] = None, channel: Optional[str] = None, db_path: str = DB_PATH) -> Dict[str, Any]:
    import json
    conn = get_db(db_path)
    min_us = 0
    if since_mark:
        cur = conn.execute("SELECT timestamp_us FROM marks WHERE name = ?;", (since_mark,))
        row = cur.fetchone()
        if row:
            min_us = row[0]

    query = "SELECT id, channel, start_time_us, duration_us, req_hex, req_ascii, reply_hex, reply_ascii, latency_us, injections_json, fact_flags_json FROM transactions WHERE start_time_us >= ?"
    params: List[Any] = [min_us]
    if channel:
        query += " AND channel = ?"
        params.append(channel)
    query += " ORDER BY start_time_us ASC;"

    cur = conn.execute(query, params)
    txs = []
    for r in cur.fetchall():
        txs.append(
            {
                "tx_id": r[0],
                "channel": r[1],
                "start_time_us": r[2],
                "duration_us": r[3],
                "request": {"hex": r[4], "ascii": r[5]},
                "reply": {"hex": r[6], "ascii": r[7], "latency_us": r[8]},
                "injections_active": json.loads(r[9]) if r[9] else [],
                "fact_flags": json.loads(r[10]) if r[10] else [],
            }
        )
    return {"transactions": txs}
