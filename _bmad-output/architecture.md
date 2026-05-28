---
stepsCompleted: [1, 2, 3, 4, 5, 6, 7, 8]
inputDocuments:
  - PRD_AgentProbe.md
  - PRD_AgentProbe_Part3_continued.md
  - PRD_AgentProbe_Part4.md
  - _bmad-output/product-brief-e-project.md
  - _bmad-output/product-brief-e-project-distillate.md
  - _bmad-output/prd.md
  - prd_v1.2.md
workflowType: 'architecture'
project_name: 'AgentProbe'
user_name: 'bender'
date: '2026-04-21'
status: 'complete'
lastStep: 8
completedAt: '2026-05-06'
---

# Architecture Decision Document

_This document builds collaboratively through step-by-step discovery. Sections are appended as we work through each architectural decision together._

## Project Context Analysis

### Requirements Overview

**功能需求（基于 PRD v1.3 战略修正，8 大功能域 50+ 功能点）：**

| 功能域 | 关键功能 | 架构复杂度 |
|--------|---------|-----------|
| Self-hosting Rig | Golden AgentProbe ↔ DUT AgentProbe，显式 device role、serial、version、topology，禁止 Agent 自动升级 Golden | 极高 |
| Mock Engine | V1 SPI-first Mock；I2C/CAN/1-Wire/PWM 后移；4 级行为模型; fidelity declaration | 高 |
| Signal Analyzer | V1 8ch + SPI decode；16ch/多协议/高级触发后移 | 高 |
| Debug Controller | CMSIS-DAP v2, SWD+JTAG, Cortex-M 全系列, GDB/Semihosting/RTT | 中高 |
| Analog Subsystem | DAC 4ch 16bit, ADC 4ch 16bit, INA219 电流测量 | 中 |
| Fault Injection | 8 类故障注入 | 中 |
| Agent Integration | CLI 工具 + Skill 文件 + 本地守护进程（V1 不做 MCP/REST/WebSocket） | 中 |
| Observability | 统一事件模型, 结构化 JSON 输出, 断言引擎 | 高 |
| CLI Tool | Python CLI (`agentprobe`/`ap`), `--json` 全局支持，replay transport | 中 |

**非功能需求：**

| 维度 | 约束 | 架构影响 |
|------|------|---------|
| 实时性 | 100MHz 采样, <1μs 协议响应 | PL 硬实时处理，不可依赖 PS/PC |
| 吞吐量 | USB 2.0 HS 实际 ~40MB/s | FPGA 端必须做预处理/压缩/触发过滤 |
| 可靠性 | ESD/过压/过流保护 | 硬件保护电路 |
| 兼容性 | Cortex-M0/M0+/M3/M4/M7/M33 | SWD 协议抽象层 |
| 可扩展性 | FPGA bitstream 可升级, Mock 模型库可扩展 | 模块化 RTL + 模型加载机制 |

**Scale & Complexity:**

- Primary domain: 嵌入式全栈（Zynq PL RTL + PS 固件 + PC 工具链 + AI Agent 集成）
- Complexity level: **高**（6-7 个技术域）
- Estimated architectural components: ~15 主要组件

### First Principles Insights（第一性原理分析）

**根本认知 #1：AgentProbe 是"物理域 ↔ 数字域"的翻译器**

架构核心挑战不是功能丰富性，而是翻译的准确性和实时性。

**根本认知 #2：系统存在两条根本不同的数据流**

| 数据流 | 特征 | 架构要求 |
|--------|------|---------|
| 控制流（Agent → 硬件） | 低频，ms 级延迟可接受 | 必须可靠，不可丢失 |
| 观测流（硬件 → Agent） | 高频，高吞吐 | 必须高吞吐，可容忍少量丢失 |

两条流在 USB 传输层、PS 固件层、PC 软件层都应有独立通道。

**根本认知 #3：USB 带宽是真正的硬约束**

16ch@100MHz 原始数据 = ~200MB/s，USB 2.0 HS 实际 ~40MB/s。FPGA 端必须做重数据预处理（协议解码、事件压缩、触发过滤）。FPGA 资源紧张反而是伪问题（功能可分时复用）。

**根本认知 #4：Agent 软件层不自研**

V1 Agent 直接使用 Claude Code / OpenCode，AgentProbe 以 CLI 插件 + Skill 文件形式提供硬件能力。不需要自研 Agent、MCP Server、GUI。

**根本认知 #5：V1 必须证明 AI-native 开发范式，而不是硬件功能拼盘**

测试自动化、回归验证和报告生成是 AgentProbe 带来的副作用；V1 的核心证明是：Agent 能通过稳定的物理感知/控制 contract 参与软硬件实现本身的开发。最强 proof 不是一次外部 demo，而是 **two-board self-hosting loop**：Golden AgentProbe 帮助 Agent 开发、烧录、观测、诊断和修复 DUT AgentProbe。

### Hardware Role Model（硬件角色模型）

| 角色 | 架构含义 | 关键约束 |
|------|----------|----------|
| AgentProbe product hardware | Zynq-7020 SoM + minimal baseboard 的产品硬件实现 | 提供 USB、PS/PL、SWD、Mock、Analyzer、Evidence 通道 |
| Golden AgentProbe | 已知稳定版本，作为可信观测/烧录工具 | Agent 不得自动升级；role、serial、firmware/bitstream version 必须显式记录 |
| DUT AgentProbe | 正在开发或验证中的 AgentProbe | 可被烧录、复位、观测、诊断；所有 state-changing action 必须绑定 DUT identity |
| External target | STM32 M3/M4/M33 等外部被测板 | 用于设计伙伴 reference demo，不替代 self-hosting proof |
| Host PC | 运行 CLI、daemon、Agent 与 artifact store | 必须保持 replay transport 与 USB transport 上层行为一致 |

所有 run outcome、evidence pack、approval record 和 report 都必须包含 device role、device_id/serial、firmware_version、bitstream_version、connection_topology_id。缺少这些字段时，系统应返回 `unknown` 或 `approval_pending`，不得输出成功 verdict。

### Architecture Decision Records（架构辩论结论）

**ADR-1: Mock 模型三级分层执行**

| 层 | 位置 | 职责 | 延迟预算 |
|----|------|------|---------|
| Protocol Layer | FPGA | 总线时序、ACK/NAK、BUSY、寄存器表查找 | < 1μs |
| Command Layer | PS | 命令解析、简单状态机、响应数据准备 | < 100μs |
| Behavior Layer | PC (可选) | 复杂行为模拟、大容量存储、模型脚本 | < 10ms (用 BUSY 缓冲) |

**ADR-2: Agent 集成 = CLI-first + Skill 文件 + 本地守护进程**

```
Claude Code / OpenCode
  → 读取 Skill 文件 (能力描述+使用指南)
  → 执行 shell: `ap <command> --json`
    → agentprobe CLI (Python, pip install)
      → agentprobe daemon (后台常驻, USB 通信)
        → USB → PS → PL → 物理操作
```

**ADR-3: USB 复合设备 5 endpoint 分流**

| Endpoint | 类型 | 用途 | 带宽预算 |
|----------|------|------|---------|
| EP1 | Bulk | 命令控制 (双向) | ~1 MB/s |
| EP2 | Bulk IN | 事件数据流 (预处理后) | ~5 MB/s |
| EP3 | Bulk IN | 逻辑分析仪 (触发式突发) | 突发 ~20 MB/s |
| EP4 | CDC | 虚拟串口 (UART/RTT/Semihosting) | ~0.5 MB/s |
| EP5 | HID | CMSIS-DAP v2 | ~1 MB/s |

**ADR-4: V1 精简范围（修订：self-hosting + SPI-first）**

