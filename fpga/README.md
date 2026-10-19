# EHand FPGA Subsystem (GW5AT-138)

本目录为 EHand 板载高云 Arora-V 晨熙五代 **GW5AT-LV138PG484AC1/I0** FPGA 协处理器工程。

## 1. 模块架构

- `src/event_sampler.v`：硬件微秒时间戳（25MHz -> 1µs）、20 路 GPIO 边沿捕获引擎、2048 深度 BSRAM 事件 FIFO 与 BAR2 MMIO 寄存器映射。
- `src/ehand_gpio.cst`：MSOC 30PIN FPC 扩展口的 20 路 3.3V LVCMOS 引脚约束文件（对齐 `docs/wiring-plan.md`）。
- `sim/tb_event_sampler.v`：自检仿真激励，Icarus Verilog 100% 验证通过。
- `build.tcl`：Gowin EDA 批处理综合与布局布线脚本。

## 2. Windows 宿主机 (Doctor) 构建指南

### 2.1 环境要求
- Gowin EDA（云源软件 For Win V1.9.12 或更高版本）
- 载入 `gowin_E_C0742BFDC005.lic`（网卡 MAC 设为 `C0:74:2B:FD:C0:05`）

### 2.2 命令行一键综合
在 Windows PowerShell 或 CMD 中：
```cmd
cd fpga
gw_sh.exe build.tcl
```
或直接用 Gowin IDE 打开工程将 `src/event_sampler.v` 与 `src/ehand_gpio.cst` 添加至项目，点击 **Run All (Synthesize -> Place & Route)**。

### 2.3 产物输出
生成比特流路径：
`impl/pnr/ehand_sampler.fs`

将 `.fs` 文件推至 Git 仓库或直接在飞书发回，鲲鹏板端通过 `openFPGALoader -m ehand_sampler.fs` 即可完成 3 秒热加载。
