---
stepsCompleted: [step-01-init, step-02-discovery, step-02b-vision, step-02c-executive-summary, step-01b-continue, step-03-success, step-04-journeys, step-05-domain, step-06-innovation, step-07-project-type, step-08-scoping, step-09-functional, step-10-nonfunctional, step-11-polish]
inputDocuments:
  - _bmad-output/product-brief-e-project.md
  - _bmad-output/product-brief-e-project-distillate.md
  - _bmad-output/architecture.md
  - PRD_AgentProbe.md
  - PRD_AgentProbe_Part3_continued.md
  - PRD_AgentProbe_Part4.md
workflowType: 'prd'
project_name: 'AgentProbe'
user_name: 'bender'
date: '2026-04-21'
classification:
  projectType: developer_infrastructure
  subType: agent_sensory_platform
  domain: Embedded AI DevTool
  complexity: high
  projectContext: greenfield
  primaryUser: AI Agent (Claude Code / OpenCode)
  secondaryUser: 嵌入式工程师
  coreAbstraction: "Physical World → Semantic JSON for Agent reasoning"
discoveryInsights:
  coreCapabilities: "Self-hosting loop + Mock Engine + 信号分析 + 诊断智能"
  baseCapabilities: "SWD 调试/烧录 (CMSIS-DAP)"
  skillArchitecture: "4层: Capability / Knowledge / Diagnostics / Strategy"
  cliDesign: "双模输出（人类默认 + --json Agent 模式）"
  v1Scope: "MVP: two-board self-hosting loop + SPI-first Mock/Analyzer + CMSIS-DAP, CLI+daemon+Skill"
  ecosystemStrategy: "开源 Mock 模型格式 + Skill 文件格式，社区贡献"
  acceptanceCriteria: "内部验收：Golden AgentProbe 验证 DUT AgentProbe 的开发闭环；外部 demo 可用温湿度或等价参考项目"
  hardwareUpgradePath: "V1 Zynq SoM + minimal baseboard → V2 productized baseboard under stable PS/PL/CLI contracts"
---

# Product Requirements Document - AgentProbe

**Author:** bender
**Date:** 2026-04-21

## Executive Summary

AgentProbe 是一个面向嵌入式开发 AI Agent 的基础设施平台。它不是把若干传统调试工具打包到一起，而是为 Agent 提供统一的物理感知面与执行控制面：一端把总线、时序、外设响应与异常行为转换为确定性、可消费的语义 JSON，另一端让 Agent 通过同一套 CLI 完成烧录、Mock 外设驱动、信号采集、诊断与验证控制。它补上了 AI 从“会写嵌入式代码”到“能证明代码在物理世界里真的工作”的最后一环。

当前嵌入式 AI Agent 已经能够生成大量驱动、协议栈和业务逻辑代码，但在代码进入真实系统后，仍然缺乏对物理行为的可观测性和可操作性：它不知道 SPI 时钟极性是否错误，不知道 I2C 设备为何不应答，不知道 UART 帧丢失发生在软件层、连线层还是时序层。结果是，Agent 在源码层很强，在实验台前却仍需要人类工程师充当“眼和手”。AgentProbe 的核心价值就是把这部分能力产品化、标准化、Agent-native 化，让 Agent 首次具备完整的闭环验证能力。

这使嵌入式开发从“以资深工程师经验和人工调试时间为核心约束”，转向“以 Agent 算力和自动迭代次数为核心约束”。目标工作流不是辅助式调试，而是端到端自主开发：用户描述一个复杂功能后，Agent 持续执行“实现 → 烧录 → 观测 → 诊断 → 修正 → 回归验证 → 演示准备 → 报告输出”的长时闭环，人类只在关键节点审阅证据、批准结果并接管高风险决策。

这个机会之所以现在成立，有三重原因。第一，LLM 的编码能力已跨过可独立完成相当比例嵌入式开发任务的门槛。第二，嵌入式系统复杂度持续上升，而能够跨硬件、固件、总线和调试链路定位问题的资深工程师仍然稀缺。第三，现有工具生态默认“人是操作者”，没有任何主流产品把 AI Agent 当成第一用户来设计感知、控制和诊断接口。AgentProbe 的切入点因此非常明确：它不是另一个调试器，而是 Agent 接管嵌入式闭环开发所必需的基础设施。

AgentProbe 的战略目标不是先做出一个功能完整的硬件工具箱，而是证明一种新的 **AI-native 软硬件开发方式**：Agent 使用标准化的物理感知与控制接口，持续完成“实现 → 构建 → 烧录 → 观测 → 诊断 → 修正 → 复跑 → 报告”的闭环。测试自动化、回归验证和报告生成是这种范式自然带来的结果，而不是产品成立的根本目标。V1 的内部 North Star 是 **self-hosting validation**：使用一块已知稳定的 Golden AgentProbe，帮助 Agent 开发、烧录、观测和修正另一块 DUT AgentProbe，从而证明 AgentProbe 能参与自身演进。

**目标用户：** 第一用户是 Claude Code、OpenCode 等 AI Agent，它们通过 `ap` CLI、守护进程和 Skill 文件消费能力；嵌入式工程师是监督者、受益者和最终责任人，通过相同平台查看证据、审阅诊断、必要时接管流程，并在无 Agent 模式下独立使用工具链。

**V1 MVP：** 交付一个可证明闭环价值的最小平台，包括 CMSIS-DAP v2 SWD 调试/烧录、SPI-first Mock/分析能力、UART 透传/嗅探、8 通道信号分析、`ap diagnose` 诊断命令、面向 Agent 的确定性 `--json` 输出与面向工程师的人类友好终端输出。V1 的首要验收锚点不是外部 demo 功能清单，而是 **Golden AgentProbe → DUT AgentProbe** 的 two-board self-hosting loop：Agent 能修改 DUT 固件或 PL/PS 相关实现，构建、烧录、观测、诊断、修复并输出可审计证据。温湿度采集器或等价外部参考项目用于展示和设计伙伴沟通，不应反向绑架内部 MVP 范围；若采用 I2C SHT30 demo，则 I2C Mock/decoder 可作为 Phase 1.5 补充。

### What Makes This Special

**它的差异化不在于单项能力，而在于 Agent-native 闭环。** J-Link 解决烧录，Saleae 解决观测，Bus Pirate 解决总线交互，但这些工具都假设人类自己观察、判断和操作。AgentProbe 把“烧录 + Mock + 采集 + 诊断”重构为 Agent 可直接调用的统一接口，使 AI 从“代码生成器”升级为“可验证、可迭代、可持续工作的嵌入式开发执行者”。

**它的护城河不只是硬件板卡，而是标准化的语义闭环协议。** 长期壁垒来自四部分：确定性 CLI/JSON 契约、将物理行为映射为高价值证据的语义事件模型、可复用的 Mock 模型体系，以及沉淀在 `ap diagnose` 与 Skill 文件中的嵌入式诊断知识。这些资产共同决定 Agent 是否真的能稳定完成闭环，而不仅仅是“连接上硬件”。

**它改变的是研发产能模型。** 传统嵌入式研发的速度上限由资深工程师能投入多少小时决定；AgentProbe 让团队把更多问题交给 Agent 在夜间和长时间窗口持续试错、验证和优化，用计算资源换取开发吞吐量、迭代频率和维护能力。这为嵌入式产品的持续升级、自动回归验证和长期演进打开了全新的效率边界。

## Project Classification

| 维度 | 分类 |
|------|------|
| **项目类型** | 开发者基础设施（Developer Infrastructure） |
| **子类型** | Agent 感知平台（Agent Sensory Platform） |
| **领域** | 嵌入式 AI 开发工具 |
| **复杂度** | 高（硬件、FPGA、固件、守护进程、CLI、Skill 全栈协同） |
| **项目上下文** | 全新项目（Greenfield） |
| **核心抽象** | Physical World → Semantic JSON for Agent reasoning |

### Hardware Role Definitions

V1 必须显式区分“产品硬件”和“被测硬件”，否则 self-hosting 与外部 demo 会混淆支持边界。

| 角色 | 定义 | V1 责任 |
|------|------|---------|
| AgentProbe product hardware | Zynq-7020 SoM + minimal baseboard 形态的 AgentProbe 本体 | 提供 SWD、观测、Mock、事件与证据输出能力 |
| Golden AgentProbe | 已知稳定、不可被 Agent 自动升级的 AgentProbe | 作为可信测量/烧录/观测工具，验证 DUT |
| DUT AgentProbe | 正在开发或验证中的 AgentProbe | 接受烧录、运行测试、暴露可观测信号与事件 |
| External target / DUT | STM32 M3/M4/M33 等外部被测目标板 | 用于外部 reference demo 与设计伙伴验证 |
| AI Agent | Claude Code / OpenCode 等能执行 shell 并解析 JSON 的 Agent | 调用 `ap --json` 完成闭环推进 |
| Embedded engineer | 人类监督者与责任人 | 审阅 evidence pack，批准高风险动作，接管 unsupported/unknown 情况 |