| 组件 | V1 | V2+ |
|------|-----|-----|
| Two-board self-hosting rig | ✅ Golden ↔ DUT，显式 device role/topology | 多 rig、共享实验台资产管理 |
| Replay transport + canonical fixtures | ✅ | 大规模 capture/replay 平台化 |
| SWD (CMSIS-DAP v2) | ✅ 用于 DUT 烧录/控制 | 更广目标芯片 |
| Mock: SPI Slave ×1 (L0-2) | ✅ SPI-first | I2C/CAN/1-Wire/PWM |
| UART: 1 路透传+嗅探 | ✅ | UART Mock |
| 信号分析: 8ch + SPI 解码 | ✅ | 16ch, 高级触发, 多协议 |
| CLI 核心命令 + `--json` | ✅ | 高级命令 |
| Skill 文件 | ✅ | MCP Server / IDE 集成 |
| Daemon (USB+事件聚合) | ✅ | PC 端复杂 Mock 行为层 |
| I2C/SHT30 外部 demo | Phase 1.5，可选 | 设计伙伴 reference demo |
| 模拟子系统 | ❌ | DAC/ADC/INA219 |
| 故障注入 | 受控 failure catalog 最小集 | 全部 |
| GUI | ❌ | Electron |

### Technical Constraints & Dependencies

**历史硬件基线（已被 ADR-5 superseded）：**
- 原方案：STM32H743VIT6 + Lattice ECP5-25K + USB HS + W25Q128
- 当前决策：Zynq-7020 SoM + minimal baseboard。后续实现不得再以 STM32H743/ECP5 作为 AgentProbe 产品硬件默认路径；STM32 M3/M4/M33 是 external target 支持边界。

**软件依赖：**
- 编译器: arm-none-eabi-gcc（V1 唯一支持）
- 调试器协议: OpenOCD / pyOCD（CMSIS-DAP v2 兼容）
- Agent 宿主: Claude Code / OpenCode（第三方，不可控）
- CLI: Python + Click 框架
- FPGA 工具链: Vivado（Zynq-7020 免费版支持）

### Cross-Cutting Concerns

1. **PS ↔ PL 通信协议** — AXI-Lite / AXI-Stream / interrupt 是核心数据通道，所有子系统依赖
2. **事件管道** — PL FIFO / DMA → PS → USB → Daemon → CLI JSON 输出，端到端延迟和可靠性
3. **控制流/观测流分离** — USB endpoint 分流 + PS 内部独立处理路径
4. **I/O 路由矩阵** — 任意引脚到任意功能映射，跨所有子系统
5. **固件/bitstream 更新** — BOOT.bin / firmware / bitstream 需版本对齐和可靠回滚
6. **CLI 输出格式一致性** — `--json` 全局支持，Agent 可解析
7. **安全护栏** — 硬件层(ESD/过流) + Skill 文件中的操作指引
8. **Self-hosting device identity** — 所有 state-changing action 必须绑定 role、serial、firmware/bitstream version 和 topology，避免 Golden/DUT 混淆

## Starter Template Evaluation

### Primary Technology Domain

CLI 开发工具 — AgentProbe 是嵌入式开发 CLI 工具（`agentprobe`/`ap`），包含 Python CLI + STM32 固件 + FPGA RTL 三个技术域。Starter 评估针对 Python CLI 项目。

### Starter Options Considered

| 方案 | 评估 | 结论 |
|------|------|------|
| `uv init --lib` + 手动配置 | 最小起步，按需添加，Astral 生态统一 | ✅ 选定 |
| cookiecutter-hypermodern-python | Poetry（已被 uv 取代），模板过重 | ❌ 淘汰 |
| Typer 替代 Click | 增加依赖但收益有限，ADR-2 已选 Click | ❌ 淘汰 |

### Selected Starter: `uv init --lib` + Astral 工具链

**Rationale（经第一性原理验证）：**

1. **可复现性**：`uv.lock` 跨平台锁文件确保 Agent 和人类看到同样的环境
2. **工具链减法**：Ruff 替代 flake8+black+isort+pyupgrade+autoflake+pydocstyle（6→1），减少维护负担
3. **可靠性优先**：选择 mypy（battle-tested）而非 ty（beta），因为代码控制物理硬件
4. **Monorepo 友好**：`cli/` 子目录隔离 Python 构建系统，不污染固件/FPGA 工程师环境

**Monorepo 顶层结构（架构师辩论共识）：**

```
agentprobe/
├── cli/                 ← Python CLI (uv 管理)
│   ├── src/agentprobe/
│   ├── tests/
│   └── pyproject.toml
├── firmware/            ← Zynq PS firmware (CMake)
│   ├── src/
│   ├── include/
│   └── CMakeLists.txt
├── fpga/                ← Zynq PL / Vivado (Makefile)
│   ├── rtl/
│   ├── sim/
│   └── Makefile
├── hardware/            ← KiCad 原理图/PCB
├── docs/                ← 文档
├── skills/              ← Agent Skill 文件
├── .github/workflows/   ← CI (按 path 过滤)
├── README.md
└── Makefile             ← 顶层编排 (make cli, make fw, make fpga, make all)
```

**Initialization Command:**

```bash
mkdir agentprobe && cd agentprobe
uv init cli --lib
cd cli
uv add click
uv add --dev pytest pytest-cov ruff mypy
cd ..
mkdir -p firmware/{src,include} fpga/{rtl,sim,constraints} hardware docs skills
```

**Architectural Decisions Provided by Starter:**

**Language & Runtime:**
- Python ≥3.11, src layout (`cli/src/agentprobe/`)
- `pyproject.toml` 管理，`uv.lock` 锁文件

**Build Backend:**
- hatchling（uv 默认）+ hatch-vcs（git tag 驱动版本号）

**Type Checking（分层策略）：**
- `protocol/` + `daemon/`（硬件控制层）→ mypy strict mode
- `cli/`（命令层）→ mypy 默认模式
- CI 中强制执行

**Linting & Formatting:**
- Ruff — lint（800+ 规则）+ format（Black 兼容），单一工具替代 6 个

**Testing:**
- pytest + pytest-cov, `tests/` 目录

**CI/CD:**
- 3 个独立 workflow：ci-cli.yml / ci-firmware.yml / ci-fpga.yml
- 按 `paths` 触发，互不干扰

**Development Experience:**
- `uv run` 即用虚拟环境
- 顶层 Makefile 跨域编排（`make cli` / `make fw` / `make fpga` / `make all`）

**Workspace Migration Path:**
- V1 使用简单子目录。若出现第二个 Python 包（如 `pytest-agentprobe`），迁移到 uv workspace。

**Note:** 项目初始化（使用上述命令）应作为第一个实现 Story。

## Core Architectural Decisions

### ⚠️ 重大架构变更：Zynq-7020 SoC 统一架构

原设计采用 STM32H743 + Lattice ECP5-25K 双芯片方案。经第一性原理分析，发现 MCU↔FPGA 通信是不必要的复杂度——MCU（调试/烧录）和 FPGA（逻辑分析/Mock）功能上独立，但物理上 ECP5 无 USB PHY，必须经 MCU 中转数据。

**决策：切换到 Xilinx Zynq-7020 SoC（ARM Cortex-A9 + FPGA 同芯片）**，消除芯片间通信问题。

### Decision Priority Analysis

**Critical Decisions（阻塞实现）：**

1. 硬件平台：Zynq-7020 SoM + 自定义底板
2. PS 软件环境：Bare-metal / FreeRTOS
3. PS↔PL 通信：AXI 总线（AXI-Lite 控制 + AXI-Stream 数据）
4. Daemon↔CLI IPC：localhost TCP
5. Self-hosting rig：Golden/DUT 角色、连接拓扑、误刷保护和 evidence identity

**Important Decisions（塑造架构）：**

6. Mock 模型定义格式：TOML
7. 事件数据格式：JSON Lines (JSONL)
8. USB 消息帧：自定义二进制 TLV
9. FPGA 设计方法：Vivado IP Integrator + 参数化设计
10. 分层 mypy 策略

**Deferred Decisions（V2+）：**

- 双核 AMP 优化（V1 单核足够）
- Linux 迁移（如需更复杂的设备端逻辑）
- Ethernet 高带宽通道
- 自研 Zynq 核心板（替代 SoM）

### ADR-5: Zynq-7020 SoC 统一架构（替代 STM32+ECP5）

