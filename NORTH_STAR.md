# NORTH STAR — AgentProbe

**只读，禁改。** 这是方向锚（Theme 层），不是任何 goal 的完成条件。
goal/epic 的"done"由 `docs/plans/E<N>-*.md` 各自定义；本文件只回答"我们朝哪走、什么不能破、最终赢的样子"。

---

## 项目终极目标（给人看的北极星）

让 AI Agent 第一次能自主验证嵌入式代码在物理世界里是否真的工作。

最终成功 = **two-board self-hosting loop 在真机上跑通**：一块稳定的 Golden AgentProbe
帮助 Agent 开发、烧录、观测、诊断、修复一块 DUT AgentProbe，全程产出可审计证据，
至少覆盖 1 条正常路径 + 1 条异常/失败路径。

> 此目标的**真机验收由人工完成**，超出任何单个 Codex goal 的范围。
> Codex 的 goal 只对应一个 epic plan，能否完成由那个 plan 的 Goal Done 判定。

权威技术架构见 `ARCHITECTURE.md`。产品动机见 `archive/`。

---

## 跨 epic 不变量（每个 epic 都必须守，违反即失败）

这些约束高于任何单个 plan，任何 goal 都不得为了"完成"而破坏它们：

- **INV-1 能力面/推理面分离（ARCHITECTURE P9）**：能力服务层是无头核心，对外只暴露
  transport-agnostic 的稳定语义契约；CLI/GUI/MCP 是平级客户端；真相源是声明式文件 + 证据库。
- **INV-2 身份门控（P5）**：所有 state-changing action 必须绑定 device identity + topology；
  缺字段返回 `unknown` / `approval_pending`，绝不输出成功 verdict。
- **INV-3 大声失败（AGENTS.md §11）**：仿真 / replay / mock 通过 **≠** 真机验证通过；
  任何 mock 产出的证据必须带 `mock_fidelity` provenance。绝不把软件级通过谎报为物理验证。
- **INV-4 Golden 不可被 Agent 自动升级**：`golden_upgrade_mode` 默认 disabled，需人工授权。
- **INV-5 Contract-first SSOT（P2）**：跨域常量由 `protocol.toml` / `address_map.toml` 生成 +
  sha256 强校验；契约版本一致（当前 0.2.0）。

---

## 软件 vs 硬件（决定 goal 能否收敛）

Codex 在 goal 模式里**碰不到真实 Zynq 板**。因此每个 epic plan 必须把工作分成两类：

- **软件可验证（计入 Goal Done）**：契约、replay、CLI、host 侧 mock 逻辑、RTL 仿真、
  固件交叉编译、单测 / 集成测试。Codex 自己就能闭环。
- **需真实硬件 / 人工（不计入 Goal Done）**：真机 bring-up、SWD 烧录、真机观测、
  真机 self-hosting、SPI mock 上板。Codex 只写到"可上板交接物"程度
  （编译过 + 仿真过 + `docs/handoff/<item>.md` 上板步骤），然后按 LOOP.md §3 hard-stop。

> 一个 goal 命中硬件门 = 那个 epic 的软件部分做完了，**这是正常完成，不是失败**。
