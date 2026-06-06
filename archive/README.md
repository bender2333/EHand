# Archive — 历史 PRD 与架构资料

此目录保存 AgentProbe 在架构重写(2026-06)之前的历史文档,**仅作产品背景与决策追溯之用**。

> **权威技术架构以仓库根目录的 [`ARCHITECTURE.md`](../ARCHITECTURE.md) 为准。**
> 这些归档文档可能与当前架构、契约版本和模块命名不一致,不应作为实现依据。

## 内容

| 文件/目录 | 说明 |
|-----------|------|
| `PRD_AgentProbe.md` / `PRD_AgentProbe_Part3_continued.md` / `PRD_AgentProbe_Part4.md` | 早期 PRD v1.0 草稿(含市场/BOM/成本/路线图等产品材料) |
| `prd_v1.2.md` | BMAD 工作流产出的 PRD(含 v1.4 战略修正) |
| `architecture_evolution_analysis.md` | 演化角度的架构分析(散文 + 辩论) |
| `agentprobe_execution_prompt.md` | 早期自主执行 prompt |
| `_bmad-output/` | BMAD 工作流产出:旧 `architecture.md`、`prd.md`、product briefs、research、readiness report |

## 为什么归档

重写前的架构文档以 PRD 风格散文和决策辩论为主,缺少干净的模块分解、接口规范和架构图。重写后:

- 技术架构集中到根目录 `ARCHITECTURE.md`(模块化、Mermaid 图驱动、契约 v0.2.0)。
- 产品动机/市场/商业内容仍可在此查阅,但不再混入架构文档。

需要了解产品背景时查阅本目录;需要实现指引时一律以 `ARCHITECTURE.md` 和 `protocol.toml` / `address_map.toml` / `scenarios/schemas/` 契约为准。