## Success Criteria

### User Success

对 AgentProbe 而言，用户成功必须同时对 **AI Agent** 与 **工程师** 成立。对 AI Agent 来说，真正的 done 不是执行了若干命令，而是：在 **V1 支持边界** 内，能把任务稳定推进到两个可验收终态之一：  
1. **regression pass + report**  
2. **explicit escalation + auditable evidence**

这意味着 V1 的成功不能只覆盖 happy path。任何可被视为“闭环成立”的场景，至少都要包含 **1 条正常路径 + 1 条异常/失败路径**，并让 Agent 对两者都能给出可审计的结论或明确升级给人类的理由。

对工程师来说，真正的 done 不是“系统说它成功了”，而是工程师可以仅基于 AgentProbe 输出的 **evidence / diagnosis / suggestion** 做出继续、回退、批准或人工接管的判断，而**不需要重新手工跑完整套 bench 排查流程**。如果一遇到异常，工程师就必须回到传统波形工具链重新抓数和重建上下文，则不算真正的用户成功。

用户成功还必须具备 **团队可交接性**。一个工程师或 Agent 配置好的 session / routing / mock 环境，应能被同团队另一位工程师或 Agent 复用和复跑，不依赖原作者口头说明。这使 AgentProbe 更像团队工作流基础设施，而不是单次演示工具。

### Business Success

AgentProbe 的商业成功不应由 vanity metrics 定义，而应由它是否开始**替代真实人工 bench 调试时间**、并进入团队的周节奏来定义。

**Proof of Product Thesis（3 个月）**：围绕 two-board self-hosting rig，Agent 必须使用 Golden AgentProbe 推进 DUT AgentProbe 的一次真实开发闭环，并在至少一个异常路径上完成**正确诊断、修正或明确升级给人类**。这一步不接受一次性彩排式通过；它必须是可重复、可复核、可作为 V1 价值锚点的演示能力。温湿度采集器或等价外部参考项目用于对外解释价值，但不替代 self-hosting proof。

**Proof of Workflow Adoption（12 个月）**：至少 **3 个设计伙伴团队**，在**真实项目**里连续 **4 周**、每周至少完成 **1 次团队自发、非陪跑式** 的真实闭环开发或回归任务。这里的“自发”明确指团队自己发起、自己执行、自己关单，而不是创始人或产品团队代操作的展示行为。

**Proof of Expansion Intent**：设计伙伴团队中，至少出现明确的扩用信号，例如把 AgentProbe 纳入第二个项目、第二类外设、或第二条回归链路。扩用不接受口头兴趣，必须体现为可观察信号，例如明确的第二场景名称、负责人和计划时间。

### Technical Success

所有技术成功声明都必须明确绑定 **V1 支持边界**：AgentProbe 产品硬件采用 Zynq-7020 SoM + minimal baseboard；被测目标支持 DUT AgentProbe 与 STM32 M3/M4/M33；工具链主路径为 `arm-none-eabi-gcc`、CLI + daemon + Skill、CMSIS-DAP v2、SPI-first Mock/分析、UART 透传/嗅探、8 通道信号分析与协议解码。I2C Mock/decoder 不作为 Phase 1 self-hosting 的硬门槛，除非外部 reference demo 明确选择 I2C 作为展示路径。任何超出边界的场景，系统都不应给出模糊承诺，而应返回明确的升级或不支持结论。

技术成功的第一原则不是“功能多”，而是 **可审计闭环**。V1 必须实现 P0 级的确定性输出：相同设备状态 + 相同命令，应得到**一致的 schema、taxonomy 和语义结论路径**。这里不要求逐字节文本完全相同，但要求 verdict class、diagnosis class 和 escalation class 可稳定判定。

`ap diagnose` 必须输出结构化字段：`diagnosis` / `evidence` / `suggestion` / `confidence`。其中 `confidence` 不能孤立存在，必须绑定到完整的证据链：**观测 → 解码 → 诊断 → 建议/修复或升级**。当证据不足、工具失败、场景不受支持或自动修复不安全时，系统必须显式升级，而不是输出“看起来合理但不可验证”的结论。

V1 还必须把 **0 silent false positive** 视作硬约束。对支持边界内的闭环任务，系统可以失败、可以升级、可以拒绝承诺，但不能在证据不足时错误地宣称已经成功完成验证。

每个被判定为成功或已升级的闭环任务，都必须产出完整证据包，至少包括：`build hash`、`firmware hash`、`flash result`、`trace summary`、`diagnose JSON`、`patch diff` 或 `escalation reason`、`regression result`、`final report`。没有证据包的闭环，不算完成。

### Measurable Outcomes

- **标准任务包闭环率**：在 V1 支持边界内，针对 10 个标准任务包，至少 8 个任务能够稳定到达可验收终态（`regression pass + report` 或 `explicit escalation + auditable evidence`）。
- **3 个月 PoP 指标**：在 two-board self-hosting rig 上完成至少 5 次独立运行，其中至少 4 次到达可验收终态；场景必须覆盖 1 条正常路径和 1 条异常路径，且至少有 1 次由非原作者操作完成。外部 reference demo 可使用温湿度采集器或等价场景，但不替代 self-hosting PoP。
- **12 个月 Adoption 指标**：3 个设计伙伴团队 × 连续 4 周 × 每周至少 1 次团队自发、真实任务、非陪跑式闭环使用。
- **可审计性指标**：在 V1 支持范围内，工程师应能仅凭 AgentProbe 输出的证据包完成继续/回退/人工接管判断，而无需回退到原始 bench 工具链重新抓数。
- **可复现/可交接指标**：同一 `session + routing + mock` 配置可由另一位工程师或 Agent 重放，并得到同类 evidence 结构与同类 verdict / diagnosis / escalation class。
- **扩用信号指标**：至少有一个设计伙伴团队给出第二场景名称、负责人和计划时间，作为扩用意图的硬信号。

## Product Scope

### MVP - Minimum Viable Product

V1 MVP 的目标不是做出功能拼盘，而是证明 **最小可信闭环**。因此 MVP 必须聚焦于：

- Two-board self-hosting validation rig：Golden AgentProbe 验证 DUT AgentProbe
- CMSIS-DAP v2 SWD 调试/烧录，用于烧录与控制 DUT
- SPI Slave ×1 Mock + SPI 协议解码，作为 Phase 1 首个硬实时 Mock/观测闭环
- UART 透传/嗅探，用于 DUT 日志、RTT/semihosting 替代路径和 evidence 关联
- 8 通道信号分析 + SPI 协议解码
- `ap` CLI + 本地 daemon + Skill 文件
- 全局 `--json` Agent 模式
- `ap diagnose`
- replay transport 与 canonical replay fixture，用于无硬件状态下验证 Agent workflow 与 schema 稳定性
- “DUT AgentProbe 自举开发闭环”作为内部验收锚点
- “温湿度采集器”或等价外部参考项目作为对外展示锚点；若继续使用 I2C SHT30，则 I2C Mock/decoder 进入 Phase 1.5
- 一个受控 failure catalog（至少覆盖正常路径与异常路径）
- 一个标准化证据包与报告格式
- 支持 STM32 M3/M4/M33 + `arm-none-eabi-gcc`

**V1 明确非目标：**

- RTOS 与更复杂的软件栈承诺
- 多板协同与广义 brownfield 零配置接入
- 模拟/电源完整性问题覆盖
- capture/replay 平台化能力
- I2C/SHT30 外部 demo 不能作为 Phase 1 self-hosting 完成的硬前置条件
- HTML 视图、富 UI、桌面工作台
- 开放生态、通用 Skill/模型平台化
- 更广的 IDE / MCP / 平台集成
- 无人审批自动提交主干或“万能自治代理”承诺

### Growth Features (Post-MVP)

Post-MVP 阶段应围绕“在不破坏可信闭环前提下扩大覆盖”展开，包括：

- 更多协议、更多模型、更多目标芯片支持
- 更强的 capture / replay / minimal HTML view
- 更丰富的诊断知识、故障目录与自动回归能力
- 开放 Mock 模型格式 / Skill 生态
- 更广的工具链接入与组织级工作流集成

### Vision (Future)

长期来看，AgentProbe 的目标不是成为另一块更复杂的调试板，而是成为 **physical verification and control layer for agents**：

- 支撑长时间无人值守的嵌入式开发闭环
- 支撑持续升级、自动优化、自动回归与团队级工作流
- 让嵌入式开发从“人力受限”转向“算力与闭环能力受限”

