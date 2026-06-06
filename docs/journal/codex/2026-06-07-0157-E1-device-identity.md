# Journal 2026-06-07 (codex / E1-device-identity)

## 01:57 - Session start
- 读 NORTH_STAR.md / NEXT.md / LOOP.md / E1 plan / tasks.md / architect journal
- git: 从 main 创建 work/v01a；main 本地 ahead 5，未回滚
- Focus: E1 AC1-7 / IT1-2，先做协议常量 + devices/topology/guard + device status

## 02:10 - E1 软件实现
- 新增 `agentprobe.devices`：topology schema 加载、state-changing action guard
- 新增 `UsbTransport.info()` 控制面解析路径；未连接 USB 时返回 unknown，不冒充硬件在线
- `device status` 无 topology 返回 unknown；有 topology 时列出声明身份但硬件状态仍 unknown
- 协议常量由 `protocol.toml` 生成到 Python/C/Verilog；`ap_shared.h` 改为包含生成头

## 02:20 - 验证
- cmd: `$env:PYTHONPATH='cli/src;.'; python -m pytest cli/tests/unit`
- result: PASS (16 passed)
- cmd: `python -m compileall -q cli\src`
- result: PASS
- cmd: `$env:PYTHONPATH='cli/src;.'; python cli\tools\generate_protocol.py --check`
- result: PASS，生成常量 hash 输出正常
- cmd: `$env:PYTHONPATH='cli/src'; python -m agentprobe scenario run --replay --json`
- result: PASS，`terminal_state=regression_pass`，outcome/evidence schema 测试覆盖
- cmd: `device status --json` / `device status --topology scenarios\topologies\self-hosting-two-board.json --json`
- result: PASS，无 topology 为 `unknown`；有 topology 可读声明身份但 USB 未连接仍 `unknown`

## 02:29 - 硬件边界
- firmware: `cmd.exe /d /s /c "call ...VsDevCmd.bat -arch=x64 && cmake -S firmware -B firmware\build-vs -G Ninja && cmake --build firmware\build-vs"` PASS；interface target 无产物
- fpga: 本机 PATH 未找到 make/yosys/svlint/slang/iverilog/verilator/vivado，未能执行 RTL 仿真；未声明 HW2 PASS
- handoff: 写 `docs/handoff/E1-som-selection.md`、`docs/handoff/E1-single-board-bringup.md`
- BLOCK: DEC1 SoM SKU 选定；真机 bring-up / PL selftest 需人工硬件环境