| 维度 | 决策 |
|------|------|
| SoC | Xilinx Zynq-7020 (XC7Z020-CLG484) |
| PS | 双核 Cortex-A9 @866MHz（V1 仅用 CPU0） |
| PL | 85K logic cells, 220 DSP, 630KB BRAM |
| 内存 | 外置 DDR3/DDR3L ≥256MB（SoM 提供） |
| 启动 | QSPI Flash（SoM 提供） |
| USB | PS 侧 USB 2.0 + 外置 ULPI PHY（如 USB3320） |
| 工具链 | Vivado（PL）+ Vitis/arm-none-eabi-gcc（PS）+ uv/Python（CLI） |

**Rationale：**
- 消除 MCU↔FPGA 通信协议设计（AXI 片上总线自动解决）
- 单芯片简化 PCB、供电、时钟
- 85K logic cells（3.5× ECP5-25K），为 V2 功能预留充足空间
- V1 用 SoM 快速验证，符合 "Phase 1 = prove one credible loop" 哲学

**Trade-offs Accepted：**
- 工具链从开源（Yosys+nextpnr）变为闭源（Vivado，免费版支持 Z-7020）
- 芯片成本从 ~$15-20 升至 ~$60-80（SoM）
- Vivado 综合时间 15-30 min（通过参数化设计减少重综合频率）

### ADR-9: Two-board Self-hosting Validation Rig

| 维度 | 决策 |
|------|------|
| Rig 形态 | 一块 Golden AgentProbe + 一块 DUT AgentProbe + Host PC |
| Golden 权限 | 可观测、烧录、复位、Mock DUT；不得被 Agent 自动升级 |
| DUT 权限 | 可被 Agent 构建产物烧录、复位、观测、诊断 |
| 连接 | Golden SWD → DUT debug header；Golden analyzer/GPIO/UART/SPI → DUT 可观测/可交互引脚 |
| 配置资产 | `scenario.toml` / routing / topology 必须声明 role、serial、连接、支持边界 |
| Evidence 要求 | 所有事件和 verdict 必须携带 source_device_role 与 target_device_role |

**Rationale：**
- 这是 AgentProbe 最强的产品证明：不是“Agent 用工具测试玩具项目”，而是“Agent 用 AgentProbe 参与 AgentProbe 本身演进”。
- 两块硬件互联把 AI-native 开发范式变成可审计 proof，而不仅是测试自动化。
- Self-hosting rig 迫使协议、输出、设备身份、安全审批和证据模型从第一天就按生产级 contract 设计。

**Safety Constraints：**
- Golden firmware/bitstream 只能通过人类批准升级。
- DUT build artifact 不能刷入 Golden；daemon 必须在 state-changing action 前校验 role、serial、expected firmware family 和 topology。
- 如果设备 identity、连接拓扑或版本窗口无法确认，操作必须进入 `approval_pending` / `unknown`，不得继续执行成功路径。

**Phase 1 Acceptance：**
- Agent 能修改 DUT 的一个受控 firmware/PL 行为，构建并烧录 DUT。
- Golden 捕获 DUT 行为，生成 evidence pack。
- Agent 能基于 evidence 完成至少一次诊断、修复或 explicit escalation。
- 非原作者可基于相同 scenario/topology 复跑一次，不依赖口头说明。

### ADR-1（修订）: Mock 模型三级分层执行

| 层 | 位置 | 职责 | 延迟预算 |
|----|------|------|---------|
| Protocol Layer | **PL**（FPGA fabric） | 总线时序、ACK/NAK、BUSY、寄存器表查找 | < 1μs |
| Command Layer | **PS**（Cortex-A9 via AXI） | 命令解析、简单状态机、响应数据准备 | < 100μs |
| Behavior Layer | PC（可选） | 复杂行为模拟、大容量存储、模型脚本 | < 10ms（用 BUSY 缓冲） |

变更：Command Layer 从"MCU"改为"PS via AXI"，延迟从 SPI 传输变为 AXI 寄存器读写（~ns 级），性能大幅提升。

### ADR-3（修订）: USB 复合设备架构

USB 由 PS 侧 Cortex-A9 直接管理，FPGA 数据通过 AXI→PS→USB 通道。

| Endpoint | 类型 | 用途 | 带宽预算 |
|----------|------|------|---------|
| EP1 | Bulk | 命令控制（双向） | ~1 MB/s |
| EP2 | Bulk IN | 事件数据流（PL→AXI→PS→USB） | ~5 MB/s |
| EP3 | Bulk IN | 逻辑分析仪（触发式突发） | 突发 ~20 MB/s |
| EP4 | CDC | 虚拟串口（UART/RTT/Semihosting） | ~0.5 MB/s |
| EP5 | HID | CMSIS-DAP v2 | ~1 MB/s |

变更：所有 endpoint 由 PS 统一管理，PL 数据通过 AXI-Stream + DMA 高效传输到 PS USB 缓冲区。

### 通信协议栈

**PS↔PL（片上）：**

| 接口 | 用途 | 方向 |
|------|------|------|
| AXI-Lite | 控制寄存器读写（配置 Mock、触发器、路由） | PS→PL / PL→PS |
| AXI-Stream + DMA | 高速数据流（逻辑分析、事件、Mock 数据） | PL→PS |
| 中断 | 事件通知（触发命中、FIFO 阈值、错误） | PL→PS |

**Daemon↔CLI（PC 端）：**

- 协议：localhost TCP（默认端口 `127.0.0.1:4729`）
- 格式：JSON-RPC 2.0（命令/响应）+ JSONL 流（事件推送）
- 理由：跨平台、简单、可扩展为本地 API

**PC↔Zynq（USB）：**

- 物理：USB 2.0 HS（ULPI PHY）
- 帧格式：自定义二进制 TLV（Type-Length-Value）
- 端点分流：见 ADR-3 修订

### 固件架构（PS 侧）

**软件环境：** FreeRTOS on Cortex-A9 (CPU0)

| 任务 | 优先级 | 职责 |
|------|--------|------|
| USB Task | 高 | USB 设备枚举、CDC/Bulk/HID 通信、命令解析分发 |
| SWD Task | 高 | CMSIS-DAP v2 协议处理，调用 PL 侧 SWD Engine |
| Event Task | 中 | 读取 PL 事件 FIFO（AXI-Stream DMA），聚合后 USB 上行 |
| Mock Mgmt | 中 | Mock 模型加载/配置，AXI-Lite 寄存器写入 |
| CLI Cmd Task | 低 | 非实时 CLI 命令处理（状态查询、配置变更） |

**V2 扩展路径：**
- 启用 CPU1 做 AMP，Event Task 和 Mock Mgmt 迁移到 CPU1。
- 增加 SWD 内部观测通道：ITM trace decode 作为 V2 优先能力，DWT 计数/事件作为轻量内部观测补充，ETM 仅在目标芯片、引脚、带宽和解码复杂度允许时进入 V2+。这些能力用于非停机观测 firmware 内部行为，补足 V1 主要依赖 UART、SPI、GPIO/logic capture 的外部观测路径。

### 数据模型与格式

**Mock 模型定义（TOML）：**

```toml
[device]
name = "BME280"
protocol = "spi"
mode = 0
max_freq_hz = 10_000_000

[registers]
0xD0 = { value = 0x60, name = "chip_id", access = "ro" }
0xF7 = { value = 0x80, name = "press_msb", access = "ro" }
0xF4 = { value = 0x00, name = "ctrl_meas", access = "rw" }
```

**事件数据格式（JSONL）：**

```jsonl
{"ts":1714400000.123,"type":"spi_transaction","bus":0,"mosi":"F4 2B","miso":"00 00","duration_us":12.5}
{"ts":1714400000.456,"type":"trigger_hit","channel":3,"value":1,"edge":"rising"}
{"ts":1714400000.789,"type":"assert_pass","rule":"voltage_in_range","measured":3.28}
```

**Evidence Envelope（JSON）：**

所有 evidence package 必须使用 envelope 包裹原始事件摘要、诊断结果和 artifact 引用。Envelope 是 Agent 消费物理证据的稳定边界，不能只依赖散落的 JSONL 事件。

