# LOOP — 长任务自动闭环协议（Codex / goal 模式）

**触发**：用户说"自动推进 / 闭环做完"或 `/loop`，并把一个 epic plan（`docs/plans/E<N>-*.md`）作为 goal 喂入。
架构与计划已由人 + 架构师 agent 定好；本协议只管"如何把这个已定 plan 自动执行到底"。

**一个 goal = 一个 epic plan。** goal 的"done"= 该 plan 的 **Goal Done + 集成测试标准**全绿，
且所有需硬件的部分已产出可上板交接物。不要超出当前 plan 的 Scope。

---

## §1 循环体（每一轮）

1. 读 `NEXT.md` 的 Next Action，确认当前 epic plan 和当前 story。
2. 读当前 `docs/plans/E<N>-*.md`：Scope / Stories / Goal Done / 集成测试标准 / 硬件交接物 / 不变量。
3. `todowrite` 把当前 story 拆成带 verify 的小步（AGENTS.md §4 目标驱动）。
4. 实现一个小块 → 立即 verify（见 §2）。
5. verify 通过 → commit + push（§5）→ 写一条 codex journal。
6. 回到 1，连续推进下一个小块 / 下一个 story / 下一个 plan 内的 task，**不停**（见 §4）。

---

## §2 验收门两类（核心判定）

每个 plan 的 Goal Done 条目都标了类别：

- **A 类（软件可验证）**：Codex 自己跑命令就能判定 done。
  典型：`pytest cli/tests`、`python -m compileall cli/src`、`generate_protocol.py --check`、
  jsonschema 校验、RTL testbench 仿真、固件交叉编译。→ **通过即推进，不停。**
- **B 类（需真实板 / 人工）**：Codex 把代码写到"可上板"程度
  （编译过 + 仿真/replay 过 + `docs/handoff/<item>.md` 写好上板步骤），然后 **hard-stop（§3）**。
  **绝不假装真机通过**（INV-3）。

---

## §3 硬边界（命中即停：写 NEXT.md open BLOCKs + journal，然后停，不要猜）

- **需要真实 Zynq 硬件**才能继续（B 类门已写到可上板交接物）。
- **真歧义**：当前 plan / NORTH_STAR / ARCHITECTURE / tasks 都给不出答案的设计抉择。
- **不可逆操作**：改 git 历史、删非自己产出的文件、动 `main`、动 git config。
- **同一问题连续失败 2 次**：停下做根因分析，换根本思路；仍不行则升级，不要增量打补丁。
- **要破坏任一不变量（INV-1..5）才能"完成"**：停，这是 plan 或架构的问题，升级。

---

## §4 不停的情况（明确允许连续自治推进）

- **context 将满：不要为此停。** 自动压缩会接管；靠 NEXT.md + journal + 已 push 的 commit 续上。
  不要为多撑 context 而疯狂压缩或仓促收尾。
- **一个 story / task 完成**：继续当前 plan 内下一个 A 类可做的工作。
- **目标 = 把当前 epic plan 推进到 Goal Done。** 在此之前，除 §3 外不主动交还。

---

## §5 Git（自动 commit + push）

- **工作分支 `work/v01a`**，禁止直接提交 `main`。首次 `git push -u origin work/v01a`。
- 每个 verify 通过的小块提交一次，conventional commits（`fix:`/`feat:`/`docs:`/`chore:`）。
  有验证产物时带 `Verified-By:` trailer；纯文档可省。
- 每次 commit 后 push 到 origin 工作分支。
- **不自动开 PR、不自动并 main、不用交互式 git（`-i`）、不加 `--no-verify`、不动 git config。**

---

## §6 Subagent / 上下文卫生

- **扇出型工作一律派 subagent**：多文件读、跨目录搜、调研模块、跑多组验证、审查一片代码。
  主线只收结论，不收被读文件原文。
- **结构性问题用 `codegraph_*` / serena**（谁调谁、改 Z 会炸什么、X 签名），不为查符号先 grep。
- **实现类工作**（连续改同一批文件）留主线，别派出去。
- 每次 subagent 派发 + 结论记一行 codex journal。

---

## §7 收尾（命中 §3 或当前 plan 达成 Goal Done）

1. 追加 codex journal（按 AGENTS.md 日志分流：`docs/journal/codex/YYYY-MM-DD-HHMM-<topic>.md`）。
2. 更新 `NEXT.md`：current plan / current focus / last action / next action / open BLOCKs。
3. 完成的工作 commit + push 到 `work/v01a`。
4. 干净收尾，让下一轮从 NEXT.md 续上。
