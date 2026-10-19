# GW5AT-138 硬件微秒时间戳与引脚边缘采样 FIFO 架构规范 (Issue #14)

## 1. 时钟基准与时间戳引擎 (Timestamp Engine)

### 1.1 硬件时钟源
- **输入晶振**：25.000 MHz 差分/单端时钟（引脚 `V18`，3.3V LVCMOS）。
- **基准周期**：1 个时钟周期 = 40.000 ns。

### 1.2 微秒分频器与计数器
- **微秒生成**：采用 5-bit 预分频计数器（模 25），每计满 25 个周期（0~24）产生 1 个精准的 1µs 节拍脉冲（Tick）。
- **时间戳寄存器**：
  - `timestamp_us[63:0]`：64 位无符号微秒计数器，自 FPGA 上电或复位起单调自增。
  - 64 位微秒上限为 $1.84 \times 10^{19}$ µs（超过 58 万年），彻底消除溢出回绕风险。
  - 亚微秒精度（可选）：当前 40ns 计数偏移 `sub_us[4:0]`，供纳秒级分析使用。

---

## 2. 20 路 GPIO 边沿捕获引擎 (Edge Capture Engine)

### 2.1 信号同步与消抖
- 对 30PIN FPC 扩展口的 20 路 GPIO（LVCMOS 3.3V）建立两级同步触发器（Flip-Flops）消除亚稳态。
- 边沿检测逻辑：
  ```verilog
  wire [19:0] gpio_rise = (~gpio_sync_d1) & gpio_sync_d0;
  wire [19:0] gpio_fall = gpio_sync_d1 & (~gpio_sync_d0);
  ```

### 2.2 事件帧紧凑编码 (64-bit Event Word)
为实现 PCIe 与 SGDMA 的高吞吐、零内存拷贝消费，每个 GPIO 边沿变化打包为 64-bit 结构体：

| 位域 (Bit) | 字段名 | 说明 |
|---|---|---|
| `[63:32]` | `timestamp_us_low` | 事件发生的 32 位硬件微秒时间戳（约 71.5 分钟回绕，配合主机维护高 32 位） |
| `[31]` | `overflow_flag` | 硬件 FIFO 溢出标志（1 表示该事件之前发生过 FIFO 丢包） |
| `[30:28]` | `reserved` | 预留备用 |
| `[27:24]` | `edge_type` | 边沿类型：`0x1`=上升沿，`0x2`=下降沿，`0x3`=电平保持采样 |
| `[23:16]` | `channel_id` | 物理引脚编号（0 ~ 19，对应 `GPIO[0]` 到 `GPIO[19]`） |
| `[15:0]` | `pin_snapshot` | 触发瞬间引脚 0~15 的瞬时电平快照（16 位位图），方便多线同步诊断 |

---

## 3. 硬件 FIFO 拓扑与存储预算

### 3.1 FIFO 规格
- **存储介质**：利用 GW5AT-138 片上 Block SRAM (BSRAM)。
- **深度**：2048 深度 $\times$ 64-bit（共 16KB 缓存空间）。
- **吞吐上限**：在 115200 波特率下，UART 每秒约 1.15 万字符（约 11.5 万个电平变化）。2048 深度可独立缓存 ~17.8 毫秒突发总线流量，完全平抑 Linux 用户态进程或 PCIe DMA 调度抖动。

### 3.2 寄存器接口与访问模式 (BAR2 MMIO)

在 PCIe BAR2 空间（直通 `mmap`）映射控制与数据寄存器：

| 偏移地址 | 寄存器名 | 读/写 | 描述 |
|---|---|---|---|
| `0x0010` | `EVENT_FIFO_STATUS` | RO | `[15:0]`：FIFO 当前条目数；`Bit 30`：FIFO 空；`Bit 31`：FIFO 满/溢出 |
| `0x0014` | `EVENT_FIFO_DATA_LO` | RO | 当前事件帧 `[31:0]`（读取自动弹栈或配对读取） |
| `0x0018` | `EVENT_FIFO_DATA_HI` | RO | 当前事件帧 `[63:32]` |
| `0x001C` | `EVENT_FIFO_CTRL` | RW | `Bit 0`：FIFO 清空复位；`Bit 1`：边沿捕获全局使能 |

---

## 4. 异常与溢出处理策略 (Fact Flag Integration)

1. **溢出锁定 (Sticky Overflow)**：当 FIFO 满且新边沿发生时，FPGA 硬件进入溢出锁定态，丢弃新事件并置位溢出标志。
2. **主机通知**：通过 PCIe 中断（MSI）或主机轮询感知 FIFO 超过高水位线（如 75%）。
3. **Timeline 事实对接**：主机读取到 `overflow_flag == 1` 时，向 EHand Timeline 数据库追加记录一条 Fact Flag：`FPGA_FIFO_OVERFLOW`，标明硬件采样断流区间，完全符合 ADR-0003 客观事实原则。
