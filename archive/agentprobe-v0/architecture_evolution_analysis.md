
# AgentProbe 架构演化分析

## 从"当前 V1"到"未来大型 Agent 系统"的架构设计

---

## 一、你的核心问题

1. **架构不直观** → 已为你生成 5 张架构图（见下方文件）
2. **FPGA 选型是否支持演化** → 见下方详细分析
3. **当前设计能否融入未来大型 Agent 基础设施** → 结论：**可以，但需要现在就做对几件事**

---

## 二、5 张架构图说明

| 图 | 文件名 | 回答什么问题 |
|----|--------|-----------|
| 1 | `architecture_block_diagram.png` | 系统总体结构：谁连谁，怎么连 |
| 2 | `data_flow_diagram.png` | 数据从哪来到哪去：控制流 + 观测流 + 闭环 |
| 3 | `evolution_architecture.png` | V1 → V2 → Future：哪些东西不变，哪些会换 |
| 4 | `fpga_internal_architecture.png` | Zynq 内部：PS/PL 分工、AXI 互联、资源余量 |
| 5 | `software_layer_architecture.png` | 软件分层：哪层是 HW-Independent，哪层需要硬件 |

---

## 三、从演化角度的架构评估

### 3.1 当前设计的"演化友好"部分 ✅

你的 architecture.md 中有几个设计决策**天然支持演化**：

| 设计决策 | 为什么支持演化 |
|---------|-----------|
| **AXI 标准总线** | PL 模块可独立升级、替换、新增，不影响 PS 代码 |
| **参数化 FPGA 设计** | Mock 行为变更 = 寄存器写入（μs），不需重综合 |
| **USB 复合设备** | 新 endpoint 可加入不影响已有通道 |
| **CLI + JSON contract** | Agent 接口稳定，底层硬件怎么换 Agent 不感知 |
| **protocol.toml SSOT** | 跨域常量统一管理，升级只改一处 |
| **Replay Transport** | 不依赖真实硬件就能测试上层逻辑 |
| **FPGA 仅用 20% LUT** | 80% 空间留给 V2/V3 新协议和功能 |

### 3.2 当前设计的"演化风险"部分 ⚠️

| 风险 | 问题描述 | 影响 |
|------|---------|------|
| **单板限制** | V1 = 单块 Zynq SoM，未来如果需要多板/远程怎么办？ | 如果 daemon 和板绑定太紧，扩展到多设备/远程会很痛 |
| **USB 带宽天花板** | USB 2.0 HS = ~40MB/s，16ch@100MHz 原始数据 = 200MB/s | V2 如果要更多通道/更高速率，USB 会成瓶颈 |
| **localhost-only daemon** | 当前 daemon 只监听 127.0.0.1:4729 | 未来如果要远程实验台 (Remote Lab)，需要重新设计 |
| **单一 Agent 假设** | 当前设计假设只有一个 Agent 实例使用设备 | 多 Agent 协作时（如一个写代码一个跑验证），缺少并发控制 |
| **Vivado 闭源工具链** | 锁定 Xilinx 生态 | 如果未来要量产或开源社区，可能需要考虑替代方案 |

### 3.3 演化评估结论

> **当前架构 80% 是演化友好的。**
> 关键在于：你现在不需要实现未来的功能，但需要**保护几个 contract 不被破坏**。

---

## 四、面向未来大型 Agent 系统的演化设计建议

### 4.1 你的未来愿景理解

```
未来目标：
  一个大型 Agent 系统
  ├─ 能直接连接多种嵌入式硬件
  ├─ Agent-native 开发（不是辅助工具，而是基础设施）
  ├─ 多 Agent 协作（写代码、验证、诊断、报告 各有 Agent）
  ├─ 可能远程访问（Remote Lab）
  └─ 可能支持多种 FPGA / 多种 MCU 家族
```

### 4.2 架构分层演化策略

