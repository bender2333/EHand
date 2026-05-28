│  ┌─ Event FIFO ────────────────────────────────────────────┐ │
│  │                                                          │ │
│  │  统一事件收集 FIFO:                                      │ │
│  │  - 所有 Mock Engine / Protocol Decoder / GPIO 产生的事件 │ │
│  │    汇聚到统一 FIFO                                       │ │
│  │  - FIFO 深度: 4096 条事件                                │ │
│  │  - 事件格式 (固定 16 字节):                              │ │
│  │    [timestamp 4B][source 1B][type 1B][length 1B]         │ │
│  │    [reserved 1B][data 8B]                                │ │
│  │  - MCU 通过 SPI 批量读取                                 │ │
│  │  - FIFO 半满时触发 FPGA_IRQ 通知 MCU                     │ │
│  │  - 溢出保护: 溢出时丢弃最旧事件并置标志                  │ │
│  └──────────────────────────────────────────────────────────┘ │
│                                                               │
│  ┌─ GPIO / PWM Engine ─────────────────────────────────────┐ │
│  │                                                          │ │
│  │  GPIO (16 路):                                           │ │
│  │  - 每路可独立配置: 输入/输出/开漏                        │ │
│  │  - 输出值由 MCU 寄存器控制                               │ │
│  │  - 输入变化检测 (双沿) → Event FIFO                     │ │
│  │  - 可配置上拉/下拉 (FPGA 内部弱上拉)                    │ │
│  │                                                          │ │
│  │  PWM 输出 (8 路):                                        │ │
│  │  - 16bit 周期 + 16bit 占空比                             │ │
│  │  - 基于 clk_50m 分频                                     │ │
│  │  - 频率范围: 约 763Hz 至 25MHz                           │ │
│  │                                                          │ │
│  │  PWM 输入捕获 (8 路):                                    │ │
│  │  - 测量频率和占空比                                      │ │
│  │  - 32bit 计数器 @ clk_50m                                │ │
│  │  - 结果通过寄存器读取                                    │ │
│  └──────────────────────────────────────────────────────────┘ │
│                                                               │
└──────────────────────────────────────────────────────────────┘
```

### 7.4 上位机 Desktop GUI 设计

```
技术栈: Electron + React + TypeScript
通信: 通过 Core Service 的 REST API + WebSocket

主要视图:

┌─ 主界面布局 ──────────────────────────────────────────────────┐
│                                                                │
│  ┌─ 顶部工具栏 ─────────────────────────────────────────────┐ │
│  │ [连接状态] [Session: sensor_board_v1 ▼] [模式: Mock ▼]   │ │
│  │ [录制 ●] [回放 ▶] [截图] [设置 ⚙]                       │ │
│  └───────────────────────────────────────────────────────────┘ │
│                                                                │
│  ┌─ 左侧面板 (设备树) ─┐ ┌─ 中央区域 (主视图,可切换) ─────┐ │
│  │                      │ │                                 │ │
│  │  ▼ AgentProbe #1     │ │  [波形] [协议] [终端] [Agent]  │ │
│  │    ├─ 🟢 SWD          │ │                                 │ │
│  │    │   └─ STM32F407   │ │  ┌─ 信号波形视图 ────────────┐│ │
│  │    ├─ Mock Devices    │ │  │                            ││ │
│  │    │   ├─ 🟢 W25Q128  │ │  │  SCK  ─┐┌┐┌┐┌┐┌┐┌─────  ││ │
│  │    │   ├─ 🟢 SHT30    │ │  │  MOSI ─┤├┤├┤├─── 9F 00   ││ │
│  │    │   └─ 🟡 MCP2515  │ │  │  MISO ─┤├┤├┤├─── FF EF   ││ │
│  │    ├─ Analyzers       │ │  │  CS   ─┘└──────┘└─────     ││ │
│  │    │   ├─ SPI #0      │ │  │                            ││ │
│  │    │   ├─ I2C #0      │ │  │  ▲ [READ_JEDEC_ID] → EF   ││ │
│  │    │   └─ UART #0     │ │  │    4018 (Winbond W25Q128)  ││ │
│  │    ├─ Analog          │ │  │                            ││ │
│  │    │   ├─ DAC x4      │ │  └────────────────────────────┘│ │
│  │    │   ├─ ADC x4      │ │                                 │ │
│  │    │   └─ INA219      │ │                                 │ │
│  │    └─ GPIO (16ch)     │ │                                 │ │
│  │                      │ │                                 │ │
│  └──────────────────────┘ └─────────────────────────────────┘ │
│                                                                │
│  ┌─ 底部面板 (日志/事件) ──────────────────────────────────┐  │
│  │ [事件流] [串口终端] [Agent 日志] [测试结果]              │  │
│  │                                                          │  │
│  │ 10:23:45.123 SPI #0 READ  addr=0x9F → EF 40 18         │  │
│  │ 10:23:45.130 UART RX: [LOG] JEDEC ID: EF4018\r\n       │  │
│  │ 10:23:45.200 SPI #0 WRITE addr=0x06 (WRITE_ENABLE)     │  │
│  │ 10:23:45.210 SPI #0 WRITE addr=0x02 data=48656C6C6F    │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                │
└────────────────────────────────────────────────────────────────┘