AgentProbe 的长期演进必须遵循一个木桶原则：**Agent 闭环能力 = min(推理能力, 可观测范围, 可执行范围, 语义转换质量)**。V1 的核心贡献是优先补齐 Agent 在物理世界中的 **可观测范围** 与 **可执行范围** 瓶颈，并通过稳定的语义转换 contract 把这些物理事实压缩成 Agent 可消费的证据。只有当观测和执行不再是主要瓶颈时，项目才应把重点转向自建 Agent 推理层或更复杂的自治策略。

## User Journeys

With the strategic scope defined, the following journeys show how that bounded closed-loop value is experienced across execution, trust, and scale.

AgentProbe 的 journey 不是一组平铺的人物故事，而是一个递进体系：

- **Execution Journeys**：证明闭环成立
- **Trust Journeys**：证明人类敢基于它做判断
- **Scale Journeys**：证明它能进入组织流程

### Execution Journey 1 — Atlas：AI Agent 的主成功路径

**Opening Scene**：Atlas 是团队日常使用的 Claude Code / OpenCode Agent 实例。它已经会写驱动和业务逻辑，但一到硬件验证就会失明——它不知道 DUT 是否真的响应，也不知道自己的判断有没有物理依据。

**Rising Action**：工程师把 DUT AgentProbe 的一个受控开发任务交给它。Atlas 读取 Skill 文件，加载 self-hosting topology，通过 `ap` CLI 完成构建、烧录、运行，并由 Golden AgentProbe 观察 DUT 的 UART 输出、SPI 事务、GPIO/逻辑信号与诊断事件。

**Climax**：关键时刻不是“代码编过了”，而是它第一次拿到**足够支撑 verdict 的物理证据**：总线事务、诊断结论、回归结果和报告链路彼此一致。

**Resolution**：Atlas 把任务推进到 `regression pass + report` 终态，工程师只需审阅 evidence 包并批准。

**Critical Information Need**：可机读的 `verdict / diagnosis / confidence / next action`，以及支持边界内的明确结论。

**Failure / Recovery Hook**：如果证据不足或场景超出支持边界，系统必须把 Atlas 推向 `explicit escalation + auditable evidence`，而不是让它继续猜。

### Execution Journey 2 — Atlas：AI Agent 的异常恢复路径

**Opening Scene**：同样是 self-hosting rig，但这次 DUT 没有产生预期事件，闭环进入异常分支。过去这会把 Agent 直接打回人类，因为它无法区分是固件逻辑错了、SPI/UART 时序错了、路由错了还是工具本身出了问题。

**Rising Action**：Atlas 观察到 NACK、超时、诊断置信度变化和建议动作，尝试在支持边界内做一次安全修正；若证据不足，则准备显式升级。

**Climax**：AgentProbe 的价值在这里真正成立：系统要么帮助 Atlas 给出**可审计 diagnosis + fix**，要么帮助它给出**显式升级 + 完整证据链**。不允许沉默失败，也不允许“看起来像成功”。

**Resolution**：异常场景不再意味着闭环断裂。即使 Atlas 无法自动修复，它也能把问题以工程师可接管的方式交出来。

**Critical Information Need**：`diagnosis class / escalation class / possible cause / next safe action`。

**Failure / Recovery Hook**：若修正不安全或不在支持范围内，系统必须停在升级终态，并附带足够证据让人类接力。

### Trust Journey 3 — 张工：嵌入式工程师的审阅与接力路径

**Opening Scene**：张工是 5 年经验的嵌入式工程师。过去他每天在 J-Link、逻辑分析仪、串口工具之间来回切换。Agent 时代到来后，他最在意的不是“Agent 会不会写代码”，而是“我凭什么信它的结论”。

**Rising Action**：他接手一条由 Agent 完成的闭环任务，不是重新搭一遍台架，而是直接查看证据包：build/flash 结果、trace 摘要、diagnose JSON、patch diff、regression 结果、final report。

**Climax**：真正的转折点，是张工第一次**不重抓波形，也敢批准结果**。AgentProbe 把他从“手工操作员”变成“审阅者和决策者”。

**Resolution**：他把 session / routing / mock 配置提交到仓库，团队其他人可以复用这套环境。AgentProbe 开始进入团队流程，而不是停留在个人技巧层面。

**Critical Information Need**：可审计 evidence 包，以及“为什么这个 verdict 值得相信”的解释。

**Failure / Recovery Hook**：如果证据不完整、结论不稳定或 taxonomy 不清晰，张工必须能选择回退、人工接管或要求重新执行，而不是被迫相信系统。

### Scale Journey 4 — 陈工：平台 / 实验台管理员的自助化路径

**Opening Scene**：陈工负责团队共享实验台。没有他，所有设计伙伴都得靠产品团队手把手配线、配路由、配 mock，产品永远走不出“陪跑 demo”。

**Rising Action**：他为不同参考板卡准备 session 模板、routing 规则、failure catalog、支持矩阵和设备健康检查，把 AgentProbe 从“单次演示工具”整理成“可交接的共享基础设施”。

**Climax**：当团队第一次**不依赖创始人、只靠模板和文档**就跑起闭环时，AgentProbe 才真正开始具备组织级采用可能性。

**Resolution**：平台管理员把已验证的 session / routing / failure catalog 固化成团队标准资产，保证后续团队成员和 Agent 可以稳定复用。

**Critical Information Need**：设备健康、模板状态、支持矩阵、已验证环境列表。

**Failure / Recovery Hook**：如果某套模板失效或设备状态异常，系统必须能够快速暴露问题来源，并支持管理员回滚到已验证配置。

### Trust Journey 5 — 刘工：支持 / 故障排查工程师的调查路径

**Opening Scene**：某个设计伙伴团队报告“闭环失败了”。刘工要搞清楚：这是用户代码问题、session 配置问题、工具问题，还是超出 V1 支持边界。

**Rising Action**：他不从零重建实验，而是直接拉取运行留下的证据包和 `verdict / diagnosis / escalation class`，并和历史案例、同一配置的重放结果做对比。

**Climax**：他能快速把问题分诊为：`supported failure / unsupported case / tool failure / insufficient evidence`，而不是陷入漫长的台架重现过程。

**Resolution**：支持工作从“凭经验救火”变成“基于结构化证据定位和交接”，也让产品团队知道该修什么、不该承诺什么。

**Critical Information Need**：triage 分类、历史对比、升级原因、支持边界可见性。

**Failure / Recovery Hook**：如果证据链断裂或 run identity 不完整，支持流程会迅速退化为手工排查，因此系统必须兜底 artifact retention 与错误分类。

### Scale Journey 6 — 李工：集成开发者的工作流接入路径

**Opening Scene**：李工负责把团队工具链接进现有研发流程。他不关心演示是不是酷，而关心：`ap` CLI 能否稳定接进脚本、Agent、夜间回归和团队规则。

**Rising Action**：他基于 `ap --json`、标准证据包和清晰的终态语义，把 AgentProbe 接入团队自动化流程：通过的任务归档，升级的任务建单，失败的任务阻断某条回归链路。

**Climax**：真正的价值时刻，不是第一次 shell 调通，而是 **AgentProbe 的终态语义第一次变成团队规则**，开始稳定出现在周节奏里。

**Resolution**：一旦集成开发者愿意持续维护这条链路，AgentProbe 就不再是实验性质工具，而开始成为团队开发基础设施。

**Critical Information Need**：稳定 JSON schema/taxonomy、终态语义、artifact export、非交互执行行为。

**Failure / Recovery Hook**：如果 exit behavior、schema 或 artifact contract 不稳定，整个接入链路就会失效，团队也不会把它纳入常规流程。

### Journey-Derived Capability Summary

**Capabilities they use**

- implement / flash / observe / diagnose / fix / regress / report
- 标准证据包与 human-auditable review
- session portability、routing/mock 模板、同配置复跑
- 设备健康检查、支持矩阵、共享环境管理
- artifact retention、triage taxonomy、历史对比
- 稳定 CLI/JSON、非交互执行、workflow 接入

**Capabilities the system must guarantee**

- deterministic schema / taxonomy / terminal state semantics
- typed escalation 与 support boundary clarity
- 0 silent false positive
- evidence chain 完整可追溯
- handoff / reproducibility / artifact retention
- V1 scope discipline：Execution、Trust、Scale 都成立，但不超范围承诺

The later Functional Requirements section formalizes these journey-derived needs as the product's binding capability contract.

## Domain-Specific Requirements

### Compliance & Regulatory

