# NEXT — 跨 session 交接

_每次 session 结束更新此文件，让下一轮从这里续上。格式短、用 bullet。_

## Current Plan
- `docs/plans/E1-device-identity-single-board.md`（T-04/05/06）— 软件验收门已完成；硬件/采购项交还人工。

## Current Focus
- E1：设备身份/拓扑 + 单板地基。T-04 软件实现完成；T-05/06 交接物完成，真实硬件 bring-up 未做。
- 项目已完成：架构 v0.2.0 + 契约 0.2.0 + 长循环协议脚手架 + E1 plan + E1 软件门控/拓扑/交接物。

## Last Action
- Codex 完成 E1 软件侧：devices topology/guard、USB status 解析路径、协议常量生成、双板 topology 样例、SoM/bring-up 交接文档。
- 验证：`pytest cli/tests/unit` 17 passed；`compileall` PASS；`generate_protocol.py --check` PASS；replay 输出 `regression_pass`；device status 无 topology/无 USB 均为 `unknown`。
- firmware CMake 在 VS DevCmd + Ninja 下 PASS（interface target，无产物）；FPGA smoke 结构检查 PASS；Icarus Verilog 11.0 临时解包运行 `python fpga/tools/run_sim.py` PASS（`AP_TOP_SMOKE_PASS`），未声明真实 PL selftest PASS。

## Next Action
- 人工：处理 DEC1 SoM SKU 选定，并按 `docs/handoff/E1-single-board-bringup.md` 执行真机 bring-up。
- Codex 下一轮可从新的 epic plan 继续；不要把 E1 的真机结果伪装成软件验证。

## Open BLOCKs
- DEC1（人工）：SoM SKU 选定 — 参考 `docs/handoff/E1-som-selection.md`。
- HW1（人工/真机）：单板 bring-up — 步骤见 `docs/handoff/E1-single-board-bringup.md`。
- HW2（工具链/硬件）：`cli/tests/unit/test_fpga_smoke.py` 已做最小 RTL/testbench 结构检查；`python fpga/tools/run_sim.py` 已用临时 Icarus Verilog 11.0 跑通 smoke 仿真。真实 PL selftest 仍需硬件环境。
