## 8. Agent 集成设计

### 8.1 MCP Server 设计

AgentProbe 提供标准 MCP (Model Context Protocol) Server，AI Agent 可通过 MCP 协议直接调用硬件能力。

**MCP Server 信息：**

```yaml
server:
  name: "agentprobe"
  version: "1.0.0"
  description: "AgentProbe - 嵌入式开发硬件闭环平台"
  transport: "stdio"  # 或 "http+sse"
```

**MCP Tools（Agent 可调用的工具）：**

```yaml
tools:

  # ─── Mock 管理 ───────────────────────────────
  - name: mock_load_model
    description: "加载 Mock 外设模型到指定通道"
    parameters:
      model_name: string    # "W25Q128", "SHT30", "Generic_SPI_Register"
      channel: string       # "spi_0", "i2c_0", "uart_0"
      config: object        # 模型特定配置参数 (可选)

  - name: mock_get_state
    description: "获取 Mock 设备的当前内部状态"
    parameters:
      device: string        # "spi_0", "i2c_0"
    returns:
      state: object         # 设备完整状态 (寄存器值/内存使用/统计)

  - name: mock_set_value
    description: "设置 Mock 设备的数据值 (如传感器读数)"
    parameters:
      device: string
      register: string      # 寄存器名或地址
      value: any             # 要设置的值

  - name: mock_inject_fault
    description: "向 Mock 设备注入故障"
    parameters:
      device: string
      fault_type: string    # "timeout", "nak", "crc_error", "busy_loop", "no_response"
      duration_ms: integer  # 故障持续时间 (0=永久,直到清除)

  - name: mock_clear_fault
    description: "清除 Mock 设备上的故障注入"
    parameters:
      device: string

  # ─── 目标板控制 ──────────────────────────────
  - name: target_flash
    description: "通过 SWD 将固件烧录到目标 MCU"
    parameters:
      firmware_path: string  # ELF/HEX/BIN 文件路径
      verify: boolean        # 烧录后校验 (默认 true)
      reset_after: boolean   # 烧录后复位 (默认 true)
    returns:
      success: boolean
      size_bytes: integer
      duration_ms: integer

  - name: target_reset
    description: "复位目标板"
    parameters:
      mode: string           # "hw" (硬件复位) 或 "sw" (软件复位)

  - name: target_power
    description: "控制目标板电源"
    parameters:
      action: string         # "on", "off", "cycle"
      delay_ms: integer      # cycle 模式: 掉电后等待时间

  - name: target_detect
    description: "检测目标板连接状态和 MCU 型号"
    returns:
      connected: boolean
      mcu_id: string
      mcu_name: string       # "STM32F407VGT6"
      state: string          # "running", "halted", "reset"

  # ─── 调试 ─────────────────────────────────────
  - name: debug_halt
    description: "暂停目标 MCU 执行"

  - name: debug_resume
    description: "恢复目标 MCU 执行"

  - name: debug_step
    description: "单步执行一条指令"

  - name: debug_set_breakpoint
    description: "设置断点"
    parameters:
      address: string        # 地址或符号名 "0x08001234" 或 "main"

  - name: debug_read_memory
    description: "读取目标 MCU 内存"
    parameters:
      address: string
      size: integer           # 字节数
    returns:
      data: string            # hex 编码

  - name: debug_read_register
    description: "读取 CPU 寄存器"
    parameters:
      register: string        # "r0", "sp", "pc", "all"
    returns:
      value: string

  - name: debug_backtrace
    description: "获取调用栈"
    returns:
      frames: array           # [{address, function, file, line}, ...]

  # ─── 信号观测 ─────────────────────────────────
  - name: signal_get_events
    description: "获取最近的总线通信事件"
    parameters:
      source: string          # "spi_0", "i2c_0", "uart_0", "all"
      count: integer          # 最近 N 条 (默认 50)
      since_ms: integer       # 或: 最近 N 毫秒内的事件
    returns:
      events: array           # 结构化事件列表

  - name: signal_get_summary
    description: "获取信号活动摘要和异常检测结果"
    parameters:
      period: string          # "last_1s", "last_5s", "last_30s", "since_reset"
    returns:
      summary: object         # 各通道统计 + 异常列表

  - name: signal_capture
    description: "启动逻辑分析仪捕获"
    parameters:
      channels: array         # [0, 1, 2, 3] 通道编号
      sample_rate_hz: integer # 采样率
      duration_ms: integer    # 持续时间
      trigger: object         # 触发条件 (可选)
    returns:
      capture_id: string      # 捕获 ID, 用于后续查询

  - name: signal_get_capture
    description: "获取逻辑分析仪捕获结果"
    parameters:
      capture_id: string
    returns:
      samples: object         # 采样数据 + 协议解码结果

  # ─── 模拟子系统 ───────────────────────────────
  - name: analog_set_dac
    description: "设置 DAC 输出电压 (模拟传感器信号)"
    parameters:
      channel: integer        # 0-3
      voltage: number         # 0.0 至 3.3 (伏特)

  - name: analog_read_adc
    description: "读取 ADC 测量值"
    parameters:
      channel: integer        # 0-3
    returns:
      voltage: number         # 测量电压 (伏特)
      raw: integer            # ADC 原始值

  - name: analog_read_current
    description: "读取目标板供电电流"
    returns:
      current_ma: number      # 电流 (毫安)
      voltage_v: number       # 电压 (伏特)
      power_mw: number        # 功率 (毫瓦)

  # ─── I/O 配置 ─────────────────────────────────
  - name: io_set_route
    description: "配置 I/O 引脚路由"
    parameters:
      target_pin: string      # "IO_0", "IO_1", ...
      connect_to: string      # "mock_spi_0.clk", "analyzer.ch0", ...
      direction: string       # "input", "output", "bidir", "highz"

  - name: io_get_routes
    description: "获取当前所有 I/O 路由配置"
    returns:
      routes: array

  # ─── 串口 ─────────────────────────────────────
  - name: serial_read
    description: "读取串口接收缓冲区"
    parameters:
      port: string            # "uart_0", "uart_1", "rtt", "semihosting"
      timeout_ms: integer     # 超时时间
    returns:
      data: string            # 接收到的文本

  - name: serial_write
    description: "通过串口发送数据"
    parameters:
      port: string
      data: string

  # ─── 断言/测试 ─────────────────────────────────
  - name: assert_expect_transaction
    description: "设置期望的总线事务, 超时判定失败"
    parameters:
      bus: string             # "spi_0"
      timeout_ms: integer
      expect: object          # 期望的事务内容
    returns:
      passed: boolean
      actual: object          # 实际事务内容
      match_details: string

  - name: assert_expect_serial
    description: "期望串口输出包含指定内容"
    parameters:
      port: string
      timeout_ms: integer
      contains: string        # 期望包含的文本
    returns:
      passed: boolean
      actual_output: string

  # ─── 网络分析 ─────────────────────────────────
  - name: network_tap_status
    description: "获取以太网 TAP 状态和流量统计"
    returns:
      link_up: boolean
      speed: string           # "10M", "100M"
      rx_packets: integer
      tx_packets: integer

  - name: network_capture_start
    description: "开始网络流量捕获"
    parameters:
      filter: string          # BPF 过滤表达式 (可选)
      max_packets: integer
      duration_ms: integer

  - name: network_capture_get
    description: "获取网络捕获的数据包"
    parameters:
      capture_id: string
      format: string          # "summary", "hex", "decoded"
    returns:
      packets: array

  # ─── Session 管理 ──────────────────────────────
  - name: session_load
    description: "加载 Session 配置文件"
    parameters:
      path: string            # YAML 文件路径

  - name: session_save
    description: "保存当前配置为 Session 文件"
    parameters:
      path: string
```