```json
{
  "schema_version": "0.1.0",
  "run_id": "run_...",
  "trace_id": "trace_...",
  "source_device": {
    "role": "golden",
    "device_id": "ap_golden_01",
    "serial": "APG001",
    "firmware_version": "0.1.0",
    "bitstream_version": "0.1.0"
  },
  "target_device": {
    "role": "dut",
    "device_id": "ap_dut_01",
    "serial": "APD001",
    "firmware_version": "0.1.0-dev",
    "bitstream_version": "0.1.0-dev"
  },
  "connection_topology_id": "topology_self_hosting_v1",
  "build_result": {},
  "flash_result": {},
  "capture_result": {},
  "diagnosis_result": {},
  "regression_result": {},
  "verdict": "regression_pass",
  "confidence": "high",
  "artifact_refs": []
}
```

Envelope 必须携带 `schema_version`、`source_device`、`target_device` 与 `connection_topology_id`。如果这些字段缺失或无法校验，daemon / CLI 必须返回 `unknown` 或 `approval_pending`，不得输出成功结论。

**CLI 配置（TOML）：** `~/.agentprobe/config.toml`

```toml
[daemon]
port = 4729
auto_start = true

[device]
auto_detect = true
preferred_serial = ""

[output]
default_format = "json"
color = true
```

### FPGA 架构（PL 侧）

**设计方法：** Vivado IP Integrator (Block Design)

| IP Block | AXI 接口 | V1 资源估算 |
|----------|----------|------------|
| Logic Analyzer (8ch) | AXI-Stream → DMA | ~5K LUT |
| SPI Mock Engine | AXI-Lite + AXI-Stream | ~3K LUT |
| I/O Router Matrix | AXI-Lite | ~1K LUT |
| UART Bridge | AXI-Lite + FIFO | ~1K LUT |
| SWD Engine | AXI-Lite | ~2K LUT |
| AXI Interconnect + DMA | 自动生成 | ~5K LUT |
| **V1 总计** | | **~17K / 85K (20%)** |

**参数化设计原则（保护 AI 闭环响应时间）：**
- Mock 行为变更 = AXI 寄存器写入（μs 级）→ **不需要重新综合**
- 逻辑分析触发条件变更 = 寄存器配置 → **不需要重新综合**
- 仅新增协议类型（如 I2C Mock）才需要重新综合（15-30 min）
- 所有可配置参数通过 AXI-Lite 寄存器暴露

### 构建与分发

| 构建域 | 工具 | 输出 |
|--------|------|------|
| PL (FPGA) | Vivado + TCL 脚本 | bitstream (.bit) |
| PS (固件) | Vitis / arm-none-eabi-gcc + FreeRTOS | ELF binary |
| CLI (Python) | uv + hatchling | PyPI wheel |
| 集成 | BOOT.bin = FSBL + bitstream + ELF | Zynq 启动镜像 |

**固件分发策略：**
- `ap firmware update` 命令通过 USB DFU 或自定义协议更新 Zynq BOOT.bin
- 固件 binary 随 CLI PyPI 发布（作为 package data）或从 GitHub Releases 下载
- CLI 启动时检查固件版本兼容性，不兼容时提示用户更新

**版本对齐：** CLI 和固件共用 git tag 版本号（hatch-vcs 驱动），协议版本号嵌入 USB 描述符。

### Technical Constraints & Dependencies（修订）

**硬件约束（已更新）：**
- SoC: **Zynq-7020** (XC7Z020-CLG484, 双核 A9 + 85K PL)
- 平台: **V1 使用 Zynq SoM**（如 MYIR Z-turn / Enclustra Mars ZX2）+ 自定义底板
- USB: USB 2.0 HS（PS 侧 + ULPI PHY，如 USB3320）
- 内存: DDR3 ≥256MB（SoM 提供）
- Flash: QSPI ≥16MB（SoM 提供，BOOT.bin 存储）
- 底板: 4 层板，仅连接器+保护电路+I/O

**软件依赖（已更新）：**
- FPGA 工具链: **Vivado**（免费版，支持 Zynq-7020）
- 固件编译: arm-none-eabi-gcc + FreeRTOS
- 调试协议: OpenOCD / pyOCD (CMSIS-DAP v2 兼容)
- Agent 宿主: Claude Code / OpenCode（第三方）
- CLI: Python + Click + uv

### Decision Impact Analysis

**Implementation Sequence:**
0. AI-native contract closure：`protocol.toml`、`address_map.toml`、outcome/evidence/scenario schema、version matrix
1. Replay-first loop：CLI + daemon + replay transport + canonical fixture，先证明 JSON/outcome/report contract
2. SoM 选型 + minimal baseboard / dev-kit topology 定义
3. Vivado Block Design（AXI 互联 + IP 框架）+ FreeRTOS 基础固件（USB 枚举 + 命令解析）
4. 端到端 single-board loop：CLI → daemon → USB → PS → AXI → PL → event → evidence pack
5. Device identity / role / topology enforcement：golden / dut / external-target
6. SWD Engine（CMSIS-DAP v2）用于 Golden 烧录 DUT
7. Logic Analyzer + UART bridge，用于 Golden 观测 DUT
8. Two-board self-hosting loop：Agent 修改 DUT → build → flash → observe → diagnose → fix/report
9. SPI Mock Engine + SPI decode，形成首个 Mock/Analyzer 可信闭环
10. I2C/SHT30 外部 demo（Phase 1.5，可选，不阻塞 Phase 1 self-hosting）
11. V2 internal observation track：ITM trace decode / DWT event counters；ETM 仅在目标硬件和带宽允许时进入 V2+

**Cross-Component Dependencies:**
- PL IP blocks 全部依赖 AXI Interconnect 框架
- PS USB Task 依赖 PL 各子系统的 AXI 寄存器映射
- CLI 命令结构依赖 USB 消息帧协议定义
- Daemon 事件流依赖 PL 事件 FIFO + PS Event Task
- Self-hosting 操作依赖 device registry、topology schema、approval gate 与 evidence identity 字段

## Implementation Patterns & Consistency Rules

### Pattern Categories Defined

**Critical Conflict Points Identified:** 24 个潜在冲突点，集中在 Python CLI、PS 固件、PL RTL、USB/TLV 协议、CLI↔Daemon IPC、事件系统六个边界。

本节只定义**一致性规则**，用于防止不同 AI Agent 在实现时做出不兼容的选择。

### Naming Patterns

**Python CLI 命名规则：**

- 包、模块、函数、变量一律 `snake_case`
- 类名一律 `PascalCase`
- 常量一律 `UPPER_SNAKE_CASE`
- CLI 命令与选项一律 `kebab-case`
- JSON 字段一律 `snake_case`

**Examples:**
- `agentprobe.protocol.frames`
- `SpiMockController`
- `start_capture()`
- `DEFAULT_SPI_FREQ_HZ`
- `ap mock-load --device-id 1234`

**PS 固件（C）命名规则：**

- 对外函数：`模块_动词_名词`
- 类型：`模块_名词_t`
- 错误码与宏：`AP_*`
- 全局共享资源：`g_*`
- mutex：`g_mtx_*`
- 文件名：`模块_功能.c/.h`

**Examples:**
- `usb_send_event()`
- `ap_err_t`
- `mock_config_t`
- `AP_ERR_TIMEOUT`
- `g_usb_state`
- `g_mtx_usb_tx`

**PL RTL（Verilog）命名规则：**

- 模块名一律 `ap_` 前缀
- 输入端口 `i_*`，输出端口 `o_*`，双向 `io_*`
- 寄存器 `r_*`，线网 `w_*`
- 参数 `P_*`
- 状态机状态 `ST_*`

**Examples:**
- `ap_spi_mock`
- `i_clk`, `o_valid`, `io_sda`
- `r_state`, `w_fifo_full`
- `P_FIFO_DEPTH`
- `ST_IDLE`

**Protocol / Artifact 命名规则：**

- 协议 SSOT 文件：`protocol.toml`
- AXI 地址注册表：`address_map.toml`
- 生成文件统一含 `_generated` 后缀
- Skill 契约文件：`skills/agentprobe.skill.md`

