# E1 单板 bring-up 交接

## 边界

- 本文是可上板步骤，不声明真机已通过。
- Codex 当前只能完成软件验证、schema 校验、replay 回归、生成常量同步和 host 侧解析路径；真实 Zynq 板连接、烧录、观测由人工执行。

## 准备

- 选定 DEC1 SKU，并记录实际 serial。
- Host 安装 Python CLI 环境、厂商 JTAG/USB 驱动、CMake 或 FPGA 工具链。
- 使用 `scenarios/topologies/self-hosting-two-board.json` 作为起点，替换实际 `serial` 和连接命名。
- Golden 默认 `golden_upgrade_allowed=false`，不要在 agent 自动流程里升级 Golden。

## 接线

- Host 到 Golden：USB-UART 或 USB device。
- Golden 到 DUT：SWDIO、SWCLK、nRESET、VTref。
- Golden 到 DUT：UART TX/RX。
- Golden 到 DUT：SPI SCK/MOSI/MISO/CS。
- Golden 到 DUT：logic analyzer 0..7。
- Golden 到 DUT：3V3 power reference 和 GND。

## 上板步骤

1. 校验 topology：

   ```powershell
   $env:PYTHONPATH='cli/src'
   python -m pytest cli/tests/unit/test_topology_examples.py
   ```

2. 查看声明式身份：

   ```powershell
   $env:PYTHONPATH='cli/src'
   python -m agentprobe device status --topology scenarios/topologies/self-hosting-two-board.json --json
   ```

3. 跑 replay 回归，证明软件闭环未回归：

   ```powershell
   $env:PYTHONPATH='cli/src'
   python -m agentprobe scenario run --replay --json
   ```

4. 交叉编译 firmware 和 RTL，确认产物可上板。

   - 当前仓库只有协议生成头和最小 RTL smoke test，尚未包含可烧录固件或真实 PL selftest。
   - firmware CMake 可在 VS DevCmd + Ninja 下配置/构建。
   - FPGA smoke 仿真入口为 `python fpga/tools/run_sim.py`，需要 `iverilog` + `vvp`；无仿真器环境下，`cli/tests/unit/test_fpga_smoke.py` 只做最小 RTL/testbench 结构检查。

5. 人工烧录 Golden，执行最小 device status / PL selftest。

6. 记录 evidence、串口日志、工具版本和实际接线照片或文字描述。

## 预期信号

- `device status --topology` 能列出 golden/dut/host 三类声明式身份，但在 USB transport 未连接前必须返回 `terminal_state=unknown`，不得冒充真实硬件在线。
- 无 topology 时返回 `terminal_state=unknown` 和 `ERR_UNKNOWN_DEVICE_IDENTITY`，不得返回成功 verdict。
- state-changing action 在缺 identity/topology 时不执行。
- Golden firmware/bitstream upgrade 默认被守卫拒绝。
- replay 输出保持 `terminal_state=regression_pass`，证据 schema version 为 0.2.0。
- `python fpga/tools/run_sim.py` 输出 `AP_TOP_SMOKE_PASS` 才能证明最小 RTL 顶层可编译/可跑 testbench；若只跑 `test_fpga_smoke.py`，只能证明 testbench 与顶层端口声明一致，不等同真实 PL selftest。

## 验收判据

- 软件侧 AC1-AC6 全部通过。
- 本文存在并覆盖接线、步骤、预期信号、失败边界。
- 真机 bring-up 只能由人工确认；未确认前不得把任何硬件路径写成已通过。
