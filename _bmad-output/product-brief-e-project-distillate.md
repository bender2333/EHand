---
title: "Product Brief Distillate: E-Project"
type: llm-distillate
source: "product-brief-e-project.md"
created: "2026-04-21"
purpose: "Token-efficient context for downstream PRD creation"
---

# E-Project Detail Pack

## 验证通道技术细节

- **GPIO 物理监测**：FPGA 实时采集目标芯片 IO 电平，功能类似"IO 万用表"；Agent 可设定预期电平并自动比对
- **SWD 内存/寄存器读取**：通过调试接口直接读取目标芯片的寄存器值和 RAM 变量，无需目标芯片运行任何探针代码
- **UART 从机模拟**：FPGA 实现 UART slave，接收目标芯片串口输出并校验内容；也可主动发送数据模拟外部设备
- **逻辑分析仪**：FPGA 精确时序采集，支持协议级解码（UART 帧结构、起止位、波特率匹配）
- Agent 综合多通道数据做交叉验证，而非依赖单一来源

## 竞品详细数据

| 产品 | 关键数据 | 弱点（相对 E-Project） |
|------|---------|----------------------|
| J-Link (SEGGER) | 市场标杆，Pro 下载速度 4MB/s，支持 RTT/VCOM，20+年品牌 | 纯人工操作，无 API 驱动闭环，EDU Mini ~$20 但功能有限 |
| Saleae Logic | Pro 最高 500MHz 采样，桌面软件体验好 | 纯采集工具，不参与开发流程，Logic Pro ~$1000 |
| Bus Pirate 5 | 开源多协议工具，活跃社区，~$40 | 手动命令行操作，无自动化 |
| ESP32-Bus-Pirate | GitHub 3078 star，Web CLI，支持 UART/I2C/SPI/JTAG/CAN | 基于 ESP32 性能有限，无调试器功能 |
| OpenOCD | 开源调试器，可脚本化，GitHub 2167 star | 无信号采集，无协议模拟，配置复杂 |
| sigrok/DSView | 开源逻辑分析+协议解码，DSView 1364 star | 采集工具，不参与开发，UI 陈旧 |

## 审核关键建议（按优先级）

### P0 — 必须在 PRD 阶段解决
- **定价策略**：BOM 成本估算 + 目标售价区间 + LLM 调用成本分摊模型；用户心理锚点：J-Link EDU ~$20 + Saleae ~$400 + Bus Pirate ~$40 ≈ $460 总和
- **AI 嵌入式代码能力预验证**：在硬件设计前，用现有工具（J-Link + OpenOCD + arm-gcc + LLM API）手动跑完一次闭环，验证 AI 对 STM32 寄存器级代码的生成能力边界
- **SWD 兼容性适配计划**：STM32 M3（如 F103）、M4（如 F407）、M33（如 L5/U5）的 Flash 编程算法和 SWD 时序有差异，需逐系列适配
- **安全护栏完整设计**：GPIO 过流保护策略、Flash 保护区域访问控制、ESD 防护、异常配置检测

### P1 — 强烈建议
- **商业模式选型**：硬件毛利 + Agent 订阅双轨？硬件开源获信任 + Agent 闭源保壁垒？LLM API 成本转嫁还是包含？
- **开放策略承诺**：板卡通信协议文档化、采集数据支持 VCD/CSV/sigrok 格式导出、Agent 生成代码无专有依赖
- **Docker 化环境**：arm-gcc + Agent 预装容器，消灭工具链配置地狱
- **"纯硬件模式"独立价值**：即使不用 Agent，板卡也能作为独立调试器+逻辑分析仪+协议工具使用

### P2 — 值得考虑
- **教育市场 GTM**：与高校嵌入式课程合作，院校采购，建立早期用户心智
- **芯片原厂合作**：ST 生态（Nucleo 定位）、Espressif（ESP32 社区，Maker 属性）
- **HIL 测试平台化**：仅 SWD + FPGA 采集 + 自动 Pass/Fail 已是独立 HIL 方案，对比 dSPACE/NI 有巨大成本优势
- **数据飞轮**：Agent 迭代产生的"代码模式 → 硬件行为"映射数据可反哺模型微调，构成长期壁垒
- **众筹首发**：Crowd Supply 或立创开源硬件平台，兼具验证市场和品牌传播

## 被否决的想法（避免下游重复提出）

- **板载自演示模式**：用户否决。产品定位是板卡通过排线连接到外部目标板，依靠板卡可观测性和调试功能驱动开发，不需要自演示
- **V1 支持泛 Cortex-M**：缩窄为 STM32 M3/M4/M33，避免兼容性长尾
- **V1 支持 I2C/SPI**：推迟到 V2，V1 聚焦 UART + GPIO + SWD
- **V1 支持 Keil/IAR**：仅 arm-none-eabi-gcc，降低复杂度

## 技术约束与偏好

- **FPGA 选型未定**：需要评估 Lattice/Gowin（低成本国产）vs Xilinx（生态成熟）
- **ARM 核选型未定**：板载 ARM 用于板卡自身控制和 USB 通信，非目标芯片
- **编译工具链**：arm-none-eabi-gcc，用户明确选择
- **Agent 架构未定**：类 Claude Code 交互式，但具体 LLM 选型、本地/云端部署、嵌入式上下文注入方式待 PRD 阶段定义
- **通信接口**：板卡与 PC 通过 USB 连接，API 形态（REST/gRPC/本地 socket/SDK）待定

## 用户场景补充

- **核心场景**：Agent 自主完成 GPIO 点灯全流程（写 → 编 → 下 → 验）
- **进阶场景**：UART 通信 bug 定位（串口从机检测异常输出 → 逻辑分析仪抓时序 → Agent 定位根因 → 修复）
- **长期场景**：80% 嵌入式开发任务自动化，覆盖外设初始化、通信协议实现、传感器驱动开发等

## 开放问题

- 定价策略和商业模式
- FPGA 和板载 ARM 具体型号选型
- Agent 的 LLM 选型及部署架构（本地/云端/混合）
- 知识产权策略（代码上传到云端的隐私问题）
- FPGA 逻辑分析仪的目标采样率和通道数
- 硬件认证计划（CE/FCC）
- 供应链和分销渠道
