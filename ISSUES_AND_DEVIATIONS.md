# AgentProbe — Issues & Deviations Log

_Last updated: 2026-05-07T16:03:25+08:00_

## Summary Table

| ID | Severity | Category | Task | Title | Status |
|----|----------|----------|------|-------|--------|
| I-001 | MED | Conflict | T-01 | User prompt contained older I2C/SHT30-first V1 wording | Resolved |
| I-002 | LOW | Gap | PRD/Architecture | Observability bottleneck formula was implicit | Resolved |
| I-003 | LOW | Gap | Architecture | SWD internal observation path was under-specified | Resolved |
| I-004 | LOW | Gap | Architecture | Evidence Envelope needed explicit schema/version/source-device definition | Resolved |
| I-005 | LOW | Gap | PRD/Skill | Skill capability boundary needed structured supported/not-supported/planned lists | Resolved |
| I-006 | LOW | Gap | PRD | Phase switch from observation bottleneck to Agent reasoning bottleneck was undefined | Resolved |

## Details

### I-001 — User prompt contained older I2C/SHT30-first V1 wording

**Severity:** MED

**Category:** Conflict

**Discovered in Task:** T-01

**Description:** The provided agent prompt referenced the older V1 boundary where SPI/I2C/UART Mock and the SHT30 temperature demo were treated as mandatory Phase 1 acceptance criteria. The updated PRD and architecture now define Phase 1 around two-board self-hosting with SPI-first Mock/Analyzer, while I2C/SHT30 is Phase 1.5 or an external reference demo.

**Impact on Primary Mission:** If the older wording were copied verbatim, future Agents could optimize for an external demo instead of the stronger North Star: a working, auditable, agent-executable self-hosting physical verification loop.

**Options Considered:**

- Option A: Copy the prompt verbatim and preserve the conflict.
- Option B: Write the prompt into `AGENTS.md` but align scope, acceptance, and safety rules with PRD v1.3 and architecture.

**Decision Taken:** Option B. The project-level prompt now preserves the user's autonomous execution intent while matching the current self-hosting strategy.

**Open Questions for Human Review:** None.

### I-002 — Observability bottleneck formula was implicit

**Severity:** LOW

**Category:** Gap

**Discovered in Task:** PRD/Architecture review

**Description:** PRD stated "Physical World -> Semantic JSON" but did not explicitly state that Agent closed-loop capability is bounded by reasoning, observable range, executable range, and semantic translation quality.

**Impact on Primary Mission:** Without the formula, future scope decisions could over-invest in Agent reasoning before physical observability and execution are sufficient.

**Options Considered:**

- Option A: Leave the principle implicit.
- Option B: Add an explicit product principle in Vision.

**Decision Taken:** Option B. PRD v1.4 adds the observability formula and clarifies V1's role in expanding observable and executable range.

**Open Questions for Human Review:** None.

### I-003 — SWD internal observation path was under-specified

**Severity:** LOW

**Category:** Gap

**Discovered in Task:** PRD/Architecture review

**Description:** Architecture covered CMSIS-DAP/SWD mainly as flash/debug control and did not describe non-stop internal observation through ITM/DWT/ETM.

**Impact on Primary Mission:** Internal trace extends observable range when external UART/SPI/GPIO evidence is insufficient.

**Options Considered:**

- Option A: Add ITM/DWT/ETM to V1.
- Option B: Declare ITM trace decode and DWT counters as V2, with ETM as conditional V2+.

**Decision Taken:** Option B. Architecture v1.4 adds the V2 internal observation track without expanding Phase 1.

**Open Questions for Human Review:** None.

### I-004 — Evidence Envelope needed explicit schema/version/source-device definition

**Severity:** LOW

**Category:** Gap

**Discovered in Task:** PRD/Architecture review

**Description:** Evidence schema existed, but architecture's data model did not explicitly define the stable Evidence Envelope with `schema_version`, `source_device`, and `target_device`.

**Impact on Primary Mission:** Agents need a stable envelope to consume evidence reliably instead of inferring from loose event streams.

**Options Considered:**

- Option A: Keep JSONL events as the main evidence contract.
- Option B: Define an envelope that wraps event summaries, device identity, diagnosis, and artifact references.

**Decision Taken:** Option B. Architecture and `evidence.schema.json` now include `source_device` and `target_device` envelope fields.

**Open Questions for Human Review:** None.

### I-005 — Skill capability boundary needed structured supported/not-supported/planned lists

**Severity:** LOW

**Category:** Gap

**Discovered in Task:** PRD/Skill review

**Description:** PRD required Skill schema governance but did not require a machine-readable capability boundary.

**Impact on Primary Mission:** Without explicit capability lists, Agents may treat roadmap text as executable capability.

**Options Considered:**

- Option A: Document boundaries only in prose.
- Option B: Require `supported_capabilities`, `not_supported`, and `planned_capabilities`.

**Decision Taken:** Option B. PRD v1.4 and `skills\agentprobe.skill.md` now require structured capability lists.

**Open Questions for Human Review:** None.

### I-006 — Phase switch from observation bottleneck to Agent reasoning bottleneck was undefined

**Severity:** LOW

**Category:** Gap

**Discovered in Task:** PRD/Architecture review

**Description:** PRD did not define when the project should stop prioritizing observable/executable range expansion and begin V3 Agent reasoning-layer work.

**Impact on Primary Mission:** A clear switch criterion prevents premature investment in custom Agent architecture while the physical verification loop remains observability-limited.

**Options Considered:**

- Option A: Leave phase switching as a qualitative judgment.
- Option B: Add a measurable bottleneck-classification threshold.

**Decision Taken:** Option B. PRD v1.4 adds bottleneck labels and a threshold for starting V3 Agent reasoning work.

**Open Questions for Human Review:** None.