**MCP Resources（Agent 可访问的资源）：**

```yaml
resources:
  - uri: "agentprobe://status"
    name: "设备状态"
    description: "AgentProbe 设备和目标板的完整状态信息"

  - uri: "agentprobe://events/stream"
    name: "实时事件流"
    description: "所有硬件事件的实时流 (SSE)"

  - uri: "agentprobe://mock/{device}/state"
    name: "Mock 设备状态"
    description: "指定 Mock 设备的详细内部状态"

  - uri: "agentprobe://models"
    name: "可用模型列表"
    description: "所有可加载的 Mock 设备模型"

  - uri: "agentprobe://session/current"
    name: "当前 Session"
    description: "当前加载的 Session 配置"
```

### 8.2 REST API 设计

```
Base URL: http://localhost:8742/api/v1

端点:

  GET    /status                         设备状态
  GET    /target                         目标板状态
  POST   /target/flash                   烧录固件
  POST   /target/reset                   复位
  POST   /target/power                   电源控制

  GET    /mock                           已加载的 Mock 列表
  POST   /mock/load                      加载模型
  DELETE /mock/{device}                  卸载模型
  GET    /mock/{device}/state            设备状态
  PUT    /mock/{device}/config           更新配置
  POST   /mock/{device}/fault            注入故障
  DELETE /mock/{device}/fault            清除故障

  GET    /signal/events                  事件查询
  GET    /signal/summary                 活动摘要
  POST   /signal/capture                 启动捕获
  GET    /signal/capture/{id}            获取捕获数据

  GET    /analog/adc/{channel}           ADC 读取
  PUT    /analog/dac/{channel}           DAC 设置
  GET    /analog/power                   电流/电压

  GET    /io/routes                      I/O 路由
  PUT    /io/route/{pin}                 配置路由

  GET    /serial/{port}                  串口读取
  POST   /serial/{port}                  串口发送

  POST   /assert/transaction             事务断言
  POST   /assert/serial                  串口断言

  POST   /test/run                       运行测试
  GET    /test/report/{id}               测试报告

  GET    /network/status                 网络 TAP 状态
  POST   /network/capture                开始网络捕获
  GET    /network/capture/{id}           获取网络捕获

  POST   /session/load                   加载 Session
  POST   /session/save                   保存 Session

  WebSocket /ws/events                   实时事件流
  WebSocket /ws/serial/{port}            实时串口流
```

