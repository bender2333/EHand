# Plan: E1 — 设备身份/拓扑 + 单板地基（goal）

**Epic ID:** E1 ｜ **Scope tasks:** T-04 / T-05 / T-06 ｜ **Status:** Ready ｜ **前置:** E0 已完成

> **Scope tasks 的完整定义见 `tasks.md`（§T-04 / §T-05 / §T-06）。** 本 plan 不重复抄任务描述，
> 只负责把它们打包成一个 goal，并补充验收标准 + 架构判断（tasks.md 没有的部分）。

> 本 plan 定义**研发任务 + 验收标准 + 边界**。实现细节（模块如何拆、文件怎么命名、
> 测试如何组织、用什么命令验证）由 Codex 自行决定——它足够聪明。

---

## 服务于北极星

建立"设备身份门控"地基（INV-2 / P5）：这是后续一切物理 state-changing 动作能安全执行的前提。
并把单板硬件通路写到可上板交接程度，为最终真机 self-hosting 铺第一段路。

## Scope

- **含**：T-04 全量（纯软件，可完整做完）；T-05 / T-06 的软件部分 + 上板交接物。
- **非目标**：真机 bring-up（人工，NS-B1）；选定具体 SoM SKU（采购决策）；
  SWD/analyzer/mock 运行逻辑（E2/E5）；网络服务 / MCP server / 多设备编排。

## 研发任务（WHAT）

- **R1 设备身份与拓扑**：从声明式 topology 文件加载设备（角色/serial/版本/连接），按契约 schema 校验。
- **R2 身份门控**（本 epic 核心）：state-changing 动作必须 identity + topology 齐全才放行；
  缺失则给出 `unknown` / `approval_pending`，绝不伪造成功；对 Golden 的升级类动作按不可自动升级拒绝。
- **R3 SoM 选型与拓扑声明**：产出选型标准文档（候选 + 取舍维度）+ 一份可校验的双板 self-hosting topology 声明样例。
- **R4 单板通路对齐**：host 侧把 `device status` 接到真实 transport 解析路径；
  涉及的固件/RTL 写到可编译、可仿真程度（不烧录、不上板）。
- **R5 单板 bring-up 交接物**：写真机上板步骤文档（接线、预期信号、验收判据）。

## ★ Goal Done（验收标准 = goal 完成条件，描述意图不规定命令）

- **AC1 身份门控四条路径**都有"编码意图"的测试且通过：齐全→放行、缺身份→unknown、
  需批准→approval_pending、Golden 升级→拒绝。
- **AC2 错误码取自契约常量**（protocol.toml / 生成常量），不硬编码字面量。
- **AC3 双板 topology 声明样例**通过契约 topology schema 校验。
- **AC4 `device status` 在无拓扑时返回 `unknown`**，不伪造 ok。
- **AC5 既有 replay 闭环不回归**：仍得到 `regression_pass` 且证据过 evidence schema（E1 改动不破坏 E0）。
- **AC6 契约 0.2.0 一致性未被破坏**。
- **AC7 交接物齐**：SoM 选型文档 + 单板 bring-up 文档存在且含验收判据。

## 集成测试标准

- **IT1 身份门控端到端**：缺身份的 state-changing 路径不执行动作、不产生成功 verdict；
  Golden 升级请求被安全拒绝。
- **IT2 回归未破坏**：replay 自托管闭环仍通过（同 AC5）。

## 硬件交接物（需真机，不计入 Goal Done）

- **HW1 单板 bring-up**（NS-B1）：代码写到可上板，步骤见交接文档，命中 LOOP.md §3 hard-stop。
- **HW2 RTL/固件**：若触碰 `fpga/`/`firmware/`，需有仿真 PASS + 交叉编译通过，不烧录。

### 人工决策项（Codex 不做，写进 NEXT.md open BLOCKs 交还）

- **DEC1 SoM SKU 选定**：从选型文档候选中拍板（采购决策）。

## 不变量检查（继承 NORTH_STAR，必须全过）

- [ ] INV-1 能力/推理分离　[ ] INV-2 身份门控（本 epic 核心）　[ ] INV-3 大声失败
- [ ] INV-4 Golden 不可自动升级　[ ] INV-5 Contract-first SSOT

## 架构要点（我重点把控的——Codex 实现时务必吃透）

**① 载重决策（不可妥协）**
身份门控（R2）是整个系统的安全护城河，也是本 epic 的重心。它一旦松动，后续所有物理
state-changing 动作都不安全。INV-2 在这里不是检查项，是地基。其余任务都可以重做，这个语义不能错。

**② 必须解耦（现在不分，以后会痛）**
- **topology 声明格式 ↔ 校验逻辑**：声明格式一定会演化（加字段、加角色）。validator 不要硬编死某版字段集；
  契约 schema 是唯一权威，validator 跟着 schema 走，不要在代码里再复制一份字段清单。
- **身份门控（策略）↔ transport（机制）**：门控是"能不能做"的策略判断，transport 是"怎么传"的机制。
  门控层不该知道底下是 USB 还是 replay——否则换 transport 就得改安全逻辑。这条直接服务 INV-1。
- **错误分类 ↔ 调用方**：错误码会增长，调用方按"类别语义"反应，不要 switch 死具体数值散落各处。

**③ 易变，要留容纳空间（别写死，但也别过度设计）**
- SoM SKU 未定（DEC1）：topology 的设备/能力描述要能容纳不同板子的差异，不要把某块板的假设焊进结构。
- 角色集合（golden/dut/external_target/host）未来可能扩（多 DUT、多 Golden）：role 处理不要假设"只有一个 dut"。
- state_changing_actions 列表会随能力增长：守卫对"未知 action"要有明确默认（保守拒绝），而非漏过。

**④ 需慎重的语义边界（最容易踩坑，plan 在此点明判据）**
- **`unknown` vs `approval_pending` 的分界**：`unknown` = 信息不全、系统**无法判断**（缺 identity/topology）；
  `approval_pending` = 系统**判断清楚了**、但动作高风险**需人批准**。两者不可混用——混了会要么漏掉批准、
  要么把"不知道"伪装成"等批准"。这是 R2 里最需要想清楚的一处。
- **Golden 升级拒绝点的归属**：必须落在**守卫层**统一拒绝，不能散落到 transport 或 CLI。
  安全决策只有一个入口，才不会被某条新路径绕过（INV-4）。

> 这些是方向与约束，不是实现指令。怎么落地（模块怎么拆、用什么数据结构）由 Codex 定；
> 但上面的解耦边界和语义判据若被破坏，即使测试通过也算 epic 没做对——届时请按 LOOP.md §3 升级。

## 给 Codex

按 LOOP.md 执行。实现路径自定。命中 HW1/HW2/DEC1 → 写交接文档 + NEXT.md BLOCKs，
hard-stop，**绝不假装真机通过**。测试要编码意图（AGENTS.md §8）。
