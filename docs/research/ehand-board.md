# EHand Board 硬件事实（Kunpeng AI Pro + OrangePi MSOC）

> Issue #2（wayfinder map #1）。已在实机上（192.168.1.111）通过物理烧录与总线读写验证。

## 1. 硬件架构概览

EHand Board 由「鲲鹏宿主机」+「高云 FPGA 子板」通过高速 M.2 / PCIe 组合构成：

| 部件 | 规格型号 | 角色分工 |
|---|---|---|
| **Host 宿主机** | 华为昇腾 310B4（Kunpeng AI Pro 16G） | 4核 ARMv8 64位，16GB LPDDR4X，Ubuntu 22.04 LTS。负责 `ehand` CLI、协议语义处理（Modbus 等）、Timeline 组装与持久化、对外通信 |
| **FPGA 子板** | 香橙派 OrangePi MSOC（GW5AT-LV138PG484AC1/I0） | 高云晨熙五代 138K LUTs。负责物理引脚精确时钟采样、UART/485 硬实时收发、硬件时间戳、故障注入（Timing Injections） |
| **主总线** | PCIe Gen2 x4（`22c2:1100`） | 宿主机与 FPGA 高速低时延互联。BAR0（64KB，SGDMA 与控制寄存器），BAR2（256MB 用户逻辑） |
| **辅助总线** | 板载 FT2232 双通道 USB | 通道 A 为 JTAG（`/dev/ttyUSB0`，openFPGALoader 烧录）；通道 B 为 UART（`/dev/ttyUSB1`，直连 FPGA Y19/U20） |

## 2. FPGA 资源与引脚分配（已实测验证）

### 2.1 基础时钟与接口
- **主时钟**：25MHz 晶振，引脚 `V18`（`IO_TYPE=LVCMOS33`）。
- **专用宿主 UART**：RXD=`Y19`，TXD=`U20`，已实测与宿主机 `/dev/ttyUSB1` 在 9600 波特率下全双工通信正常。
- **JTAG 链路**：FT2232 经 M.2 金手指连接，IDCODE `0x0011081b`，实测支持 SRAM 临时载入与 SPI Flash 固化。

### 2.2 30-PIN FPC 扩展接口（用于 EHand Target Board Wiring）
0.5mm 间距 30PIN FPC 扩展座，引出 20 路 3.3V LVCMOS GPIO：

| FPC 引脚 | 信号名称 | FPGA 引脚 | 说明 |
|---|---|---|---|
| Pin 1, 2 | VBUS | - | 电源输入 / 输出 |
| Pin 3, 4 | GND | - | 地 |
| Pin 5 | DeBug_4 | `E21` | 高速调试 / 观测 |
| Pin 6 | DeBug_2 | `G21` | 高速调试 / 观测 |
| Pin 7 | DeBug_3 | `D21` | 高速调试 / 观测 |
| Pin 8 | DeBug_1 | `G22` | 高速调试 / 观测 |
| Pin 9 | 2_IO8 | `B22` | 通用 Channel IO |
| Pin 10 | 1_IO8 | `B21` | 通用 Channel IO |
| Pin 11 | 2_IO7 | `A21` | 通用 Channel IO |
| Pin 12 | 1_IO7 | `B20` | 通用 Channel IO |
| Pin 13 | 2_IO6 | `A20` | 通用 Channel IO |
| Pin 14 | 1_IO6 | `A19` | 通用 Channel IO |
| Pin 15 | 2_IO5 | `B18` | 通用 Channel IO |
| Pin 16 | 1_IO5 | `A18` | 通用 Channel IO |
| Pin 17 | 2_IO4 | `B17` | 通用 Channel IO |
| Pin 18 | 1_IO4 | `A16` | 通用 Channel IO |
| Pin 19 | 2_IO3 | `B16` | 通用 Channel IO |
| Pin 20 | 1_IO3 | `A15` | 通用 Channel IO |
| Pin 21 | 2_IO2 | `B15` | 通用 Channel IO |
| Pin 22 | 1_IO2 | `A14` | 通用 Channel IO |
| Pin 23 | 2_IO1 | `B13` | 通用 Channel IO |
| Pin 24 | 1_IO1 | `A13` | 通用 Channel IO |
| Pin 25, 26| NC | - | 空脚 |
| Pin 27, 28| VCC3V3 | - | 3.3V 辅助供电 |
| Pin 29, 30| GND | - | 地 |

### 2.3 板载外设与状态指示
- **LED（16路）**：`N13`, `P14`, `R14`, `N14`, `P15`, `P16`, `R16`, `P17`, `T18`, `R18`, `R17`, `W22`, `Y22`, `AA21`, `AB22`, `AB21`（低电平点亮）。实测 `N13` 闪烁正常。
- **按键（4个）**：`V20`, `W19`, `W20`, `W21`。
- **数码管（2x4位）**：段码 `M21, L21, M17, J22, H22, K21, K22, J20(DP)`，位选 `K17, J17, L14, L15` / `L16, M16, H20, G20`。
- **拨码开关（2x8位）**：`U18, U17, W17, V17, AA19, AA18, AB18, AB20` / `V10, AB12, W10, AA11, AA10, AB11, AA9, AB10`。