### 8.3 Agent 完整工作流示例

```
Agent 任务: "为 STM32F407 开发 W25Q128 SPI Flash 驱动"

Agent 执行步骤:

Step 1: 检查硬件连接
  → tool: target_detect
  ← {connected: true, mcu_name: "STM32F407VGT6", state: "halted"}

Step 2: 加载 Mock 模型
  → tool: mock_load_model
    {model_name: "W25Q128", channel: "spi_0"}
  ← {success: true, device_id: "spi_0_w25q128"}

Step 3: 配置 I/O 路由
  → tool: io_set_route {target_pin: "IO_5", connect_to: "mock_spi_0.clk"}
  → tool: io_set_route {target_pin: "IO_6", connect_to: "mock_spi_0.miso"}
  → tool: io_set_route {target_pin: "IO_7", connect_to: "mock_spi_0.mosi"}
  → tool: io_set_route {target_pin: "IO_8", connect_to: "mock_spi_0.cs"}

Step 4: 编写驱动代码
  → Agent 编写 spi_flash.c / spi_flash.h
  → Agent 编写 main.c (测试代码)

Step 5: 编译
  → Agent 调用: arm-none-eabi-gcc ...
  ← 编译成功, 生成 build/firmware.elf

Step 6: 烧录
  → tool: target_flash
    {firmware_path: "build/firmware.elf", verify: true, reset_after: true}
  ← {success: true, size_bytes: 42368, duration_ms: 1200}

Step 7: 等待运行并观察
  → tool: signal_get_events
    {source: "spi_0", since_ms: 2000}
  ← {events: [
       {ts: 0.105, type: "spi_transaction",
        decoded: {command: "READ_JEDEC_ID", opcode: "0x9F",
                  mosi: "9F000000", miso: "FFEF4018"}},
       {ts: 0.110, type: "spi_transaction",
        decoded: {command: "READ_STATUS_REG1", opcode: "0x05",
                  mosi: "0500", miso: "FF00"}}
     ]}

Step 8: 读取串口日志
  → tool: serial_read {port: "uart_0", timeout_ms: 3000}
  ← {data: "[LOG] SPI Flash Init OK\r\n[LOG] JEDEC ID: EF4018\r\n"}

Step 9: 验证读写功能
  → tool: signal_get_summary {period: "last_5s"}
  ← {summary: {
       spi_0: {transactions: 28, errors: 0, last_command: "READ_DATA"},
       anomalies: []
     }}

Step 10: 检查 Mock 内部状态
  → tool: mock_get_state {device: "spi_0"}
  ← {state: {
       status_reg1: "0x00",
       write_enable_latch: false,
       memory_written_bytes: 256,
       memory_hash: "a1b2c3d4..."
     }}

Step 11: 测试故障处理
  → tool: mock_inject_fault
    {device: "spi_0", fault_type: "busy_loop", duration_ms: 5000}
  → tool: target_reset {}
  → (等待 6 秒)
  → tool: serial_read {port: "uart_0", timeout_ms: 7000}
  ← {data: "[LOG] SPI Flash Init...\r\n[WARN] Flash busy timeout, retrying...\r\n[LOG] Flash recovered\r\n"}
  → tool: mock_clear_fault {device: "spi_0"}

Step 12: Agent 判定
  ← "驱动开发完成, 通过全部功能测试和故障恢复测试"

如果 Step 7 发现异常 (比如 MISO 全 FF):
  → Agent 分析: "JEDEC ID 返回全 FF, 可能 SPI 模式配置错误"
  → Agent 修改代码: 将 SPI Mode 从 0 改为 3
  → 回到 Step 5 重新编译烧录
  → 自动迭代直到正确
```