- **硬件上市合规**：如果 AgentProbe 以 USB 连接硬件产品形式销售，V1 就必须把 **CE / RoHS / WEEE** 视为现实约束，而不是后期补课项。美国路径上，**FCC / EMC** 应视为高概率适用项，需后续实验室与法规顾问确认。
- **市场化认证边界**：如果产品希望对外宣称 USB certified / 使用相关 logo，则需要规划 **USB-IF compliance**；否则 marketing claim 必须严格受控。
- **隐私与数据处理边界**：只要产品开始上传代码、trace、日志、账号、telemetry 到云端，就会触发更实质性的 **GDPR / CCPA** 义务。V1 最安全策略仍是 **local-first / low-telemetry / privacy-by-default**。
- **AI 责任边界**：对当前本地优先、开发辅助型产品，**AI Act** 不是 V1 的首要阻塞项；但一旦未来自建云端 agent 或更深托管 AI 能力，责任会明显抬升。
- **企业采购与安全工程**：对企业客户而言，**NIST SSDF、SBOM、漏洞响应、供应商/模型治理** 很可能比“AI 功能多强”更早成为门槛。
- **物理执行安全护栏**：AgentProbe 不只是“看”硬件，还会烧录、复位、驱动引脚、改变目标板状态。因此需要把 **目标板保护、电平/电流/路由安全、危险动作边界与确认机制** 明确视为 domain-level requirement，而不是普通实现细节。

### Technical Constraints

- **支持边界必须清晰**：V1 产品硬件路径是 Zynq-7020 SoM + minimal baseboard；被测目标路径是 DUT AgentProbe 与 STM32 M3/M4/M33；软件主路径是 `arm-none-eabi-gcc`、CLI + daemon + Skill、CMSIS-DAP v2、SPI-first Mock/分析、UART 透传/嗅探、8ch 分析与协议解码。I2C/SHT30 是可选外部 demo 路径，不是 Phase 1 self-hosting gate。
- **双数据流约束**：这个产品的核心不是一般软件工具，而是同时处理 **控制流** 与 **观测流**；二者在 USB、PS 固件、daemon、CLI 层都必须分离，不能被统一成模糊接口。
- **时序真实性约束**：Mock 价值不在“能响应”，而在“足够像真实器件以支撑驱动开发”。因此关键时序、异常行为、clock stretching / busy / timeout 等必须进入受控 failure catalog。
- **证据完整性是一等约束**：这个域里不只是“有日志”，而是需要 **Evidence Integrity**——证据必须完整、可关联、可追溯，足以支撑 verdict。否则产品的核心承诺就不成立。
- **支持环境识别**：系统必须清楚区分 **supported / unsupported / unknown** 环境。在 unknown 状态下优先升级，而不是继续输出看似可信的 verdict。
- **本地优先的架构好处**：local-first + USB-only 既能降低合规复杂度，也更符合嵌入式实验台环境；这不是只是实现选择，而是 domain fit。

### Integration Requirements

- **工具链集成**：V1 必须以 `ap` CLI 为主入口，能够稳定接入 Claude Code / OpenCode 的 Skill 文件与 shell workflow，而不是优先建设 GUI 或广义平台化接口。
- **调试生态兼容**：调试链建议对齐 **CMSIS-DAP v2 / OpenOCD 兼容心智**，降低嵌入式团队迁移成本。
- **证据与工件管理**：每次闭环任务必须产出标准证据包，能被工程师、支持、集成流程共同消费，而不只是给单一角色看。
- **Session / Routing / Failure Catalog 资产化**：这个域里，“模板和受控环境”本身就是产品能力的一部分，必须支持在团队内复用、交接和重放。
- **Configuration as Controlled Engineering Artifact**：session、routing、failure catalog、support matrix 不能散落在个人经验和 wiki 里；它们必须像代码一样可版本化、可比较、可回滚、可交接。
- **终态语义接入团队流程**：`regression pass + report`、`explicit escalation + auditable evidence` 这类终态，不只是 Agent 内部概念，而应能进入团队自动化规则与支持流程。
- **Self-hosting rig 接入**：V1 必须支持在配置资产中声明 device role（golden / dut / external-target）、serial、firmware/bitstream version 和连接拓扑，避免 Agent 在两块相同硬件之间误刷、误测或误判。

### Risk Mitigations

- **避免过度承诺自治**：V1 要证明的是 **可审计闭环**，不是“万能自治代理”。超出支持边界时必须显式升级。
- **防止 demo 成功掩盖真实采用失败**：必须把“团队自发、非陪跑式、真实任务”写进 success criteria，否则很容易出现 demo 漂亮但 adoption 弱的假阳性。
- **防止 silent false positive**：这个域里最危险的不是失败，而是**错误地宣称通过**。因此 0 silent false positive 应被视作硬约束。
- **防止 unsupported environment masquerading as supported**：用户或 Agent 在看起来相似、但其实超出支持矩阵的环境里使用系统，会制造极高的错误信心风险。系统必须明确标识 supported / unsupported / unknown。
- **防止模板/环境不可复用**：如果 session、routing、mock 配置不能交接和重放，产品就只能停留在创始人陪跑阶段。
- **防止云端隐私与开源分发风险后置**：如果未来接入云端分析或打包开源协议栈，却没有提前准备 license review、SBOM 和隐私边界，后面会卡在企业采购与法务审查。

## Innovation & Novel Patterns

### Detected Innovation Areas

AgentProbe 的创新主定位可以统一表述为：**Agent 的 physical verification and control layer**。它的根本创新不在于“让调试更自动”，而在于**第一次把物理验证从只能由人完成的活动，转化成 Agent 可以执行、消费并据此收敛的活动**。

这意味着它不是单纯把 flash、observe、diagnose 串成一个更顺手的工具链，而是在改写嵌入式开发中的默认交互单元：

- 物理世界行为被转写为 Agent 可消费的语义证据对象
- 验证结果不再只是日志和波形，而是系统可操作的终态：**verdict / diagnosis / escalation**
- 工程师从默认操作者转变为默认审阅者与异常处理者

换句话说，AgentProbe 真正的新范式不是 “AI + hardware”，而是 **让物理验证成为 agent-executable 的系统能力**。如果用户最终只是把它理解成一个更顺手的硬件工具箱，这条创新叙事就不成立。

从底层原理上看，最深的变化不是“自动化更多一点”，而是**物理验证第一次成为 Agent 可以直接完成的工作**。一旦这一点成立，嵌入式迭代的主要瓶颈就会从“人如何观察和解释硬件行为”，转移到“系统如何设计支持边界、证据契约与升级路径”。这也是它从功能增强跨越到操作模型变化的根本原因。

### Market Context & Competitive Landscape

今天市场上已经存在很多局部能力：调试器、仪器控制、自动化测试框架、CI 编排工具、远程实验室管理平台、AI 编码助手。但这些系统大多仍然默认：

- 人负责观察和解释物理行为
- 人负责判断验证是否成立
- Agent 最多只负责生成候选代码或辅助脚本

AgentProbe 的不同点，不是简单“集成更多工具”，而是提供一种新的 contract layer：**可被 Agent 消费、可被团队复用、可被支持流程分诊的 evidence + escalation contract**。这让它与普通工具聚合、workflow automation、或者“带 AI 的实验室软件”拉开了层级差异。

在表述层级上，这个创新可以分为四层：

- **本质层**：交互单元被重写，物理世界被转成语义证据
- **产品层**：Agent 的 physical verification and control layer
- **架构层**：cross-layer control plane for embedded execution and observation
- **战略层**：agent-native embedded development infrastructure 的第一层

为了保持叙事一致性，本 PRD 统一采用产品层表述作为主定位，其他表述只作为解释与延展。

从短期看，它可以被证明为一个窄而有力的 wedge：面向有限硬件场景的 physical verification layer。从长期看，如果这种接口被团队和流程围绕起来使用，它可能成长为 agent-native embedded development infrastructure 的第一层。

### Validation Approach

这条创新 thesis 必须被分阶段验证，而不是一次性宣称成立。

**近期可证明的条件：**

- 在一个真实、窄范围、强约束的嵌入式任务里，Agent 能完成端到端闭环
- 系统能产出可读、可审阅、可复用的语义证据，而不是仅产出原始日志
- 系统能明确给出终态：成功、诊断结论、或需要升级给人的异常
- 工程师在流程中的默认位置是审阅与接管，而不是全程手操作者

**长期战略意义的验证信号：**

- 团队开始围绕 evidence objects 和 escalation contract 组织协作
- 新项目能复用 session assets、支持边界和验证模式，而不是每次重建 demo
- 外部开始把 AgentProbe 理解为 Agent 的物理验证接口，而不是硬件工具集合

对不同受众，这个创新可以保持同一个核心：

- 工程师看到的是新的 evidence interface
- 管理者看到的是新的 delegation model
- 市场看到的是新的基础设施层