关键视图说明:

  1. 波形视图: 类似 Saleae Logic 的信号时序显示
     - 缩放/平移/测量
     - 协议解码叠加显示
     - 光标和测量工具

  2. 协议视图: 表格形式的协议解码数据
     - 按事务列出
     - 可过滤/搜索
     - 点击定位到波形

  3. 终端视图: 串口终端
     - 支持多路串口 (UART 嗅探 + RTT + Semihosting)
     - 发送/接收
     - 日志高亮和过滤

  4. Agent 视图: Agent 活动监控
     - Agent 操作日志 (实时)
     - 当前代码 diff
     - 编译输出
     - 测试结果
     - [暂停] [单步] [覆盖] [对话] 按钮

  5. 配置视图: I/O 路由可视化配置
     - 拖拽式引脚映射
     - Mock 模型选择和参数配置
     - 模拟通道配置
```

### 7.5 CLI 工具设计

```
工具名: agentprobe (简写 ap)
语言: Python (基于 Click 框架)
安装: pip install agentprobe

命令结构:

  ap connect                     # 连接 AgentProbe 设备
  ap status                      # 显示设备和目标板状态
  ap info                        # 显示设备固件版本/FPGA版本等

  # Session 管理
  ap session load <file.yaml>    # 加载 Session 配置
  ap session save <file.yaml>    # 保存当前配置
  ap session list                # 列出可用 Session

  # Mock 管理
  ap mock load <model> [options] # 加载 Mock 模型
  ap mock list                   # 列出已加载的 Mock
  ap mock state <device>         # 查询 Mock 设备状态
  ap mock set <device> <param>   # 设置 Mock 参数
  ap mock inject <device> <fault># 注入故障

  # I/O 路由
  ap io route <pin> <function>   # 配置引脚路由
  ap io status                   # 显示当前路由表

  # 调试
  ap target flash <firmware>     # 烧录固件
  ap target reset                # 复位目标板
  ap target power <on|off>       # 电源控制
  ap target detect               # 检测目标 MCU

  # 信号捕获
  ap capture start [options]     # 开始信号捕获
  ap capture stop                # 停止捕获
  ap capture export <file>       # 导出捕获数据

  # 模拟
  ap analog dac <ch> <voltage>   # 设置 DAC 输出
  ap analog adc <ch>             # 读取 ADC
  ap analog current              # 读取电流

  # 事件监控
  ap monitor [--filter=spi,uart] # 实时监控事件流
  ap monitor --json              # JSON 格式输出 (Agent 友好)

  # 测试
  ap test run <test_suite.yaml>  # 运行测试套件
  ap test report <output>        # 生成测试报告

  # 固件更新
  ap firmware update <file>      # 更新 MCU 固件
  ap firmware update-fpga <file> # 更新 FPGA bitstream

示例:

  # 快速开始: 加载配置, 烧录, 监控
  $ ap session load sensor_board_v1.yaml
  $ ap target flash build/firmware.elf
  $ ap target reset
  $ ap monitor --filter=spi_0,uart_0

  # Agent 脚本调用示例
  $ ap mock state w25q128 --json
  {
    "device": "w25q128",
    "status_reg": "0x00",
    "write_enable": false,
    "busy": false,
    "memory_written_bytes": 0,
    "transactions": 0
  }
```