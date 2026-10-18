# EHand V1 Wiring Plan（基于 OrangePi MSOC 30PIN FPC）

> 对应 Issue #7。一处接线，全软件定义（Software-Defined Channels，见 ADR-0002）。

## 1. 物理接口规格

- **连接器**：OrangePi MSOC 板载 0.5mm 间距 30PIN 下接 FPC 排座（30PIN 翻盖插座）。
- **电气标准**：3.3V LVCMOS（全引脚兼容 3.3V MCU；5V MCU 需加电平转换或限流）。
- **供电引出**：
  - Pin 27, 28: `VCC3V3`（最大 500mA 辅助供电，可供电平转换器或 485 收发器）
  - Pin 3, 4, 29, 30: `GND`（与 Target Board 共地）
  - Pin 1, 2: `VBUS`（5V 输入/出）

## 2. 推荐接线脚位定义（Fixed Physical Wiring）

人类工程师仅需将 Target Board 与 MSOC 30PIN FPC 转接板连接一次，后续所有协议分配、波特率、角色均由 Agent 通过 `ehand apply` 声明：

| FPC Pin | 信号名 | FPGA 引脚 | 默认 Channel 绑定 | 目标板（Target Board）连接建议 |
|---|---|---|---|---|
| **Pin 9** | 2_IO8 | `B22` | `channel.uart1.rx` | Target Board UART_TX |
| **Pin 10** | 1_IO8 | `B21` | `channel.uart1.tx` | Target Board UART_RX |
| **Pin 11** | 2_IO7 | `A21` | `channel.rs485.di` | RS485 收发器 DI（发送数据） |
| **Pin 12** | 1_IO7 | `B20` | `channel.rs485.ro` | RS485 收发器 RO（接收数据） |
| **Pin 13** | 2_IO6 | `A20` | `channel.rs485.re_n` | RS485 收发器 RE_N（接收使能，低有效） |
| **Pin 14** | 1_IO6 | `A19` | `channel.rs485.de` | RS485 收发器 DE（驱动使能，高有效） |
| **Pin 15** | 2_IO5 | `B18` | `channel.ntc.pwm` | NTC 模拟量输出（经 10k/100nF RC 滤波接 ADC 输入） |
| **Pin 16** | 1_IO5 | `A18` | `channel.pulse1.out`| 脉冲源 1 输出（方波/脉冲计数测试） |
| **Pin 17** | 2_IO4 | `B17` | `channel.pulse2.out`| 脉冲源 2 输出 |
| **Pin 18** | 1_IO4 | `A16` | `channel.sw1.out` | 开关 1 输出（干接点/高低电平模拟） |
| **Pin 19** | 2_IO3 | `B16` | `channel.sw2.out` | 开关 2 输出 |
| **Pin 20** | 1_IO3 | `A15` | `channel.gpio1.in` | Target Board 输出观测（如 LED/继电器状态） |
| **Pin 21** | 2_IO2 | `B15` | `channel.gpio2.in` | Target Board 输出观测 |
| **Pin 22** | 1_IO2 | `A14` | `channel.gpio3.in` | Target Board 输出观测 |
| **Pin 23** | 2_IO1 | `B13` | `channel.gpio4.in` | Target Board 输出观测 |
| **Pin 24** | 1_IO1 | `A13` | 备用 Channel | 备用 |
| **Pin 5** | DeBug_4 | `E21` | 硬件示波器探针 4 | 内部状态/Trigger 硬件镜像输出 |
| **Pin 6** | DeBug_2 | `G21` | 硬件示波器探针 2 | 内部状态/Trigger 硬件镜像输出 |
| **Pin 7** | DeBug_3 | `D21` | 硬件示波器探针 3 | 内部状态/Trigger 硬件镜像输出 |
| **Pin 8** | DeBug_1 | `G22` | 硬件示波器探针 1 | 内部状态/Trigger 硬件镜像输出 |

## 3. 软件动态可配置性

当 Target Board 的引脚功能调整时，无需拔插跳线：
- 任意通用 IO 引脚在 FPGA 内部由跨线矩阵（Crossbar）互联。
- `uart1`、`pulse`、`switch` 可以通过 TOML 声明任意互换映射（例如把 Pin 9/10 换成 I2C 或 SPI，未来只需更新 FPGA 比特流重映射）。