这意味着这条创新叙事不仅能在 PRD 内部成立，也能在工程、管理、市场三种语境下保持一致。它的母句可以被压缩为：**AgentProbe makes physical verification agent-executable.**

### Risk Mitigation

这条创新叙事最容易失败的方式包括：

- 产品被降级理解为“更聪明的硬件工具箱”
- 闭环只在创始人陪跑或理想 demo 条件下成立
- 证据对象、升级机制和 session assets 不足以形成真正可复用的 contract
- 愿景叙事远大于当前可证明范围，导致信任透支

因此，Step 6 的风险控制应明确坚持：

- **先证明窄场景、强证据、明确终态的真实闭环，再扩张叙事**
- moat 不押在单一设备支持能力上，而押在 evidence contract / escalation contract / reusable session assets 上
- 创新必须写成 staged thesis：**短期是可证明的 physical verification layer，长期才是潜在的 agent-native infrastructure layer**
- 始终明确 supported / unsupported / unknown 边界，避免“看起来闭环、实际上靠人补洞”

**外部一句话表达：**
**AgentProbe 让 Agent 第一次能自己验证嵌入式代码在物理世界里是否真的工作。**

## Developer Infrastructure Specific Requirements

### Project-Type Overview

AgentProbe 在产品类型上应被实现为一个 **面向 Agent 与嵌入式工程师协作的 developer infrastructure product**：它的正式交付形态不是 GUI 平台，也不是语言 SDK，而是 **Python CLI + 本地 daemon + Skill** 的组合。V1 的主要目标不是覆盖所有开发入口，而是先把“人工 shell + 烧录 / 串口 / 逻辑分析 + 人工判断与记录”的工作流，收敛成一个可复用、可审阅、可版本化的本地闭环。

这意味着它的 project-type 核心要求不是“功能越多越好”，而是：

- 安装与升级路径足够简单，开发者能快速接入
- 自动化接口足够稳定，Agent 能长期依赖
- 配置与证据资产足够工程化，团队能复用而不是一次性 demo
- 项目边界足够清晰，不因为过早暴露 SDK / IDE / daemon API 而失控

### Technical Architecture Considerations

- **正式交付面**：V1 以 Python CLI 包形式分发，通过 `pip` 安装，并依赖本地 daemon 管理 USB 通信与设备会话。
- **正式自动化接口**：唯一承诺的编程 / 自动化表面是 `ap <command> --json` 这类 CLI + JSON contract，而不是 Python SDK、socket API、MCP、REST 或 IDE 插件。
- **配置资产模型**：session、routing、failure catalog、support matrix 等必须以**项目内声明式文件**存在，可版本化、可代码评审、可对比、可回滚、可在团队内重用。
- **输出双轨制**：默认输出服务于人类阅读，`--json` 服务于 Agent 与自动化；两者必须语义对齐，尤其是 terminal states、evidence schema、escalation taxonomy。
- **本地优先运行模型**：developer infrastructure 的可信度来自 local-first、USB-attached、可审计执行，而不是远程托管的“黑箱自动化”。
- **集成边界纪律**：V1 不对外承诺正式 SDK，不开放稳定 daemon API，不做 IDE 集成；避免让支持面在产品尚未稳定前扩散。

### Language Matrix

- **控制平面实现语言**：Python（CLI + daemon），优先优化安装门槛、生态兼容性与 shell/Skill 集成体验。
- **消费接口语言策略**：V1 不提供多语言 SDK；任何语言环境都通过 shell 调用 CLI，并消费稳定 JSON 输出。
- **目标开发环境支持**：V1 仅支持 `arm-none-eabi-gcc` 工具链相关工作流，Keil MDK、IAR、STM32CubeIDE 等不作为 first-class integration target。
- **Agent 兼容面**：Claude Code / OpenCode 等能执行 shell 和解析 JSON 的 Agent，是 V1 的一等用户，而不是附带兼容对象。
- **人类工程师兼容面**：嵌入式工程师可以直接用 CLI 复跑、审阅证据、接管异常，但不要求先学习新 DSL 或绑定特定 IDE。

### Installation Methods

- **主安装路径**：`pip install` 安装 AgentProbe CLI，建立最短 onboarding 路径。
- **环境准备要求**：安装文档必须同时覆盖 Python 运行环境、本地 daemon 启动方式、USB 连接条件、CMSIS-DAP / 板卡前置检查。
- **项目级初始化**：应支持为项目生成或校验基础声明式配置文件，而不是把首次接入完全建立在手工命令记忆上。
- **升级策略**：CLI / daemon / schema 版本必须可见且可对齐，避免升级后出现“命令可跑但 contract 已漂移”的隐性问题。
- **离线/实验台适配**：安装和运行路径应适配本地实验环境，不依赖云端服务才能完成基本闭环。

### API Surface

- **正式 API 定义**：CLI 命令集合 + 全局 `--json` 输出 + versioned evidence / escalation schema，共同构成 V1 的官方 contract。
- **命令语义要求**：命令应围绕连接、烧录、执行、观测、诊断、报告等核心动作组织，并保持幂等性、可脚本化与错误语义清晰。
- **终态优先**：返回值不能只是一堆原始日志；必须能稳定表达 success / diagnosis / escalation / unsupported / unknown 等终态。
- **配置输入面**：项目声明式文件是 API surface 的一部分，因为它决定了 session、routing、failure modeling 与 support boundary 的行为。
- **明确非目标**：不承诺 Python import API、不承诺嵌入 IDE 的对象模型、不承诺开放 daemon 协议作为集成基线。

### Code Examples & Quickstart

- **首要文档资产**：优先建设 Quickstart + 端到端闭环示例，而不是先写厚重的参考手册。
- **内部旗舰示例**：以 Golden AgentProbe 验证 DUT AgentProbe 的 self-hosting loop 作为实现团队的第一验收示例，展示 Agent 如何修改、构建、烧录、观测、诊断、修复并输出 evidence pack。
- **外部旗舰示例**：以“温湿度采集器”或同等级别的真实案例作为设计伙伴 quickstart，展示从连接、执行、观测到 verdict/report 的完整闭环；若示例依赖 I2C，则不应阻塞 Phase 1 SPI-first self-hosting。
- **最小 Agent 集成示例**：提供 Skill + shell workflow + `--json` 输出的最小可运行例子，让 Agent 用户最快看到“如何接入”。
- **异常路径示例**：至少提供一个 failure / escalation 示例，避免文档只覆盖 happy path。
- **复跑示例**：示例应展示如何把 session、routing、evidence artifact 保留下来并在团队内复跑。

### Migration Guide

- **主要迁移来源**：人工 shell + 烧录 / 串口 / 逻辑分析 + 人工观察与记录。
- **迁移策略**：不是要求团队抛弃原有工具认知，而是把原来分散的动作与判断，逐步收敛到统一的 CLI contract、证据对象和终态输出上。
- **认知迁移重点**：工程师的角色从“每一步都亲手操作”转向“审阅结果、接管异常、调整配置资产”。
- **风险控制**：迁移文档必须明确 supported / unsupported / unknown 边界，以及何时应该回退到人工流程，避免过度信任自动化。
- **采用路径**：先从单一项目、单一板卡、单一闭环案例切入，再逐步扩展到更多团队模板与复用资产。

### Implementation Considerations

- **Contract stability first**：作为 developer infrastructure，V1 最重要的不是命令数量，而是 contract 稳定性、错误语义一致性和文档可依赖性。
- **Config as product surface**：项目内声明式配置不是附属品，而是产品表面的一部分，必须有 schema、校验、版本化与示例。
- **Evidence as reusable artifact**：证据对象必须天然适合审阅、支持分诊和团队复用，而不是只服务于单次执行。
- **Non-goals for V1**：不做正式 SDK、不做 IDE 插件、不开放 daemon API、不把 GUI 作为主入口。
- **Adoption discipline**：所有 developer-tool 设计都应服务于“更快进入闭环、更多次稳定复跑、更多团队可复用”，而不是表面上的平台感。

These project-type requirements define the shape of the product; the following section turns that shape into a phased validation and sequencing plan.

## Phased Development & Scope Validation Plan

### MVP Strategy & Philosophy

**MVP Approach:** Problem-solving MVP with a narrow, proof-oriented wedge. AgentProbe 的 V1 不是先证明“平台有多完整”，也不是打造一个 experience-first demo，而是先证明：**Agent 能通过标准化物理感知/控制接口完成可审阅、可复跑的软硬件开发闭环。** 这个 MVP 的核心不是 feature breadth，而是可信的 end-to-end proof。Phase 1 的内部 North Star 是 two-board self-hosting：Golden AgentProbe 帮助 Agent 开发和验证 DUT AgentProbe。

