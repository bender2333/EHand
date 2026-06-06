# Decisions — AgentProbe

_阻塞级 / 方向级决策记录。每条：Q（问题）/ Decision（决定）/ Why（理由）/ Date。_
_日常小决策进 journal；只有影响架构或流程的进这里。_

---

## D-1 — plan = goal = epic（长循环驱动模型）
**Date:** 2026-06-06
**Decision:** Codex 用 goal 模式驱动；一个 goal 对应一个 epic plan（`docs/plans/E<N>-*.md`）。
plan 由架构师 agent 产出，**自带 Goal Done + 集成测试标准 + 硬件交接物**。
**Why:** 用户用敏捷层级类比 —— Theme（NORTH_STAR）/ Epic（一个 goal）/ Story / Task。
plan 自包含验收标准，goal 才能独立收敛。

## D-2 — NORTH_STAR 不含 done 判定
**Date:** 2026-06-06
**Decision:** NORTH_STAR.md 瘦身为纯 Theme：方向 + 跨 epic 不变量 + 最终成功画像，**不含任何验收门**。
验收门下放到各 epic plan。
**Why:** 验收门是 epic 级 done，塞进 NORTH_STAR 会把"方向锚"和"完成条件"混淆，
导致 goal 永远无法完成（真机门够不到）。这是设计中纠正的一个硬伤。

## D-3 — 硬件边界 = 硬停 + 交接物
**Date:** 2026-06-06
**Decision:** Codex 在 goal 循环里碰不到真实 Zynq 板。需真机的步骤（B 类）写到"可上板交接物"
程度（编译过 + 仿真/replay 过 + `docs/handoff/<item>.md` 上板步骤），然后 hard-stop（LOOP.md §3）。
真机执行划归人工验收，不计入 Goal Done。
**Why:** 否则长循环会在第一个硬件任务（T-06 单板 bring-up）撞墙，要么空转要么造假，
违反 INV-3 大声失败。

## D-4 — 自治跨度：连续推进直到 Goal Done
**Date:** 2026-06-06
**Decision:** 一次 goal 循环连续推进多个 task，直到当前 epic plan 的 Goal Done 达成，
或命中 LOOP.md §3 硬边界。context 将满不停（自动压缩接管 + NEXT.md/journal/commit 续上）。
**Why:** 用户要求最大化自治吞吐；context 压缩已能保证续跑，无需为此中断。

## D-5 — 单一长期工作分支 work/v01a
**Date:** 2026-06-06
**Decision:** Codex 自动提交全程在 `work/v01a`，禁止直接提交 main，不自动开 PR / 并 main，等人工合并。
**Why:** 隔离自动产出与稳定 main，人工保留合并闸门。

## D-6 — 弃用 docs/superpowers/plans/，统一 docs/plans/
**Date:** 2026-06-06
**Decision:** epic plan 统一放 `docs/plans/`。AGENTS.md 里 children-story-site 的 superpowers 路径
是旧项目残留，已弃用。
**Why:** 那条路径与 AgentProbe 无关，是复制残留。
