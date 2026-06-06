# E1 SoM 选型交接

## 目标

- 为 AgentProbe v0.2 单板地基选择可采购、可调试、可承载 PS/PL 闭环的 Zynq-7020 SoM 或开发套件。
- 本文只给候选和取舍维度；最终 SKU 是人工采购决策，属于 DEC1。

## 必选条件

- Zynq-7020 或兼容 7Z020 等级，具备 ARM PS + Artix-7 PL。
- 至少暴露 USB-UART 或 USB 设备通路，便于 host 侧 `device status` 和后续 daemon 接入。
- 暴露足够 PL IO：SWD、UART、SPI、8ch logic analyzer、GPIO、power/ground 参考。
- 有可重复的 JTAG/boot 模式文档，支持固件和 bitstream 交叉编译产物上板。
- 采购渠道稳定，资料无需 NDA 才能完成 bring-up。

## 候选

| 候选 | 优点 | 风险 |
|---|---|---|
| Digilent Zybo Z7-20 | 文档完整，Zynq-7020，社区资料多，适合早期 bring-up | 不是 SoM 形态，后续产品化需迁移 |
| Trenz TE0720-03-1CFA + baseboard | SoM 路径更接近最终硬件，可复用模块化设计 | 采购和 baseboard 组合复杂度更高 |
| MYIR Z-Turn Board V2 7020 | 成本和接口较平衡，有现成开发板资料 | 文档和社区资料不如 Digilent 稳定 |

## 推荐

- 研发首板推荐 Digilent Zybo Z7-20。
- 理由：E1 的目标是把单板通路写到可上板交接程度，不是冻结产品硬件。资料完整和调试路径稳定比 SoM 形态更重要。
- 若采购必须走 SoM 形态，优先 Trenz TE0720 系列，并要求同步采购官方或成熟 baseboard。

## 人工决策 DEC1

- 需要人工确认最终采购 SKU、数量、供货周期、配套线缆和电平转接。
- 决策后更新 `scenarios/topologies/self-hosting-two-board.json` 里的 serial、device_id 命名和实际连接信号。

## 验收判据

- 已选 SKU 满足必选条件。
- 能按厂家文档完成供电、JTAG/USB 连接和 boot 模式设置。
- 能为 E2/E5 后续任务暴露 SWD、UART、SPI、logic capture、power、ground 通路。
- 若选择非推荐项，需在 `docs/decision.md` 记录偏离原因。