**Scoping Principle:** **If a capability does not directly help prove one credible, reviewable, repeatable loop in Phase 1, it should default to later phases.** 因此 V1 优化的是 **bounded, reviewable autonomy**，而不是 maximal autonomy。

**Resource Requirements:** 以 **1-2 人极限精干团队 + Agent 补执行面** 为前提设计范围。现实上这意味着 V1 必须严格压缩支持矩阵、参考场景和交付表面，只保留最能证明闭环价值的部分；任何需要额外专职集成、平台运营、IDE 生态或广泛设备适配的能力，都不应进入 MVP。

### MVP Feature Set (Phase 1)

**Phase 1 Objective:** **Prove one credible self-hosting loop - once, credibly, and repeatably.**

**Core User Journeys Supported:**
- AI Agent 主成功路径：从实现到烧录、观测、诊断、回归、报告的完整闭环
- AI Agent self-hosting 路径：使用 Golden AgentProbe 开发、烧录、观测和修正 DUT AgentProbe
- AI Agent 异常恢复路径：至少一个真实 failure path，能给出 diagnosis 或 explicit escalation
- 嵌入式工程师审阅/接力路径：工程师基于 evidence pack 做批准、回退或接管
- 最小复跑能力：同一项目配置可被**非原作者**复跑至少一次，不依赖创始人现场陪跑

**Must-Have Capabilities:**
- Python CLI + 本地 daemon + Skill 作为唯一正式交付面
- `pip install` 为主安装路径
- 全局 `--json` contract，与人类可读输出保持语义一致
- 项目内声明式配置（session / routing / failure catalog / support boundary）
- device role / serial / firmware version / connection topology 的显式声明，防止 self-hosting rig 中误操作 Golden 或 DUT
- CMSIS-DAP v2 SWD 调试/烧录主路径
- 支撑 AgentProbe DUT self-hosting 所需的最小 Mock / 观测 / 解码能力
- SPI-first Mock/分析路径；I2C 外部 demo 进入 Phase 1.5，而不是 Phase 1 完成门槛
- 标准化 evidence pack、final report、typed terminal states
- `success / diagnosis / escalation / unsupported / unknown` 等明确终态
- 至少 1 条正常路径 + 1 条异常路径的可复跑验证
- 明确人工审阅与接管机制，避免过度自治承诺

**Phase 1 Contract Requirement:** Phase 1 的成功不以“某次 happy path 跑通”定义，而以是否证明了 **evidence / escalation / review / repeatable configuration / device-role safety** 这五个核心 contract 定义。没有可审阅证据、没有显式升级语义、没有人工审阅闸门、没有最小复跑能力、或不能可靠区分 Golden/DUT/external target，都不算 Phase 1 完成。

**Explicit MVP Boundaries:**
- 不做正式 SDK
- 不做 IDE / 编辑器集成
- 不开放 daemon API 作为外部集成基线
- 不追求多板卡、多工具链、多协议大面积覆盖
- 不追求“无人审批自治代理”叙事
- 不允许 Agent 自动升级或替换 Golden AgentProbe 的稳定 firmware/bitstream
- 不把共享实验台管理、复杂平台能力、广泛组织集成作为 Phase 1 前提
- 不为未来平台化预埋与证明闭环无关的额外架构重量
- **Founder-assisted success does not count as MVP completion**

### Post-MVP Features

**Phase 2 (Post-MVP): Prove loop transferability**
- 扩到第二个真实场景 / 第二类外设 / 第二条闭环链路
- 验证 evidence / escalation / configuration contract 不只适用于单一手工参考案例
- 增加可复用模板与更强的 session / routing 资产沉淀
- 扩展 failure catalog、诊断覆盖与自动回归能力
- 让“单场景 proof”升级为“可迁移的团队工作流能力”

**Phase 3 (Expansion): Prove infrastructure gravity**
- 更广的板卡、协议、工具链与团队流程覆盖
- 更强的平台化能力，如共享实验台资产管理、capture/replay、更多组织级集成
- 更深的 agent-native embedded infrastructure 能力，把 evidence / escalation contract 变成团队默认接口
- 更开放的生态策略，如 mock 模型格式、Skill 生态与更广的自动化接入

**Phase Switch Criterion: Observation-to-Reasoning Bottleneck**
- 在 Phase 1/2 中，每个 `explicit_escalation` 或失败 run 都必须标注主要瓶颈类别：`observation_gap`、`execution_gap`、`semantic_translation_gap`、`agent_reasoning_gap`、`support_boundary_gap`。
- 当至少 20 个可复跑闭环 run 中，超过 40% 的失败被审阅确认主要来自 `agent_reasoning_gap`，且同批次中 `observation_gap + execution_gap` 低于 25%，说明木桶短板已从 AgentProbe 的物理感知/执行层转移到 Agent 推理层。
- 只有达到上述条件后，才启动 V3 Agent 重构、自建 Agent 记忆/规划层或更复杂自治策略；否则继续优先扩展观测、执行和语义转换质量。

### Risk Mitigation Strategy

**Technical Risks:**
- 最大技术风险不是单点功能缺失，而是**在证据不足时看起来像自治成立**
- 缓解方式是：单一 self-hosting rig、单一受控支持边界、强 terminal states、强 evidence contract、强人工审阅闸门
- 所有 MVP 技术决策都应服务于“闭环可信度”，而不是“自治表面效果”

**Market Risks:**
- 最大市场风险是被理解为一次性 demo 或更聪明的硬件工具箱
- MVP 必须通过“可复跑、可交接、可扩到第二场景”的信号，证明它不是演示项目
- 早期学习目标不是广泛市场覆盖，而是验证设计伙伴是否愿意把它纳入真实周节奏

**Demo Risk:**
- 惊艳体验不能替代产品成立；所有成功都必须经得起复跑、审阅、交接和第二场景迁移

**Resource Risks:**
- 1-2 人团队最大的风险是被多表面交付拖散：硬件、CLI、诊断、文档、集成都想同时做
- 缓解方式是严格放弃 SDK、IDE、平台化和广泛兼容面，优先保住一个强闭环
- Agent 应被用来放大实现、测试、文档和复跑效率，但不能被用来掩盖支持边界不清的问题

The journey-derived needs, domain constraints, project-type expectations, and phased scope above are formalized below as the product's binding capability contract.

## Functional Requirements

This section defines the full capability contract for the product; phased delivery is governed by the scoping section, not by FR order.

### Closed-Loop Task Execution

Defines how supported tasks are initiated, advanced, paused, resumed, and completed.

- FR1: AI Agent can initiate a supported embedded development and validation task against a target project.
- FR2: AI Agent can define the intended validation objective for a task and receive the outcome against that objective.
- FR3: AI Agent can execute a managed task flow that covers implementation validation from build through final outcome for a supported scenario.
- FR4: AI Agent can run both nominal-path and failure-path validation scenarios for a supported workflow.
- FR5: AI Agent can attempt a supported correction and re-validation cycle within the same task when evidence supports it.
- FR6: AI Agent can run unattended supported tasks until they reach an explicit terminal outcome or a required human approval point.
- FR7: Embedded engineer can execute the same supported task flow directly without an AI agent.
- FR8: AI Agent can re-run a previously defined task using preserved project context.
- FR8a: The system must include run sequence number, same-failure-class streak count, and elapsed time since first run in every task outcome output, enabling Agent or Skill to make informed loop-control decisions.
- FR8b: The system must not refuse or block a supported task invocation based on iteration count or elapsed time; loop-control decisions belong to the Agent or Skill layer, not the tool layer.

### Observation, Evidence & Reporting

Defines how physical behavior becomes reviewable and machine-consumable task evidence.

- FR9: AI Agent can access machine-readable evidence produced during a task run.
- FR10: Embedded engineer can review a complete evidence package for any completed or escalated run.
- FR11: Embedded engineer can trace each reported conclusion back to the supporting evidence generated during the run.
- FR12: Support engineer can inspect the full artifact set, run identity, and final outcome for a historical run.
- FR13: Integration developer can consume structured outcomes and artifacts from automated workflows.
- FR14: AI Agent can generate a final report that summarizes outcome, evidence, and recommended next action.
- FR15: Embedded engineer can compare the results of repeated runs for the same scenario.
- FR15a: AI Agent can request a compressed evidence summary (attention hints, key anomalies, verdict-relevant signals) sized to fit within a bounded context window, rather than consuming raw full-channel evidence.
- FR15b: The system must produce evidence summaries that preserve verdict-critical information while discarding redundant or low-relevance data, with explicit indication of what was omitted.

### Diagnosis, Escalation & Safety Governance

Defines how the product turns evidence into decisions, applies support boundaries, and governs risky actions.