```
┌─────────────────────────────────────────────────────────┐
│  Layer A: Agent Contract (从 V1 开始稳定，永不破坏)       │
│  ├── Terminal State Schema                               │
│  ├── Evidence Package Schema                             │
│  ├── Diagnosis Taxonomy                                  │
│  ├── Escalation Protocol                                 │
│  └── Skill File Format                                   │
├─────────────────────────────────────────────────────────┤
│  Layer B: Orchestration (V2 引入，V1 预留接口)           │
│  ├── Multi-Device Session Manager                        │
│  ├── Multi-Agent Coordination                            │
│  ├── Remote Lab Gateway                                  │
│  └── Job Queue / Priority Scheduler                      │
├─────────────────────────────────────────────────────────┤
│  Layer C: Device Abstraction (V1 CLI+Daemon, V2 扩展)    │
│  ├── Device Discovery Protocol                           │
│  ├── Universal Transport Interface                       │
│  ├── Capability Declaration                              │
│  └── Health Check / Topology Validator                   │
├─────────────────────────────────────────────────────────┤
│  Layer D: Hardware Implementation (可替换的)             │
│  ├── Zynq-7020 (V1)                                     │
│  ├── Zynq UltraScale+ (V3)                              │
│  ├── Custom ASIC (V5)                                    │
│  └── Cloud FPGA (V5+)                                    │
└─────────────────────────────────────────────────────────┘
```

**核心原则：Layer A 永不破坏，Layer D 随时可换。**

### 4.3 V1 中必须"现在就做对"的 5 件事

这些决定了未来能否平滑演化：

#### ① Evidence Schema 必须版本化

```json
{
  "schema_version": "1.0.0",
  "run_id": "...",
  "evidence": {...},
  "verdict": "...",
  "source_device": {
    "type": "agentprobe-zynq7020",
    "serial": "...",
    "firmware_version": "..."
  }
}
```

**为什么：** 未来可能有不同硬件产出证据。Schema 版本化让消费者（Agent/工程师）能处理不同来源。

#### ② Device Identity 必须是 first-class concept

```toml
[device]
id = "ap-001"
type = "agentprobe"
hardware_version = "zynq7020-som-v1"
firmware_version = "0.1.0"
capabilities = ["spi_mock", "i2c_mock_v2", "analyzer_8ch", "swd"]
supported_targets = ["stm32_m3", "stm32_m4", "stm32_m33"]
```

**为什么：** 未来多板/多设备时，Agent 需要知道"哪个设备能做什么"。V1 只有一块板，但 identity 机制必须存在。

#### ③ Transport Layer 必须抽象化

```python
class Transport(ABC):
    @abstractmethod
    async def send_command(self, cmd: Command) -> Response: ...
    @abstractmethod
    async def receive_events(self) -> AsyncIterator[Event]: ...

class USBTransport(Transport): ...        # V1: 本地 USB
class ReplayTransport(Transport): ...     # V1: 文件回放
class RemoteTransport(Transport): ...     # V3: 远程实验台
class CloudFPGATransport(Transport): ...  # V5: 云 FPGA
```

**为什么：** Agent 调用的是 Transport 接口，不是 USB 细节。未来换成远程或云 FPGA，Agent 代码 0 改。

#### ④ Daemon 必须支持"设备列表"而不是"单设备"

```python
# V1 实际只有一个设备，但 API 设计必须是列表
devices = daemon.list_devices()
# [{"id": "ap-001", "type": "agentprobe", "status": "connected"}]

# 不要设计成：
device = daemon.get_device()  # ❌ 单数形式，未来改不了
```

**为什么：** V2 的 Two-Board Rig 就需要两个设备。如果 V1 的 API 是单数形式，V2 就要 breaking change。

#### ⑤ Skill File 必须声明 capability boundary

