# Plan: E1 — 设备身份/拓扑 + 单板地基（goal）

**Epic ID:** E1
**Scope tasks:** T-04（device identity topology）、T-05（SoM baseboard 契约）、T-06（单板 loop 地基）
**Status:** Ready（可作为 goal 喂给 Codex）
**前置:** E0（T-01..03 契约/monorepo/replay-first）已完成。

---

## 服务于北极星

建立"设备身份门控"这条地基（INV-2 / ARCHITECTURE P5）——这是后续一切 state-changing
物理动作（烧录/复位/mock）能安全执行的前提；并把单板硬件通路写到可上板交接物程度，
为最终真机 self-hosting loop 铺第一段路。

---

## Scope

**含：**
- T-04 全量（纯软件，可完整做完）：`devices` 模块 = 设备注册表 + topology validator + role 守卫。
- T-05 软件部分：SoM/baseboard **选型标准文档** + topology 声明文件 schema 落地 + 上板交接物。
- T-06 软件部分：单板通路的 host 侧骨架（`UsbTransport` 接口对齐 + `ap device status` 走真实 transport 的代码路径），RTL/固件写到可编译/可仿真。

**非目标（明确不做）：**
- 不做真机 bring-up（T-06 真机执行 = 人工，NS-B1）。
- 不选定具体 SoM SKU（采购决策 = 人工，见下方人工决策项）。
- 不实现 SWD/analyzer/mock 的运行逻辑（E2/E5）。
- 不引入网络服务 / MCP server / 多设备编排。

---

## Stories（每个带 verify）

- **S1 — devices 模块骨架**：新建 `cli/src/agentprobe/devices/`，定义 `Device`/`Topology`
  数据类（对齐 topology.schema.json）+ `DeviceRegistry`。
  → verify: `python -m compileall cli/src/agentprobe/devices`
- **S2 — topology 加载与校验**：从声明式 topology 文件加载，按 `topology.schema.json` 校验；
  缺字段/角色非法时报错。
  → verify: 单测 `pytest cli/tests/unit/test_topology.py`（含合法 + 缺字段 + 非法 role 三类用例）
- **S3 — role 守卫（INV-2 核心）**：`assert_can(action, device, topology)`：
  state-changing action 必须 identity+topology 齐全，否则返回 `unknown`/`approval_pending`；
  对 golden 且 `golden_upgrade_allowed=false` 的升级类动作返回 `safety_refused`（错误码 106）。
  → verify: 单测 `pytest cli/tests/unit/test_role_guard.py`（覆盖 unknown / approval_pending / safety_refused / ok 四条路径）
- **S4 — 错误码对齐**：守卫返回的错误码取自 `protocol.toml`/生成常量，不硬编码字面量。
  → verify: 单测断言错误码 == 契约值（103 unknown_device_identity / 104 topology_mismatch / 105 approval_required / 106 safety_refused）
- **S5 — SoM 选型标准 + topology 声明样例**：写 `docs/handoff/E1-som-selection.md`（选型标准 + 候选）
  + `scenarios/topologies/self-hosting-v1.json`（双板 topology 声明，过 schema 校验）。
  → verify: jsonschema 校验该 topology 文件通过 `topology.schema.json`
- **S6 — 单板 transport 路径对齐**：`ap device status` 在有 topology 时走 devices 解析；
  `UsbTransport.info()` 接口签名与 `Transport` Protocol 对齐（仍可 `NotImplementedError`，但签名/导入正确）。
  → verify: `pytest cli/tests`（全绿）+ `python -m agentprobe device status --json` 输出合法
- **S7 — 单板 bring-up 交接物**：写 `docs/handoff/E1-single-board-bringup.md`：
  CLI→daemon→USB→PS→AXI→PL→event→证据 的真机上板步骤、所需接线、预期信号、验收判据（NS-B1）。

---

## ★ Goal Done（软件验收标准 = goal 完成条件）

全部满足即 E1 goal 完成：

- **AC1** `pytest cli/tests` 全绿，新增测试覆盖 S2/S3/S4 的所有分支。
  cmd: `cd cli && python -m pytest tests -q` → 期望: all passed。
- **AC2** `python -m compileall cli/src` 无错误。
- **AC3** role 守卫四条路径（unknown / approval_pending / safety_refused / ok）各有意图测试，
  且错误码取自契约常量（非硬编码）。
- **AC4** `scenarios/topologies/self-hosting-v1.json` 通过 `topology.schema.json`（jsonschema）。
- **AC5** `python -m agentprobe device status --json` 输出合法 JSON，无 topology 时返回
  `unknown`（不伪造 ok）。
- **AC6** 交接物齐：`docs/handoff/E1-som-selection.md` + `docs/handoff/E1-single-board-bringup.md` 存在且含上板步骤 + 验收判据。
- **AC7** `generate_protocol.py --check` 通过，契约版本仍一致 0.2.0（未被本 epic 破坏）。

---

## 集成测试标准（端到端怎么算通过）

- **IT1 — 身份门控端到端**：构造一个缺 identity 的 state-changing 请求路径，
  断言系统返回 `unknown` 且不执行动作；构造 golden 升级请求，断言 `safety_refused`。
  → 通过判据：两条都不产生成功 verdict，错误码正确。
- **IT2 — replay 回归未被破坏**：`ap scenario run --replay --json` 仍返回 `regression_pass`，
  Evidence Envelope 仍过 evidence.schema.json v0.2.0。
  → 通过判据：E1 的改动不回归 E0 已验证的闭环。

---

## 硬件交接物（需真机，不计入 Goal Done）

- **HW1 — 单板 bring-up**（对应 NS-B1）：代码写到可上板（transport 接口齐、固件可编译、
  RTL 可仿真），上板步骤见 `docs/handoff/E1-single-board-bringup.md`。命中 LOOP.md §3 hard-stop。
- **HW2 — RTL/固件**：若本 epic 触碰 `fpga/`/`firmware/`，需有 testbench 仿真 PASS + 交叉编译通过，
  但不要求烧录。

### 人工决策项（Codex 不做，写进 NEXT.md open BLOCKs 交还）
- **DEC1 — SoM SKU 选定**：从 `docs/handoff/E1-som-selection.md` 候选中选定具体板卡（采购决策）。

---

## 不变量检查（继承 NORTH_STAR，必须全过）

- [ ] INV-1 能力面/推理面分离：devices 是能力侧，不引入推理逻辑。
- [ ] INV-2 身份门控：本 epic 的核心交付，S3/S4/IT1 直接验证。
- [ ] INV-3 大声失败：无 topology 返回 unknown 而非伪造 ok；仿真/编译通过不谎报真机通过。
- [ ] INV-4 Golden 不可自动升级：S3 的 safety_refused 路径强制。
- [ ] INV-5 Contract-first SSOT：错误码/角色取自生成常量，AC7 守住版本一致。

---

## 给 Codex 的执行提示
- 按 LOOP.md 循环；S1→S7 顺序推进，每个 story 的 verify 通过就 commit（work/v01a）。
- 结构性查询（谁调 `make_outcome`、topology schema 字段）用 `codegraph_*`/serena，不 grep。
- 命中 HW1/HW2/DEC1 → 写 handoff 文档 + NEXT.md BLOCKs，hard-stop，**不要假装真机通过**。
- 测试要编码意图（AGENTS.md §8）：守卫测试必须"业务逻辑变了就会失败"，不是只断言返回了东西。