- FR16: AI Agent can receive a structured diagnosis when a supported task does not validate successfully.
- FR17: AI Agent can receive explicit escalation guidance when evidence is insufficient, recovery is unsafe, or the situation exceeds the supported boundary.
- FR18: Embedded engineer can review the reason, supporting evidence, and recommended next action for any escalated task.
- FR19: Support engineer can classify a failed or escalated run by failure type for investigation and handoff.
- FR20: AI Agent can determine whether a requested action or observed situation is supported, unsupported, or unknown before relying on the result.
- FR21: Embedded engineer can see the support-boundary status and reason for any task or environment before approving or relying on its outcome.
- FR22: Embedded engineer can require human approval before high-risk task steps that may change target hardware state.
- FR23: Team maintainer can define when human approval is required for task steps or final outcomes.
- FR24: Integration developer can distinguish success, diagnosis, escalation, unsupported, and unknown outcomes in downstream workflows.
- FR24a: AI Agent can declare and query device roles (`golden`, `dut`, `external_target`) before executing a self-hosting task.
- FR24b: The system must require explicit device identity, firmware/bitstream version, and topology identity before any state-changing action in a two-board rig.
- FR24c: The system must prevent DUT build artifacts from being applied to Golden AgentProbe unless a human explicitly authorizes Golden upgrade mode.

### Validation Scenario Design, Templates & Reproducibility

Defines how teams turn validation intent into reusable, executable test assets.

- FR25: Embedded engineer can define project-specific validation context as reusable project assets.
- FR26: AI Agent can execute a task using saved project context rather than ad hoc setup.
- FR27: Embedded engineer can version, compare, and update project validation assets over time.
- FR28: Platform administrator can publish validated project templates for repeated use.
- FR29: Embedded engineer can replay a prior scenario using preserved task context and artifacts.
- FR30: Support engineer can restore the execution context of a previous run for diagnosis and reproduction.
- FR31: Platform administrator can create additional validated templates for new supported scenarios as the product expands.
- FR32: Hardware test engineer can define repeatable validation scenarios, preconditions, and expected outcomes for supported hardware workflows.
- FR33: Hardware test engineer can package nominal-path and failure-path validation scenarios into reusable regression sets.
- FR34: Hardware test engineer can verify that required hardware setup conditions are satisfied before a validation result is treated as trustworthy.

### Mock Fidelity & Divergence Detection

Defines how mock engine results relate to real hardware behavior and how divergence is surfaced.

- FR34a: Every mock model must declare its fidelity boundary: which behavioral aspects are faithfully simulated, which are approximated, and which are not covered.
- FR34b: AI Agent can query the fidelity declaration of any active mock before relying on mock-based evidence for a verdict.
- FR34c: When a task transitions from mock-based validation to real-hardware validation, the system must automatically flag any divergence between mock-predicted and hardware-observed outcomes.
- FR34d: If mock-based evidence supports a pass verdict but real-hardware evidence contradicts it, the system must surface a mock-divergence diagnostic with root-cause hints (timing, electrical, behavioral model gap).
- FR34e: Embedded engineer can review a mock-vs-real comparison report for any scenario that was validated in both environments.


### Review, Collaboration & Workflow Integration

Defines how humans, teams, and automation consume outcomes, make decisions, and keep work moving.

- FR35: Embedded engineer can approve, reject, or take over from a completed or escalated AI-led task.
- FR36: Embedded engineer can make a continue, rollback, or handoff decision without repeating the full bench workflow when sufficient evidence is available.
- FR37: Support engineer can triage runs using terminal outcomes, evidence packages, and run history.
- FR38: Integration developer can route task outcomes into team workflows based on explicit terminal states.
- FR39: Team maintainer can define which task outcomes trigger pass, block, escalation, or review behavior in their workflow.
- FR40: Platform administrator can surface validated environments, shared assets, and device readiness for team use.
- FR41: Embedded engineer can hand off a task's evidence, context, and next steps to another team member or agent.
- FR42: Support engineer can compare a current run against prior runs to identify meaningful differences in evidence, outcome, or task context.
- FR43: Platform administrator can mark shared templates or environments as validated, deprecated, or unavailable for team use.
- FR44: Embedded engineer can review and resolve pending approval requests for in-progress tasks.
- FR45: AI Agent can pause at a required approval point and resume the same task after a human decision.
- FR46: Developer or AI Agent can see whether selected shared assets are validated, deprecated, or unavailable before starting a task.

### Developer Access & Adoption

Defines how developers and agents discover, enter, and automate the supported product workflow.

- FR47: Developer can install and begin using AgentProbe through a supported local onboarding flow.
- FR48: Developer can initialize a project for supported use with the required local context and assets.
- FR49: AI Agent can discover the supported capabilities, usage constraints, and operating guidance needed to invoke the product correctly.
- FR50: Developer can operate AgentProbe in both human-readable and machine-readable modes.
- FR51: Developer can determine whether their environment is ready and supported before running a task.
- FR52: Developer can learn the supported workflow through a quickstart and end-to-end reference example.
- FR53: Integration developer can automate supported task flows from non-interactive workflows without a language-specific SDK.

## Non-Functional Requirements

Only the NFR categories that materially affect AgentProbe's product viability are included here.

These NFRs prioritize auditable bounded autonomy over raw latency or broad-scale optimization.

### Reliability

- NFR1: Every supported task must end in an explicit terminal state or an auditable interruption state; silent termination is not acceptable.
- NFR2: When a task fails or is interrupted, the system must preserve run identity, accumulated evidence, current task context, and the failure or interruption reason for later review.
- NFR3: If a task is interrupted by process, host, or communication failure, the system must retain the last known run state and all available evidence needed for audit and safe recovery.
- NFR4: For repeated runs of the same supported scenario with the same validated context, the system must produce the same terminal-state class unless the underlying evidence materially changes.
- NFR5: The system must not report a validation success when evidence is insufficient to support that conclusion.

### Safety

- NFR6: Any blacklisted operation must require explicit user authorization each time it is requested.
- NFR7: Authorization for a blacklisted operation must be scoped to the specific requested action and must not be implicitly reused across later actions, tasks, or sessions.
- NFR8: If a task reaches a blacklisted or otherwise high-risk action without the required authorization, the system must pause or refuse the action and preserve the task context for review or resumption.
- NFR9: Any task that changes target hardware state must leave an auditable record of the action taken, the authorization state, and the resulting terminal outcome.
- NFR10: If the system cannot determine whether a requested state-changing action is within the supported safety boundary, it must default to escalation or refusal rather than execution.

### Security

- NFR11: Core supported closed-loop workflows must be executable without mandatory cloud dependency.
- NFR12: By default, task evidence, project assets, logs, and reports must remain local unless a user explicitly exports or shares them.
- NFR13: Evidence packages and shared validation assets must preserve provenance and modification history sufficient to detect unauthorized or untrusted changes.

### Performance

- NFR14: Any in-progress task, especially non-interactive execution, must emit a progress update or heartbeat at least once within every 30-second window until it reaches a terminal state or approval point.

### Integration / Interoperability

- NFR15: Every non-interactive invocation must expose an explicit terminal outcome in structured output on completion, interruption, or approval wait.
- NFR16: Structured terminal-state outputs, outcome taxonomy, and machine-readable artifact references must remain stable across patch and minor releases, or be explicitly versioned when changed.
- NFR17: Every machine-readable output must include an explicit schema or contract version identifier.
- NFR18: Automated workflows must be able to distinguish success, diagnosis, escalation, unsupported, unknown, and approval-pending states without parsing human-oriented text.
- NFR19: Machine-readable outputs must preserve run identity and artifact references so downstream systems can correlate results with stored evidence.
- NFR20: Human-readable and machine-readable outputs for the same run must represent the same terminal-state semantics.

### Run Context Reporting & Physical Safety Guardrails

- NFR21: Every task outcome must include run_sequence, same_class_streak, and elapsed_since_first_run in both human-readable and machine-readable output, providing sufficient context for Agent or Skill to make loop-control decisions.
- NFR22: The system must not refuse or throttle a supported, non-destructive task invocation based on iteration count, elapsed time, or failure streak; loop-control policy is the responsibility of the Agent or Skill layer.
- NFR23: The system must refuse or require explicit human authorization for operations that risk irreversible physical damage (e.g., Flash write cycles approaching endurance limit, voltage settings exceeding target rating), regardless of Agent or Skill instructions.
- NFR23a: Every self-hosting run outcome must include `source_device_role`, `target_device_role`, `device_id`, `serial`, `firmware_version`, `bitstream_version`, and `connection_topology_id`.
- NFR23b: If Golden/DUT identity or topology cannot be verified, the system must return `unknown` or `approval_pending` instead of executing a state-changing action.
- NFR23c: Golden firmware/bitstream update mode must be disabled by default and require explicit human authorization scoped to the specific Golden device and artifact.