---

## 9. 可观测性设计

### 9.1 统一事件模型

所有硬件活动都被建模为统一格式的事件，是整个可观测性系统的基础。

**事件 Schema：**

```json
{
  "id": "evt_00001234",
  "timestamp": 1679234567.123456,
  "timestamp_ns": 123456789,
  "source": "spi_0",
  "category": "bus_transaction",
  "level": "decoded",
  "data": {
    "command": "READ_JEDEC_ID",
    "opcode": "0x9F",
    "mosi_hex": "9F000000",
    "miso_hex": "FFEF4018",
    "bytes": 4,
    "duration_us": 32
  },
  "mock_state": {
    "device": "W25Q128",
    "status_reg": "0x00",
    "action_taken": "returned JEDEC ID from config"
  },
  "context": {
    "session": "sensor_board_v1",
    "target_state": "running",
    "firmware_build": "build_042",
    "uptime_ms": 105
  }
}
```

**事件类别：**

| 类别 | source 示例 | 说明 |
|------|------------|------|
| bus_transaction | spi_0, i2c_0, can_0 | 总线通信事务（已解码） |
| bus_raw | la_ch0, la_ch1 | 原始信号变化 |
| uart_data | uart_0, rtt, semihosting | 串口/RTT 数据 |
| gpio_change | gpio_5, gpio_12 | GPIO 电平变化 |
| debug_event | swd | 调试事件（断点/异常/暂停） |
| power_event | ina219 | 电源事件（电流突变/过流） |
| analog_sample | adc_0, dac_1 | 模拟采样/输出记录 |
| target_state | target | 目标板状态变化（连接/断开/复位/运行/停止） |
| mock_state | spi_0_w25q128 | Mock 设备内部状态变化 |
| system_event | system | 系统事件（连接/错误/配置变更） |
| network_packet | eth_tap | 网络数据包 |

### 9.2 Agent 可观测性（机器视角）

Agent 通过 API 获得的是结构化、有语义、可直接推理的数据。

**核心 API：**

#### 1. 实时事件流

```
WebSocket /ws/events?filter=spi_0,uart_0&level=decoded

→ 建立连接后, 持续推送过滤后的事件 JSON

事件推送示例:
{"ts":0.105,"src":"spi_0","cmd":"READ_JEDEC_ID","mosi":"9F000000","miso":"FFEF4018","ok":true}
{"ts":0.108,"src":"uart_0","data":"[LOG] JEDEC ID: EF4018\r\n"}
{"ts":0.110,"src":"spi_0","cmd":"READ_STATUS","mosi":"0500","miso":"FF00","ok":true}
```

#### 2. 快照查询

