# NEXT — 跨 session 交接

_每次 session 结束更新此文件，让下一轮从这里续上。格式短、用 bullet。_

## Current Plan
（尚无 epic plan 进入执行。等架构师 agent 在 `docs/plans/` 下产出第一个 epic plan
并由人作为 goal 喂给 Codex 后，在此填写 `docs/plans/E<N>-*.md`。）

## Current Focus
- 项目刚完成架构 v0.2.0 重写 + 契约 0.2.0 + 长循环协议脚手架。
- 实现进度：tasks.md 的 T-01..T-03 已完成（契约 / monorepo / replay-first loop）。
- 下一个待规划的 epic：T-04 起（device identity topology + 单板地基），见 tasks.md。

## Last Action
- 建立长循环协议脚手架：NORTH_STAR.md / LOOP.md / NEXT.md / docs/decision.md / journal 目录。
- 工程清理：删 _bmad/，归档旧 docx+html，.gitignore 忽略本地工具目录。

## Next Action
- 等架构师 agent 出第一个 epic plan（建议 E1 = T-04/05/06，device identity + SoM 契约 + 单板地基）。
- Codex 拿到该 plan 后按 LOOP.md 执行；当前无可自动推进项（无 plan 即不启动 goal）。

## Open BLOCKs
- （无软件阻塞。硬件类阻塞会在对应 epic plan 进入 B 类门时出现。）