**Examples:**
- `cli\src\agentprobe\protocol\_generated.py`
- `firmware\include\ap_protocol_generated.h`
- `fpga\rtl\ap_protocol_generated.vh`

### Structure Patterns

**Project Organization:**

- 仓库使用 monorepo
- `cli\`、`firmware\`、`fpga\`、`hardware\`、`skills\` 明确分域
- 跨域契约仅允许通过 SSOT 文件进入各实现域
- 不允许在各域内手写复制协议常量

**Python Source Structure:**

```text
cli\
├── pyproject.toml
├── uv.lock
├── src\agentprobe\
│   ├── cli\
│   ├── daemon\
│   ├── protocol\
│   ├── models\
│   ├── core\
│   └── formatters\
├── tests\
│   ├── unit\
│   ├── integration\
│   ├── replay\
│   └── fixtures\
└── tools\
    └── generate_protocol.py
```

**Firmware Structure:**

```text
firmware\
├── include\
│   ├── ap_protocol_generated.h
│   ├── ap_shared.h
│   └── ap_errors.h
├── src\
│   ├── usb\
│   ├── swd\
│   ├── mock\
│   ├── events\
│   └── platform\
└── tests\
```

**FPGA Structure:**

```text
fpga\
├── rtl\
│   ├── ap_protocol_generated.vh
│   ├── ap_sync_ff.v
│   ├── ap_spi_mock.v
│   ├── ap_logic_analyzer.v
│   └── ap_swd_engine.v
├── bd\
├── sim\
├── constraints\
├── scripts\
│   └── synth.tcl
└── address_map.toml
```

**File Structure Rules:**

- tests 镜像 source/subsystem 结构
- 生成文件只放在约定目录，不混入手写逻辑
- Skill 文件、Schema、协议 SSOT 都属于一等资产，纳入版本控制
- 不允许把跨域契约藏在 README 或注释中

### Format Patterns

**CLI Output Envelope（统一数据源）：**

所有 CLI 命令先构建统一对象，再由 formatter 渲染；不允许为 human/JSON 维护两套独立数据路径。

**Success:**

```json
{
  "status": "ok",
  "command": "mock-load",
  "data": {},
  "timestamp": "2026-04-29T19:00:00Z"
}
```

**Error:**

```json
{
  "status": "error",
  "command": "mock-load",
  "error": {
    "code": "DEVICE_NOT_FOUND",
    "message": "No AgentProbe device detected",
    "detail": "Connect device and retry",
    "recoverable": false
  },
  "timestamp": "2026-04-29T19:00:00Z"
}
```

**Data Exchange Rules:**

- JSON 字段统一 `snake_case`
- 时间戳统一 ISO 8601 UTC
- 布尔值统一 `true/false`
- 错误码统一 `UPPER_SNAKE_CASE`
- 单项返回仍使用 object，不因数量为 1 改成标量

**USB TLV Frame Format:**

```text
| Version (1B) | Type (1B) | Length (2B, LE) | Payload (N bytes) | CRC8 (1B) |
```

- 小端序（Little-Endian）强制统一
- 所有多字节编码必须通过封装函数，不允许直接散落使用 `struct.pack` / 手写位拼接
- `protocol_version` 由 `protocol.toml` 维护

**Formatter Registry:**

- `output.py` / `formatters\` 采用注册表模式
- V1 必须支持：`json`、`human`
- 预留：`csv`、`vcd`

**Mock / Config / Schema Formats:**

- Mock 模型：TOML
- CLI 配置：TOML
- Mock 校验：JSON Schema
- 录制回放：JSONL

### Communication Patterns

**Event Naming Convention:**

事件名统一 `{subsystem}.{object}.{action}`。

**Examples:**
- `spi.transaction.complete`
- `swd.flash.progress`
- `la.trigger.hit`
- `device.connection.lost`

**Daemon RPC Rules:**

- JSON-RPC 方法名统一 `{subsystem}_{action}`
- 所有 RPC 方法第一个参数必须是 `device_id`
- `ap daemon start` 必须幂等；已有实例则复用

**Examples:**
- `mock_load(device_id, ...)`
- `swd_flash(device_id, ...)`
- `device_info(device_id)`

**Internal Communication Boundaries:**

- CLI 不直接访问 USB，只访问 daemon client
- daemon 不直接拼业务 JSON，只返回标准 envelope 或事件对象
- PL 不理解 JSON，仅处理寄存器、流和中断
- 跨域共享常量只能来自生成文件

### Process Patterns

**Protocol-First Development:**

新增跨域功能必须遵循以下顺序：

1. 先修改 `protocol.toml`
2. 生成 Python / C / Verilog 定义文件
3. 再并行实现 CLI、固件、RTL
4. 跑端到端集成验证
5. 最后更新 Skill 契约文件

**SSOT Rules:**

- `protocol.toml` 管理：消息类型、事件类型、错误码、协议版本、跨域常量
- `address_map.toml` 管理：AXI 地址空间分配
- Agent 不得直接编辑任何 `_generated` 文件
- 修改 SSOT 必须触发全域 CI

**Error Handling Patterns:**

- Python 所有用户可见异常都继承 `AgentProbeError`
- 固件对外接口返回 `ap_err_t`
- 错误码定义带 `recoverable` 标记
- 可恢复错误才允许自动重试

**Retry Rules:**

- USB 通信：最多 3 次指数退避
- daemon 连接：最多 5 次线性退避
- SWD 写入/烧录：默认不自动重试，除非错误码明确可恢复

**FreeRTOS Shared Resource Rules:**

- 所有跨任务共享资源必须登记在 `ap_shared.h`
- 每个共享资源必须有对应命名 mutex
- 获取锁必须带超时
- 超时返回 `AP_ERR_BUSY`
- 禁止无限等待锁

**Memory / Safety Rules:**

- 固件禁止 `malloc`
- 固件关键路径使用静态分配或预分配缓冲区
- RTL 禁止 `initial` 初始化业务状态
- 跨时钟域必须使用标准同步模块 `ap_sync_ff`

**Testing Patterns:**

- CLI/daemon 必须同时测试 `json` 与 `human` 输出
- replay 测试是一等测试层级
- daemon 支持 `--replay` 模式，无硬件也可执行集成测试
- 协议生成器本身必须有测试

**Skill Contract Patterns:**

- Skill 文件视为接口契约，不是可有可无文档
- CLI 命令、参数、输出语义变化时必须同步更新 skill
- CI 校验 Skill 中命令清单与 `ap --help` 一致

### Enforcement Guidelines

**All AI Agents MUST:**

- 只能修改 `protocol.toml` / `address_map.toml` 来变更跨域契约
- 新增 CLI 命令时必须支持 `--json`
- 新增 daemon RPC 时必须带 `device_id`
- 新增固件接口时必须返回 `ap_err_t`
- 新增 RTL IP 时必须遵循标准 AXI 控制寄存器布局
- 修改协议后必须同步更新 Skill 契约与 replay fixture

**Pattern Enforcement:**

- Python：Ruff + mypy + pytest
- Firmware：`-Wall -Wextra -Werror` + 静态检查
- FPGA：Verilator lint + Vivado synthesis check
- Cross-domain：SSOT 生成器测试 + generated hash 校验 + Skill/CLI 一致性校验

### Pattern Examples

**Good Examples:**

- `ap mock-load --device-id 2102A --json`
- `mock_load(device_id, model_path)` RPC 签名
- `usb_send_event()` 返回 `ap_err_t`
- `ap_spi_mock` 模块通过 `AXI-Lite CTRL/STATUS/CONFIG/IRQ_*` 暴露寄存器
- `protocol.toml` 中定义 `TYPE_SPI_MOCK_LOAD` 后自动生成三域常量

**Anti-Patterns:**

- 直接编辑 `ap_protocol_generated.h`
- Python 中手写 `struct.pack(">H", length)`
- CLI 直接打开 USB 设备绕过 daemon
- human 输出和 JSON 输出分别维护两套业务逻辑
- 在固件中 `malloc(256)` 创建传输缓冲
- 在 Skill 文件中记录已经废弃的命令签名

## Project Structure & Boundaries

### Complete Project Directory Structure

```text
agentprobe/
├── README.md
├── LICENSE
├── .gitignore
├── .editorconfig
├── Makefile
├── protocol.toml
├── docs/
│   ├── quickstart/
│   │   ├── getting-started.md
│   │   └── first-loop.md
│   ├── protocol/
│   │   ├── tlv-frame.md
│   │   └── event-schema.md
│   ├── hardware/
│   │   ├── som-selection.md
│   │   └── baseboard-constraints.md
│   └── examples/
│       ├── replay-walkthrough.md
│       └── ci-usage.md
├── .github/
│   └── workflows/
│       ├── ci-cli.yml
│       ├── ci-firmware.yml
│       ├── ci-fpga.yml
│       └── ci-protocol-sync.yml
├── scripts/
│   ├── bootstrap.ps1
│   ├── verify-env.ps1
│   ├── package-release.ps1
│   └── export-boot-bin.ps1
├── skills/
│   └── agentprobe.skill.md
├── scenarios/
│   ├── templates/
│   │   ├── blink-hello/
│   │   │   ├── scenario.toml
│   │   │   └── expected-outcome.json
│   │   ├── spi-register-read/
│   │   │   ├── scenario.toml
│   │   │   └── expected-outcome.json
│   │   └── swd-flash-and-probe/
│   │       ├── scenario.toml
│   │       └── expected-outcome.json
│   ├── replay/
│   │   ├── nominal/
│   │   └── failure/
│   └── schemas/
│       ├── scenario.schema.json
│       └── evidence.schema.json
├── cli/
│   ├── pyproject.toml
│   ├── uv.lock
│   ├── README.md
│   ├── src/
│   │   └── agentprobe/
│   │       ├── __init__.py
│   │       ├── __main__.py
│   │       ├── errors.py
│   │       ├── cli/
│   │       │   ├── app.py
│   │       │   ├── options.py
│   │       │   └── commands/
│   │       │       ├── task.py
│   │       │       ├── mock.py
│   │       │       ├── analyze.py
│   │       │       ├── swd.py
│   │       │       ├── scenario.py
│   │       │       ├── report.py
│   │       │       ├── device.py
│   │       │       └── daemon.py
│   │       ├── core/
│   │       │   ├── engine.py
│   │       │   ├── approval.py
│   │       │   ├── diagnosis.py
│   │       │   ├── reporter.py
│   │       │   ├── artifacts.py
│   │       │   ├── support_boundary.py
│   │       │   └── output.py
│   │       ├── daemon/
│   │       │   ├── server.py
│   │       │   ├── rpc.py
│   │       │   ├── usb_transport.py
│   │       │   ├── replay_transport.py
│   │       │   ├── device_registry.py
│   │       │   ├── run_store.py
│   │       │   └── event_bridge.py
│   │       ├── protocol/
│   │       │   ├── frames.py
│   │       │   ├── messages.py
│   │       │   ├── errors.py
│   │       │   ├── constants.py
│   │       │   └── _generated.py
│   │       ├── models/
│   │       │   ├── scenario.py
│   │       │   ├── run.py
│   │       │   ├── evidence.py
│   │       │   ├── outcome.py
│   │       │   └── device.py
│   │       ├── scenario/
│   │       │   ├── loader.py
│   │       │   ├── validator.py
│   │       │   └── templates.py
│   │       └── formatters/
│   │           ├── base.py
│   │           ├── human.py
│   │           └── json.py
│   ├── tests/
│   │   ├── unit/
│   │   ├── integration/
│   │   ├── replay/
│   │   └── fixtures/
│   └── tools/
│       ├── generate_protocol.py
│       └── check_skill_sync.py
├── firmware/
│   ├── CMakeLists.txt
│   ├── README.md
│   ├── include/
│   │   ├── ap_shared.h
│   │   ├── ap_errors.h
│   │   ├── ap_protocol_generated.h
│   │   ├── ap_axi_map_generated.h
│   │   └── ap_config.h
│   ├── src/
│   │   ├── main.c
│   │   ├── usb/
│   │   │   ├── usb_task.c
│   │   │   └── usb_endpoints.c
│   │   ├── protocol/
│   │   │   ├── dispatch.c
│   │   │   └── tlv_decode.c
│   │   ├── swd/
│   │   │   └── cmsis_dap.c
│   │   ├── mock/
│   │   │   └── mock_manager.c
│   │   ├── events/
│   │   │   └── event_task.c
│   │   └── platform/
│   │       ├── axi_regs.c
│   │       ├── interrupts.c
│   │       └── clocks.c
│   ├── freertos/
│   ├── bsp/
│   ├── scripts/
│   │   ├── build.ps1
│   │   └── flash.ps1
│   └── tests/
│       └── host/
├── fpga/
│   ├── Makefile
│   ├── address_map.toml
│   ├── bd/
│   │   ├── system.tcl
│   │   └── ip/
│   ├── rtl/
│   │   ├── include/
│   │   │   └── ap_protocol_generated.vh
│   │   ├── common/
│   │   │   └── ap_sync_ff.v
│   │   ├── top/
│   │   │   └── ap_top.v
│   │   ├── io/
│   │   │   └── ap_io_router.v
│   │   ├── mock/
│   │   │   └── ap_spi_mock.v
│   │   ├── analyze/
│   │   │   └── ap_logic_analyzer.v
│   │   ├── debug/
│   │   │   └── ap_swd_engine.v
│   │   └── stream/
│   │       └── ap_event_fifo.v
│   ├── sim/
│   │   ├── tb_spi_mock.sv
│   │   ├── tb_logic_analyzer.sv
│   │   └── tb_event_fifo.sv
│   ├── constraints/
│   │   ├── baseboard.xdc
│   │   └── som.xdc
│   └── scripts/
│       ├── synth.tcl
│       ├── impl.tcl
│       └── export-bitstream.tcl
└── hardware/
    ├── som-baseboard/
    │   ├── kicad/
    │   ├── pinout.csv
    │   ├── bom.csv
    │   └── docs/
    ├── fixtures/
    │   ├── cables/
    │   └── adapters/
    └── mechanical/
        └── enclosure/