```markdown
# agentprobe.skill.md

## Capabilities (V1)
- spi_mock: SPI protocol mock with register table
- analyzer_8ch: 8-channel logic analyzer @100MHz
- swd_flash: Flash STM32 via SWD/CMSIS-DAP
- uart_bridge: UART passthrough

## Not Supported (V1)
- i2c_mock: planned for V2
- can_mock: planned for V2
- fault_injection: planned for V2
- remote_access: planned for V3

## Device Requirements
- hardware: agentprobe-zynq7020-som-v1
- firmware: >=0.1.0
```

**为什么：** Agent 根据 Skill File 决定能做什么。V2 增加新能力时，只需更新 Skill File，Agent 自动发现新能力。

---

## 五、FPGA 选型的演化分析

### 5.1 Zynq-7020 的演化潜力

| 维度 | V1 现在 | V2 可做 | 极限 |
|------|---------|---------|------|
| LUT | 17K/85K (20%) | +I2C+CAN+Fault = ~40K (47%) | ~70K (82%) |
| BRAM | 少量 FIFO | 深度波形缓存 | 630KB |
| DSP | 未使用 | 信号处理/FFT | 220 个 |
| CPU | CPU0 only | CPU0+CPU1 AMP | 2x A9 |
| 带宽 | USB 2.0 (~40MB/s) | 压缩+触发优化 | **天花板** |

### 5.2 FPGA 演化路径建议

```
Phase 1 (Now):  Zynq-7020 SoM
                ├── 够用，成本低，验证快
                └── 不需要自研 PCB

Phase 2 (6-12mo): Zynq-7020 自研 Baseboard
                ├── SoM 不变，Baseboard 优化接口
                └── 增加模拟前端、更多 I/O

Phase 3 (12-18mo): 评估是否需要升级 SoC
                ├── 如果 USB 带宽够 → 继续 Zynq-7020
                ├── 如果需要更多通道 → Zynq-7045 (350K LUT)
                └── 如果需要 USB 3.0 → Zynq UltraScale+ (MPSoC)

Phase 4 (18+mo): 根据实际需求决定
                ├── 高端版：UltraScale+ (大通道数/高速率)
                ├── 量产版：自研 ASIC (降成本)
                └── 云端版：AWS F1 / Azure NP (远程实验台)
```

### 5.3 关键决策：现在不需要做，但需要保护的

| 设计决策 | V1 做法 | 保护措施 |
|---------|---------|---------|
| AXI 地址空间 | 给每个 IP block 分配地址范围 | 预留足够的地址空间 gap，V2 新模块可以插入中间 |
| Bitstream 版本 | V1 固定一个 bitstream | 在 device identity 中声明 bitstream 版本，未来可热切换 |
| 中断分配 | V1 用少量中断 | 预留中断号给未来模块 |
| DMA 通道 | V1 用 1-2 个 | 预留 DMA 通道给未来高速流 |

---

## 六、面向"大型 Agent 系统"的接口设计

### 6.1 当前 CLI-only 接口 vs 未来多接口

```
V1 (Now):
  Agent → ap CLI --json → Daemon → USB → Zynq

V2 (6-12 mo):
  Agent → MCP Server → Daemon → USB → Zynq
  Agent → ap CLI --json → Daemon → USB → Zynq  (向后兼容)

V3 (18+ mo):
  Agent → MCP Server → Orchestrator → [多个 Daemon] → [多个设备]
  Agent → REST API → Orchestrator → Remote Lab → [远程设备]
  Agent → ap CLI --json → Local Daemon → USB → [本地设备]
```

### 6.2 演化关键：Daemon 是 pivot point

```
V1 Daemon (minimal):
  ├── 单设备连接
  ├── JSON-RPC on localhost
  ├── USB transport
  └── Event bridge

V2 Daemon (扩展):
  ├── 多设备连接 (list_devices)
  ├── Session orchestration (golden + dut)
  ├── Event routing (per device)
  └── 仍然是 localhost

V3 Daemon → Orchestrator (升级):
  ├── 远程设备发现
  ├── Multi-Agent 并发控制
  ├── Job queue + priority
  ├── 可部署为 service
  └── API: MCP + REST + WebSocket + CLI
```