```
GET /api/v1/snapshot

返回当前所有子系统的瞬时状态:
{
  "timestamp": 1679234567.5,
  "target": {
    "connected": true,
    "mcu": "STM32F407VGT6",
    "state": "running",
    "uptime_ms": 12345
  },
  "mock_devices": {
    "spi_0": {
      "model": "W25Q128",
      "status_reg1": "0x00",
      "write_enable": false,
      "busy": false,
      "memory_written_bytes": 4096,
      "total_transactions": 142,
      "error_count": 0,
      "last_command": "READ_DATA",
      "last_activity_ms_ago": 12
    },
    "i2c_0": {
      "model": "SHT30",
      "address": "0x44",
      "temperature": 25.5,
      "humidity": 60.2,
      "total_transactions": 38,
      "error_count": 0
    }
  },
  "analog": {
    "dac": [1.65, 0.0, 0.0, 0.0],
    "adc": [1.64, 0.02, 0.01, 0.01],
    "target_current_ma": 45.2,
    "target_voltage_v": 3.28
  },
  "gpio": {
    "pin_5": {"direction": "output", "level": 1},
    "pin_6": {"direction": "input", "level": 0}
  },
  "network": {
    "link_up": true,
    "speed": "100M",
    "rx_packets": 1234,
    "tx_packets": 567
  }
}
```

#### 3. 智能摘要（Agent 最常用的接口）

```
GET /api/v1/summary?period=last_5s

返回:
{
  "period": "last_5s",
  "target_state": "running",
  "bus_activity": {
    "spi_0": {
      "transactions": 28,
      "errors": 0,
      "commands_seen": ["READ_JEDEC_ID", "READ_STATUS", "WRITE_ENABLE", "PAGE_PROGRAM", "READ_DATA"],
      "data_transferred_bytes": 1280,
      "avg_transaction_us": 45
    },
    "i2c_0": {
      "transactions": 5,
      "errors": 0,
      "addresses_seen": ["0x44"],
      "naks": 0
    },
    "uart_0": {
      "bytes_received": 128,
      "lines": [
        "[LOG] SPI Flash Init OK",
        "[LOG] JEDEC ID: EF4018",
        "[LOG] Write test: 256 bytes @ 0x000000",
        "[LOG] Read verify: PASS"
      ]
    }
  },
  "anomalies": [],
  "mock_state_changes": [
    {"device": "spi_0", "change": "write_enable: false → true → false", "count": 1},
    {"device": "spi_0", "change": "memory_written: 0 → 256 bytes", "count": 1}
  ],
  "analog": {
    "dac_changes": [],
    "adc_readings": {"ch0": {"min": 1.63, "max": 1.66, "avg": 1.645}},
    "current_avg_ma": 45.1,
    "current_peak_ma": 67.3
  },
  "assessment": "All operations nominal. SPI Flash driver write-read cycle completed successfully."
}

当有异常时:
{
  "anomalies": [
    {
      "severity": "warning",
      "type": "unexpected_response",
      "source": "spi_0",
      "detail": "READ_JEDEC_ID returned 0xFFFFFF instead of expected 0xEF4018",
      "event_id": "evt_00001180",
      "timestamp": 0.105,
      "possible_causes": [
        "SPI clock polarity (CPOL) mismatch - target configured Mode 0, device expects Mode 3",
        "SPI chip select (CS) not properly asserted",
        "SPI MISO line not connected"
      ],
      "suggested_actions": [
        "Check SPI mode configuration in driver code",
        "Verify IO routing: is MISO connected to the correct pin?"
      ]
    }
  ]
}
```

#### 4. 断言/期望引擎

```
POST /api/v1/assert/transaction
{
  "bus": "spi_0",
  "timeout_ms": 2000,
  "expect": {
    "command": "READ_JEDEC_ID",
    "miso_contains": "EF4018"
  }
}

返回 (等待直到匹配或超时):
{
  "passed": true,
  "matched_event": {
    "ts": 0.105,
    "command": "READ_JEDEC_ID",
    "mosi": "9F000000",
    "miso": "FFEF4018"
  },
  "wait_ms": 105
}

或:
{
  "passed": false,
  "reason": "timeout",
  "events_during_wait": [
    {"ts": 0.050, "command": "unknown", "mosi": "FF", "miso": "FF"}
  ],
  "suggestion": "No valid SPI transaction detected. Check SPI initialization."
}
```

### 9.3 工程师可观测性（人类视角）

同一套事件数据，以人类友好的方式呈现。

**工程师 Dashboard 视图设计：**