### Skill & Extension Governance

- NFR24: Every Skill file must declare a schema version; the system must validate Skill files against the declared schema before loading.
- NFR25: Skill files that fail schema validation must be rejected with an explicit error identifying the incompatibility, rather than silently degrading behavior.
- NFR26: Community-contributed Skill files must pass an automated validation gate (schema compliance, safety boundary declaration, fidelity statement) before being usable in production tasks.
- NFR27: When a Skill schema version is deprecated, the system must emit a clear migration warning with actionable guidance, and continue supporting the prior version for at least one minor release cycle.
- NFR27a: Every Skill file must declare `supported_capabilities`, `not_supported`, and `planned_capabilities` lists so an Agent can distinguish executable Phase 1 behavior from future roadmap or unsupported requests without relying on prose interpretation.

### Mock Fidelity Assurance

- NFR28: Every mock model must include a machine-readable fidelity declaration that specifies supported behavioral aspects, known approximations, and uncovered edge cases.
- NFR29: The system must not allow a mock-only verdict to be reported as equivalent to a hardware-validated verdict; mock-based outcomes must carry an explicit provenance tag.
- NFR30: Mock-vs-real divergence detection must trigger automatically when both mock and hardware evidence exist for the same scenario, without requiring manual comparison.

### Performance Budget

- NFR31: A single closed-loop iteration (build → flash → capture → diagnose → verdict) for a supported V1 scenario must complete within 120 seconds under normal operating conditions.
- NFR32: Evidence summary generation must complete within 5 seconds regardless of raw evidence volume.
- NFR33: CLI command response for non-task queries (status, support-boundary check, asset listing) must return within 3 seconds.



---

## Changelog

| 版本 | 日期 | 作者 | 变更摘要 |
|------|------|------|----------|
| v1.1 | 2026-04-30 | bender | AI-native 防御性设计增强（基于第一性原理 review） |

| v1.2 | 2026-04-30 | bender | 职责分层修正：工具层 vs Agent/Skill 层边界厘清 |

| v1.3 | 2026-05-06 | bender | 战略主线修正：two-board self-hosting 与 AI-native 开发范式成为 Phase 1 North Star |

| v1.4 | 2026-05-07 | bender | Claude review 补强：观测木桶公式、Skill capability boundary、阶段切换条件 |

### v1.4 变更明细（2026-05-07）

**修正原则：明确 AgentProbe 的阶段价值来自扩大 Agent 的可观测范围、可执行范围与语义转换质量。**

本次没有方向性修正，属于对 PRD/架构已正确方向的补强。

| 区域 | 变更 | 原因 |
|------|------|------|
| Vision | 增加 `Agent 闭环能力 = min(推理能力, 可观测范围, 可执行范围, 语义转换质量)` 木桶公式 | 明确可观测性决定闭环能力上限 |
| User Journeys | 将 Phase 1 主 journey 从 SHT30 demo 改为 Golden → DUT self-hosting 场景 | 与 v1.3 North Star 对齐 |
| Phased Development | 增加 Observation-to-Reasoning Bottleneck 阶段切换条件 | 定义何时从观测/执行扩展转向 V3 Agent 推理层重构 |
| Skill Governance | 增加 `supported_capabilities`、`not_supported`、`planned_capabilities` 要求 | 防止 Agent 把 roadmap 当成当前可执行能力 |

### v1.3 变更明细（2026-05-06）

**修正原则：先证明 AI-native 软硬件开发范式，再扩展外部 demo 与功能覆盖。**

AgentProbe 的 V1 不以“功能完整的调试硬件”定义，而以 **Golden AgentProbe → DUT AgentProbe** 的 self-hosting loop 定义。温湿度采集器仍可作为外部展示示例，但不替代内部 North Star。

**新增/修正：**

| 区域 | 变更 | 原因 |
|------|------|------|
| Executive Summary | 增加 AI-native development paradigm 与 self-hosting validation 叙事 | 使产品目标高于测试自动化 |
| Hardware Role Definitions | 明确 AgentProbe hardware、Golden、DUT、external target、AI Agent、人类工程师 | 避免 Zynq 产品硬件与 STM32/DUT 被测硬件混淆 |
| V1 Scope | 改为 two-board self-hosting + SPI-first Mock/Analyzer + CMSIS-DAP + CLI/daemon/Skill | 与架构实现路径一致，降低 I2C demo 对 MVP 的绑架 |
| Technical Success | 明确 I2C/SHT30 是 Phase 1.5 或外部 demo 路径 | 消除 PRD 与 architecture 的 V1 范围冲突 |
| Safety Boundary | 增加 device role / serial / firmware version / topology 要求，禁止 Agent 自动升级 Golden | 防止两块相同硬件互联时发生误刷、误测、误判 |

### v1.2 变更明细（2026-04-30）

**修正原则：工具是手和眼睛，不是大脑。**

AgentProbe 的职责是提供事实和保障物理安全，不包括替 Agent 做战略决策或维护 Agent 记忆。示波器不会因为你量了5次就拒绝第6次。

**删除：**

| ID | 内容 | 删除原因 |
|----|------|----------|
| FR34f-j | Agent 自校准与诊断历史引用 | 属于 Agent 记忆模块，不是工具职责；待自建 Agent 时再考虑 |

**修正：**

| ID | 原版 | 修正版 | 原因 |
|----|------|--------|------|
| FR8a | Daemon 发出 loop-break 信号 | CLI 输出 run_sequence / same_class_streak / elapsed_time，供 Agent/Skill 消费 | 循环控制是决策，不是工具该做的 |
| FR8b | Agent 查询剩余迭代预算 | 系统不得基于迭代次数拒绝非破坏性操作 | 工具无条件执行，Skill 写 SOP |
| NFR21 | Daemon 强制迭代上限 + 自动 escalation | CLI 输出运行上下文字段，循环策略归 Skill | 手不应该有主见 |
| NFR22 | 连续同类失败 Daemon 强制 escalation | 系统不得基于失败次数拒绝非破坏性操作 | 同上 |
| NFR23 | 迭代预算消耗可见 | 物理损伤风险操作必须拒绝或要求人类授权 | 唯一合理的工具侧拒绝：物理安全 |

**职责分层总结：**

| 职责 | 归属 | 机制 |
|------|------|------|
| 报告事实（第几次、结果是否重复） | AgentProbe CLI | `--json` 输出字段 |
| 循环控制（要不要停、何时升级） | Skill / CLAUDE.md | Agent SOP 规则 |
| 物理安全护栏（Flash 寿命、过压） | Daemon | 硬拒绝，不可被 Agent 覆盖 |


### v1.1 变更明细（2026-04-30）

**新增 FR：**

| ID | 内容 | 动机 |
|----|------|------|
| FR8a | 迭代预算超限时强制 loop-break | Agent 可能陷入无限修正循环，需要外部硬约束 |
| FR8b | Agent 可查询剩余迭代预算 | 让 Agent 能感知自身资源消耗，做出 escalation 决策 |
| FR15a | 压缩证据摘要（attention hint） | Agent context window 有限，原始证据可能超出认知带宽 |
| FR15b | 摘要必须保留 verdict-critical 信息 | 防止摘要丢失关键诊断线索 |
| FR34a-e | Mock 保真度声明与 mock-vs-real 分歧检测 | Agent 无法自行判断 mock 结论是否可迁移到真实硬件 |


**新增 NFR：**

| ID | 内容 | 动机 |
|----|------|------|
| NFR21-23 | 运行上下文报告与物理安全护栏 | 工具只报告事实，循环决策归 Agent/Skill 层 |
| NFR24-27 | Skill 文件 schema 版本化与治理 | 社区贡献的 Skill 可能破坏 Agent 确定性推理 |
| NFR28-30 | Mock 保真度保证 | 防止 mock-only 结论被错误等同于硬件验证结论 |
| NFR31-33 | 端到端性能预算 | 原文仅有 30s heartbeat，缺少闭环延迟约束 |

**设计原则变更：**

本次修订的核心原则是：**AI-native 设计不仅要为 Agent 的能力设计接口，还必须为 Agent 的认知局限性（context window、hallucination tendency、loop risk、confidence miscalibration）设计防御性约束。** 具体体现为：

1. **认知带宽防御**：证据摘要层，避免 Agent 被原始数据淹没
2. **循环风险防御**：硬性迭代预算，避免无限重试
3. **保真度边界防御**：Mock 结论必须携带 provenance，不可等同硬件验证
5. **生态质量防御**：Skill 文件必须经过 schema 验证，社区贡献不可绕过 gate