```

### Architectural Boundaries

**API Boundaries:**

- `cli\src\agentprobe\cli\commands\` 只负责命令行入口、参数绑定与输出选择；命令实现不得直接触碰 USB 或硬件状态。
- `cli\src\agentprobe\daemon\rpc.py` 定义 CLI ↔ daemon 的唯一调用边界；所有 RPC 入口必须显式携带 `device_id`。
- `cli\src\agentprobe\protocol\` 是 PC 侧 TLV/事件契约层；消息类型、错误码和版本号只能来自 `protocol.toml` 生成结果。
- `firmware\src\protocol\` 是设备侧命令解码边界；负责把 USB TLV 映射为 PS 内部动作，不承载业务决策。
- `fpga\rtl\` 暴露的对 PS 边界仅限 AXI-Lite 寄存器、AXI-Stream 数据流和中断线；PL 内部模块不得直接知道 JSON-RPC 或 CLI 语义。

**Component Boundaries:**

- CLI 表现层（`cli\cli\`）与任务编排层（`cli\core\`）分离，避免 human 输出逻辑渗入任务状态机。
- daemon 传输层（`usb_transport.py` / `replay_transport.py`）与 run/evidence 管理（`run_store.py` / `event_bridge.py`）分离，保证真实硬件和回放模式共享同一上层行为。
- 固件中 USB、事件、Mock、SWD 四类任务各自独立，协作仅通过 `ap_shared.h` 中登记的共享资源和明确的队列/中断。
- FPGA 以 `common`、`io`、`mock`、`analyze`、`debug`、`stream` 分域，所有跨时钟域交互必须经 `ap_sync_ff` 或 FIFO。
- `scenarios\` 作为可版本化验证资产，与 `docs\` 说明文档分离；场景定义不是 prose，而是可执行输入。

**Service Boundaries:**

- daemon 独占设备连接、设备发现、会话生命周期与事件采集；CLI 不得绕过 daemon 直连设备。
- `core\engine.py` 负责闭环任务推进、状态迁移、审批点停等和终态生成；它不负责具体 USB/AXI 通信细节。
- `core\diagnosis.py` 与 `core\reporter.py` 分离：前者输出结构化诊断与下一步建议，后者负责组合证据、结论和工件引用。
- 固件 USB Task 是设备侧对外服务入口；SWD/Event/Mock 作为内部服务供 USB Task 编排调用。
- PL 中 `ap_io_router` 是所有引脚路由的唯一汇聚点；协议模拟、逻辑分析、调试引擎都不能私自占用物理引脚。

**Data Boundaries:**

- `protocol.toml` 管理消息类型、事件类型、错误码、协议版本和共享常量；`fpga\address_map.toml` 管理 AXI 地址空间，二者是唯一跨域 SSOT。
- `_generated` 文件只允许由 `cli\tools\generate_protocol.py` 生成；任何手工编辑都视为架构违规。
- 运行期证据采用 JSONL 事件流 + 结构化终态结果；人类可读报告必须由相同的统一对象渲染。
- 场景模板、回放数据、Schema 分别位于 `scenarios\templates\`、`scenarios\replay\`、`scenarios\schemas\`，防止示例、测试和规范混杂。
- 硬件设计资产与软件构建产物严格分离：`hardware\` 只存设计源文件，不存临时导出物。

### Requirements to Structure Mapping

**Feature / FR Category Mapping:**

- **Closed-Loop Task Execution（FR1-FR8）**  
  落在 `cli\src\agentprobe\core\engine.py`、`cli\src\agentprobe\cli\commands\task.py`、`cli\src\agentprobe\daemon\server.py`、`firmware\src\protocol\`、`fpga\bd\` / `fpga\rtl\top\`。
- **Observation, Evidence & Reporting（FR9-FR15）**  
  落在 `cli\src\agentprobe\core\artifacts.py`、`reporter.py`、`formatters\`、`daemon\event_bridge.py`、`daemon\run_store.py`、`firmware\src\events\`、`fpga\rtl\stream\`、`fpga\rtl\analyze\`。
- **Diagnosis, Escalation & Safety Governance（FR16-FR24）**  
  落在 `cli\src\agentprobe\core\diagnosis.py`、`approval.py`、`support_boundary.py`、`models\outcome.py`、`skills\agentprobe.skill.md`、`hardware\som-baseboard\docs\`。
- **Validation Scenario Design, Templates & Reproducibility（FR25-FR34）**  
  落在 `scenarios\templates\`、`scenarios\replay\`、`scenarios\schemas\`、`cli\src\agentprobe\scenario\`、`cli\tests\replay\`。
- **Review, Collaboration & Workflow Integration（FR35-FR46）**  
  落在 `cli\src\agentprobe\cli\commands\report.py`、`device.py`、`scenario.py`、`daemon\run_store.py`、`docs\examples\`。
- **Developer Access & Adoption（FR47-FR53）**  
  落在 `cli\src\agentprobe\cli\app.py`、`skills\agentprobe.skill.md`、`docs\quickstart\`、`scripts\bootstrap.ps1`、`.github\workflows\`。

**Cross-Cutting Concerns:**

- **协议一致性**：`protocol.toml`、`fpga\address_map.toml`、`cli\tools\generate_protocol.py`、`ci-protocol-sync.yml`
- **结构化输出一致性**：`cli\src\agentprobe\core\output.py`、`cli\src\agentprobe\formatters\`
- **证据可追溯性**：`cli\src\agentprobe\daemon\run_store.py`、`core\artifacts.py`、`scenarios\replay\`
- **高风险动作治理**：`core\approval.py`、`core\support_boundary.py`、`skills\agentprobe.skill.md`
- **硬件可重复验证**：`scenarios\templates\`、`cli\tests\replay\`、`hardware\fixtures\`

### Integration Points

**Internal Communication:**

- CLI 通过 JSON-RPC 调用 daemon；daemon 负责把 RPC 请求转换为 USB TLV 命令或 replay 流。
- daemon 以统一事件桥接器把实时设备事件和回放事件标准化为 JSONL，再交给 `core` 层和 formatter。
- 固件通过 AXI-Lite 配置 PL、通过 AXI-Stream DMA 读取高速事件和采样数据、通过中断接收触发通知。
- `generate_protocol.py` 同时产出 Python/C/Verilog 生成文件，使 CLI、固件、RTL 在编译前即对齐常量与版本。

**External Integrations:**

- Claude Code / OpenCode 通过 `skills\agentprobe.skill.md` + `ap --json` 进入系统。
- OpenOCD / pyOCD 使用 CMSIS-DAP v2 接入，由 `firmware\src\swd\cmsis_dap.c` 和 `fpga\rtl\debug\ap_swd_engine.v` 支撑。
- GitHub Actions 通过 `.github\workflows\` 执行 CLI、固件、FPGA、协议同步检查。
- Vivado / arm-none-eabi-gcc / uv 分别服务 PL、PS、CLI 构建域，由 `scripts\` 和各子域构建文件编排。

**Data Flow:**

1. `scenarios\templates\` 中的场景与项目上下文由 CLI 载入并校验。
2. `core\engine.py` 将任务转换为 daemon RPC，并为本次运行创建 run identity。
3. daemon 通过 USB TLV 或 replay 驱动设备/仿真执行。
4. 固件协调 PS 任务并通过 AXI 与 PL 模块交互；PL 产生事件、采样结果和状态变更。
5. daemon 收集 JSONL 证据流，`core\reporter.py` 生成统一对象，再由 formatter 输出 human/JSON 结果。

### File Organization Patterns

**Configuration Files:**

- 仓库级配置放根目录（`Makefile`、`.editorconfig`、`protocol.toml`）。
- Python 构建配置只放 `cli\pyproject.toml`，不污染固件/FPGA 域。
- FPGA 时序与综合配置集中在 `fpga\constraints\` 和 `fpga\scripts\`。
- 硬件约束、引脚与 BOM 放在 `hardware\som-baseboard\`，避免散落到文档目录。

**Source Organization:**

- CLI 代码按 `cli` / `core` / `daemon` / `protocol` / `models` / `scenario` / `formatters` 分层，禁止跨层捷径调用。
- 固件按任务职责分目录，公共接口统一进 `include\`。
- RTL 按功能分域，顶层连接只存在于 `fpga\rtl\top\ap_top.v`。

**Test Organization:**

- Python 单元测试、集成测试、回放测试分目录存放，并与源代码分层镜像。
- 固件 host 侧测试放 `firmware\tests\host\`，避免与设备特定 BSP 代码耦合。
- FPGA 仿真测试统一放 `fpga\sim\`，每个关键 IP 至少对应一个 testbench。

**Asset Organization:**

- 场景模板、回放素材、Schema 统一归属 `scenarios\`。
- Skill 契约放 `skills\`，不是 `docs\` 的附属说明。
- 夹具、线缆、转接器等实验台资产文档归属 `hardware\fixtures\`，与 PCB 设计资产并列管理。

### Development Workflow Integration

**Development Server Structure:**

- `ap daemon start` 启动本地常驻服务，对应 `cli\src\agentprobe\daemon\server.py`。
- `--replay` 模式通过 `replay_transport.py` 复用同一服务边界，使无硬件开发与真实设备开发保持同构。
- CLI 的开发入口始终是 `cli\src\agentprobe\cli\app.py`，Skill 与文档都以该入口为准。

**Build Process Structure:**

- `cli\tools\generate_protocol.py` 是所有跨域构建前置步骤。
- 顶层 `Makefile` 负责串联 `make cli`、`make fw`、`make fpga`、`make all`，但不隐藏子域原生命令。
- `.github\workflows\ci-protocol-sync.yml` 强制检查 SSOT 变更、生成文件漂移和 Skill/CLI 一致性。

**Deployment Structure:**

- CLI 产物是 Python wheel；固件与 bitstream 组合为 Zynq 启动镜像；硬件产物是 SoM 底板设计包。
- 发布流程通过 `scripts\package-release.ps1` 和 `export-boot-bin.ps1` 组装版本化产物。
- `docs\quickstart\first-loop.md` 对应 V1 的单条可信闭环，用作实现验收和对外 onboarding 基线。

## Architecture Validation Results

### Coherence Validation ✅

**Decision Compatibility:**

- Zynq-7020 SoC、FreeRTOS on PS、Vivado PL、Python CLI + daemon、SSOT 协议生成链路彼此兼容。
- V1 的 CLI-first、本地 daemon、USB TLV、AXI-Lite / AXI-Stream 分层能够共同支撑 two-board self-hosting 可信闭环目标。
- 技术选型之间不存在阻塞级冲突；剩余风险集中在闭合决策和实施顺序，而不是架构矛盾。

**Pattern Consistency:**

- 命名、结构、通信、流程规则与技术选型一致，没有自相矛盾的实现约束。
- `protocol.toml` / `address_map.toml` 作为跨域 SSOT，与 `_generated` 文件规则、Skill 同步规则、CI 校验规则相互一致。
- human / JSON 单路径输出、daemon 独占设备访问、固件 `ap_err_t`、RTL AXI 边界定义具备端到端一致性。

**Structure Alignment:**

- Step 6 定义的目录结构能够承接 Step 4/5 中的协议优先、daemon 边界、AXI 边界、formatter 注册表和 replay 测试策略。
- `cli\`、`firmware\`、`fpga\`、`hardware\`、`scenarios\`、`skills\` 的责任边界清晰，适合 AI agents 并行开发。
- 项目结构已经把契约、实现、测试、验证资产和硬件设计资产分离，降低了跨域耦合。

### Requirements Coverage Validation ✅

**Epic / Feature Coverage:**

- PRD 中功能需求均已获得架构支撑：闭环执行、self-hosting device identity、证据与报告、诊断与升级、安全治理、场景与复现、协作与集成、开发者接入。
- 所有关键用户路径均能映射到 CLI、daemon、PS 固件、PL 模块、场景资产和文档资产中的明确位置。

**Functional Requirements Coverage:**

- FR1-FR8：由 `core\engine.py`、CLI 命令层、daemon 服务、PS/PL 控制路径承接。
- FR9-FR15：由事件流、evidence store、reporter、formatter、run store 和 replay 资产承接。
- FR16-FR24c：由 diagnosis、approval、support boundary、device registry/topology、structured outcomes 和 Skill 契约承接。
- FR25-FR34：由 `scenarios\templates\`、`scenarios\replay\`、Schema、validator、fixtures 承接。
- FR35-FR46：由报告、run history、approval wait、handoff 语义和共享资产状态承接。
- FR47-FR53：由 CLI 入口、quickstart、Skill、环境校验脚本与非交互 JSON 模式承接。

**Non-Functional Requirements Coverage:**

- NFR1-NFR5（可靠性）：由显式终态、run identity、evidence persistence、replay 和诊断语义承接。
- NFR6-NFR10（安全）：由 approval gate、support boundary、blacklisted action 治理和审计记录承接。
- NFR11-NFR13（安全/本地性）：由本地 daemon、本地证据优先、版本化资产与 provenance 要求承接。
- NFR14（性能）：由 daemon / firmware 事件流、进度事件与 heartbeat 语义承接。
- NFR15-NFR23c（互操作与 self-hosting 安全）：由 schema/version 标识、稳定终态 taxonomy、artifact references、human/json 单语义、device identity 和 topology enforcement 承接。

### Implementation Readiness Validation ✅

**Decision Completeness:**

- 核心硬件、软件、协议、IPC、事件格式、测试与 CI 约束都已经有明确架构决策。
- 关键实现顺序已经被定义为 contract/replay-first，再进入 single-board loop 和 two-board self-hosting，而不是各子域自由推进。

**Structure Completeness:**

- 项目结构具体到目录和代表性文件级别，足以指导实现代理按边界拆分工作。
- 内外部集成点、数据流、构建与发布结构已经明确，不再停留在抽象描述层。

**Pattern Completeness:**

- 关键冲突点已被命名并配套规则：命名、输出、协议、重试、共享资源、生成文件、Skill 同步、回放测试、Golden/DUT identity。
- 尚未落地的是少数“闭合闸门”，不是架构缺席。

### Gap Analysis Results

**Critical Gaps:**

1. **SoM SKU 尚未最终冻结**  
   已通过 **ADR-6: V1 SoM Contract-First Closure** 收敛：先冻结 minimum contract，再在合同范围内选最终 SKU。
2. **SSOT 仍停留在架构定义层**  
   已通过 **ADR-7: Protocol Generator Before Feature Parallelization** 收敛：先实现 `protocol.toml` + `address_map.toml` + generator + generated-hash enforcement，再允许跨域并行开发。

**Important Gaps:**

3. **Replay fixture 缺少 canonical contract**  
   已通过 **ADR-8: Replay Fixture as Contract Asset** 收敛：fixture 必须绑定 scenario id、protocol_version、schema_version、expected terminal state、artifact references。
4. **版本兼容矩阵尚未显式发布**  
    需要补充 protocol version、CLI schema version、Skill contract version、firmware / bitstream compatibility window 的统一说明。
5. **Self-hosting topology schema 尚未落地**  
   需要补充 device role、serial、firmware/bitstream version、connection_topology_id、allowed state-changing actions 的 schema 与校验规则。

**Nice-to-Have Gaps:**

- 增补 SoM 供应商比较文档与采购替代策略
- 增补 two-board self-hosting 可信闭环的 reference implementation walkthrough
- 增补 replay fixture 编写指南与 CI 命名规范

### Validation Issues Addressed

- 原本“未决 SoM SKU”已从模糊风险转为 **implementation gate**。
- 原本“SSOT / replay / versioning 仍是理念”已被转化为三条验证驱动的闭合决策（ADR-6 / ADR-7 / ADR-8）。
- Step 7 现在不只验证架构合理，还明确了**实现前必须先闭合的闸门**，从而降低多代理实现时的分叉概率。

### Architecture Completeness Checklist

**✅ Requirements Analysis**

- [x] Project context thoroughly analyzed
- [x] Scale and complexity assessed
- [x] Technical constraints identified
- [x] Cross-cutting concerns mapped

**✅ Architectural Decisions**

- [x] Critical decisions documented with versions
- [x] Technology stack fully specified
- [x] Integration patterns defined
- [x] Performance considerations addressed

**✅ Implementation Patterns**

- [x] Naming conventions established
- [x] Structure patterns defined
- [x] Communication patterns specified
- [x] Process patterns documented

**✅ Project Structure**

- [x] Complete directory structure defined
- [x] Component boundaries established
- [x] Integration points mapped
- [x] Requirements to structure mapping complete

### Architecture Readiness Assessment

**Overall Status:** READY FOR IMPLEMENTATION WITH CLOSURE GATES

**Confidence Level:** Medium-High

**Key Strengths:**

- 技术栈与边界清晰，适合 monorepo + 多代理并行实现
- 协议、输出、事件、回放、Skill 契约之间的统一性较强
- V1 范围被控制在可验证的 two-board self-hosting 可信闭环上，没有失控扩张

**Areas for Future Enhancement:**

- 最终 SoM SKU 与底板器件清单收敛
- protocol generator / replay fixture / version matrix 的落地实现
- 基于 two-board self-hosting 可信闭环的 reference implementation 与 CI 基线

### Architecture Change Log

| 版本 | 日期 | 变更摘要 |
|------|------|----------|
| v1.4 | 2026-05-07 | Claude review 补强：V2 ITM/DWT 内部观测路径、Evidence Envelope、Skill capability boundary 对应实现要求、V3 推理瓶颈阶段切换条件 |

### Implementation Handoff

**AI Agent Guidelines:**

- Follow all architectural decisions exactly as documented
- Use implementation patterns consistently across all components
- Respect project structure and boundaries
- Refer to this document for all architectural questions

**First Implementation Priority:**

1. Freeze V1 SoM minimum contract
2. Implement protocol generator + generated hash enforcement
3. Define canonical replay fixture contract
4. Publish version compatibility matrix