```
┌─ 工程师主界面 ─────────────────────────────────────────────────┐
│                                                                 │
│  ┌─ 状态栏 ──────────────────────────────────────────────────┐ │
│  │  🟢 AgentProbe Connected                                  │ │
│  │  🟢 Target: STM32F407 Running │ Uptime: 12.3s             │ │
│  │  🤖 Agent: Active - "Developing SPI Flash driver v3"      │ │
│  │  ⚡ Power: 45.2mA @ 3.28V = 148mW                        │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                 │
│  ┌─ 信号波形视图 ────────────────────────────────────────────┐ │
│  │  时间轴: ←──── 0ms ──── 1ms ──── 2ms ──── 3ms ────→     │ │
│  │                                                            │ │
│  │  SPI_CLK   ──┐┌┐┌┐┌┐┌┐┌┐┌┐┌┐┌──────────────────────     │ │
│  │  SPI_MOSI  ──┤├┤├┤├┤├┤├┤├┤├┤├──  0x9F 00 00 00          │ │
│  │  SPI_MISO  ──┤├┤├┤├┤├┤├┤├┤├┤├──  0xFF EF 40 18          │ │
│  │  SPI_CS    ──┘└─────────────┘└──                          │ │
│  │  UART_TX   ────────────┐┌┐┌┐┌┐┌┐┌┐┌┐┌┐┌┐┌┐┌┐┌───       │ │
│  │  GPIO_5    ────────────────────────────────┐┌─────        │ │
│  │                                                            │ │
│  │  ▲ 解码: [SPI] READ_JEDEC_ID → EF 40 18 (Winbond W25Q128)│ │
│  │  ▲ 解码: [UART] "[LOG] JEDEC ID: EF4018\r\n"             │ │
│  │                                                            │ │
│  │  测量: △T = 32μs │ 频率 = 1.0MHz │ 占空比 = 50%          │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                 │
│  ┌─ Agent 活动面板 ──────────────────────────────────────────┐ │
│  │                                                            │ │
│  │  10:23:45 🤖 分析 W25Q128 Datasheet, 提取寄存器表          │ │
│  │  10:23:47 🤖 生成 Mock 模型 W25Q128 Level 2               │ │
│  │  10:23:48 🤖 编写 spi_flash.c (版本 v3)                   │ │
│  │           📝 修改: 将 SPI_MODE 从 0 改为 3                │ │
│  │  10:23:52 🤖 编译: ✅ 0 errors, 0 warnings               │ │
│  │  10:23:54 🤖 烧录: ✅ 42.3KB, 1.2s                       │ │
│  │  10:23:55 🤖 复位目标板                                    │ │
│  │  10:23:55 🤖 断言 PASS: JEDEC_ID = EF4018 ✅             │ │
│  │  10:23:56 🤖 断言 PASS: Write 256B → Read verify ✅       │ │
│  │  10:23:57 🤖 开始故障注入测试...                           │ │
│  │                                                            │ │
│  │  [⏸ 暂停Agent] [⏭ 单步] [✋ 覆盖] [💬 对话]              │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                 │
│  ┌─ 协作模式 ────────────────────────────────────────────────┐ │
│  │                                                            │ │
│  │  全自动模式:    Agent 全自主迭代, 工程师只看结果           │ │
│  │  监督模式:      Agent 每步实时显示, 工程师可暂停/修改      │ │
│  │  协作模式:      工程师做硬件决策, Agent 做代码             │ │
│  │  回放模式:      Agent 完成后, 工程师回放审核全过程         │ │
│  │                                                [当前: 监督]│ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 9.4 以太网 TAP（网络分析扩展）

对于需要以太网通信的嵌入式项目，AgentProbe 通过外置 1 分 2 以太网 TAP 模块提供网络可观测性。

**方案设计：**

```
原始连接:
  目标板 ─── [RJ45] ─── 网络/路由器

使用 TAP 后:
  目标板 ─── [RJ45 IN] ─┬─ [RJ45 OUT] ─── 网络/路由器
                         │
                    [TAP 镜像口]
                         │
                    [AgentProbe]
                    USB-Ethernet 适配
                    或板载 MAC+PHY

TAP 硬件方案:
  方案 A (推荐, 外置模块):
    - 独