**设计建议：V1 的 Daemon 从第一天就应该用 `device_id` 参数来寻址操作，即使只有一个设备。** 这一个小决策避免了未来巨大的 breaking change。

---

## 七、总结：演化设计的三条原则

### 原则 1: Contract 稳定，Implementation 可换

```
稳定的：                    可换的：
├── Evidence Schema         ├── FPGA 型号
├── Terminal State Enum     ├── USB vs 远程
├── Diagnosis Taxonomy      ├── 单板 vs 多板
├── Escalation Protocol     ├── 本地 vs 云
└── Skill File Format       └── Zynq vs UltraScale
```

### 原则 2: 接口预留未来，实现只做当前

```
V1 接口：daemon.list_devices() → 返回 1 个设备
V1 实现：只处理 1 个 USB 连接
─── 接口预留了"多设备"，实现只做了"单设备" ───
V2 时：实现改为处理 N 个连接，接口不变
```

### 原则 3: 每一层都有明确的"替换边界"

```
如果替换 FPGA  → 只改 Layer D (Hardware)
如果加远程    → 只改 Layer C (Transport)
如果加 MCP    → 只改 Layer B (Orchestration)
如果换 Agent  → Layer A (Contract) 不变

没有哪一层的变更会 cascade 到所有层。
```

---

## 八、给你的具体建议

### 现在就做（V1 scope 内）：

1. ✅ Evidence Schema 加 `schema_version` 字段
2. ✅ Device Identity 作为 first-class 概念（即使只有一个设备）
3. ✅ Daemon API 用 `device_id` 参数（即使只有一个值）
4. ✅ Transport 抽象为接口（USB + Replay + Mock 三种实现）
5. ✅ Skill File 声明 capability boundary（支持/不支持/计划中）
6. ✅ FPGA 地址空间预留 gap
7. ✅ protocol.toml 加 version 字段

### 不要做（留给 V2/V3）：

1. ❌ 不要现在实现 MCP Server
2. ❌ 不要现在实现 Remote Lab
3. ❌ 不要现在实现 Multi-Agent Coordination
4. ❌ 不要现在换 FPGA（Zynq-7020 够用）
5. ❌ 不要现在做 USB 3.0（USB 2.0 V1 够用）

### 记住：

> **做对 Contract，做小 Implementation，留够空间。**
> 
> 未来的大型 Agent 系统不是重写，而是在稳定 Contract 上持续扩展。

---

## 九、回答你的核心疑问

### Q: 当前设计能否融入未来的大型 Agent 架构？

**A: 能。但前提是把上面 7 件"现在就做"的事情做好。**

原因：
- 你的 Contract Layer（Evidence/Terminal State/Diagnosis）是 Agent 真正依赖的东西
- 硬件可以升级、替换、扩展，但 Contract 必须从 V1 开始就稳定
- 未来"大型 Agent 系统"本质上是在 Contract 之上叠加：Orchestrator + Remote + Multi-Agent
- 这些高层能力不需要改底层 Contract，只需要在中间加 Layer

### Q: FPGA 选型是否正确？

**A: Zynq-7020 作为 V1 是正确的。**

原因：
- 85K LUT，V1 只用 20%，有 4x 余量给 V2
- SoM 形态加速验证，不需要自研 PCB
- 如果未来发现不够，升级到 Zynq-7045 或 UltraScale+ 时，PS 代码和 CLI/Daemon 代码几乎不改（因为 Transport 抽象了）
- 最大的限制是 USB 2.0 带宽，但 V1/V2 的场景（8-16ch@100MHz + 触发压缩）远够用

### Q: 架构不直观怎么办？

**A: 用这 5 张图替代纯文字。建议在 architecture.md 中嵌入这些图的引用。**

---

Generated: 2026-05-06
