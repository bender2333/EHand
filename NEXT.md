# NEXT — 跨 session 交接

_每次 session 结束更新此文件，让下一轮从这里续上。格式短、用 bullet。_

## Current Plan
- `docs/plans/E1-device-identity-single-board.md`（T-04/05/06）— Ready，可作为 goal 喂给 Codex。

## Current Focus
- E1：设备身份/拓扑 + 单板地基。T-04 纯软件可完整做完；T-05/06 会停在硬件交接物。
- 项目已完成：架构 v0.2.0 + 契约 0.2.0 + 长循环协议脚手架 + E1 plan。

## Last Action
- 架构师产出第一个 epic plan：E1（自带 Goal Done AC1-7 + 集成测试 IT1-2 + 硬件交接物 HW1-2 + 人工决策 DEC1）。

## Next Action
- Codex：以 E1 plan 为 goal，按 LOOP.md 从 S1（devices 模块骨架）开始推进。
- Goal Done = E1 plan 的 AC1-7 全绿 + 交接物齐。命中硬件门（HW1/HW2/DEC1）→ hard-stop 交还。

## Open BLOCKs
- DEC1（人工）：SoM SKU 选定 — 等 Codex 产出 `docs/handoff/E1-som-selection.md` 候选后由人决策。
