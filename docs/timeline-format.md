# Timeline 格式与下钻规范（Timeline Format & Drill-down）

> 对应 Issue #6（wayfinder map #1）。参考 `CONTEXT.md` 与 ADR-0003。

## 1. 核心设计原则

1. **分层聚合（Layered）**：从 Summary（默认）-> Transaction（交互事务）-> Frame / Byte（字/字节与精确时序）逐级下钻，防止海量底层数据淹没 Agent 上下文。
2. **纯事实陈述（Fact Flags）**：仅标记协议违规（如校验错、超时、字节间隙超时），不主观判断「谁的代码写错了」。
3. **单时间轴对齐（Time-aligned）**：所有 Channel 的收发、故障注入、状态标记共享同一硬件微秒基准时间戳（`timestamp_us`）。

## 2. 格式结构定义（JSON）

### 2.1 顶层概要：Summary（`ehand log` 默认输出）
```json
{
  "summary": {
    "start_time_iso": "2026-10-18T15:20:00.000Z",
    "duration_ms": 5240.5,
    "marks": [
      { "name": "boot", "time_ms": 10.2 },
      { "name": "after_init", "time_ms": 1200.0 }
    ],
    "counts": {
      "channels": 2,
      "transactions": 14,
      "bytes_rx": 112,
      "bytes_tx": 84,
      "injections": 1,
      "fact_flags": 1
    },
    "fact_flags": [
      {
        "id": "flag_001",
        "time_ms": 1342.15,
        "channel": "rs485",
        "kind": "crc_mismatch",
        "detail": "Expected CRC 0x4112, received 0x1234"
      }
    ]
  }
}
```

### 2.2 事务层：Transaction（`ehand log --level=transaction`）
```json
{
  "transactions": [
    {
      "tx_id": "tx_001",
      "channel": "uart1",
      "start_time_us": 120500,
      "duration_us": 8320,
      "request": {
        "hex": "010300000002C40B",
        "ascii": "....",
        "timestamp_us": 120500
      },
      "reply": {
        "hex": "01030400010002A385",
        "latency_us": 1240,
        "timestamp_us": 121740
      },
      "injections_active": [],
      "fact_flags": []
    }
  ]
}
```

### 2.3 字节与微秒时序层：Byte / Event（`ehand log --level=byte --channel=uart1`）
```json
{
  "events": [
    {
      "time_us": 120500,
      "channel": "uart1",
      "dir": "RX",
      "byte": "0x01",
      "flags": []
    },
    {
      "time_us": 121541,
      "channel": "uart1",
      "dir": "RX",
      "byte": "0x03",
      "gap_us": 1041,
      "flags": []
    }
  ]
}
```

## 3. CLI 查询与下钻指令

- `ehand log`：输出当前切片内默认 Summary 及所有 Fact Flags。
- `ehand log --since-mark=<name>`：从指定 Mark 切片点开始输出。
- `ehand log --level=transaction [--channel=<ch>]`：下钻查看交互事务。
- `ehand log --level=byte [--tx=<id>]`：下钻查看单事务或全时段的底层精确时序与逐字节事件。
