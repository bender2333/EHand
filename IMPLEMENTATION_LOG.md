# AgentProbe — Implementation Log

_Last updated: 2026-05-07T16:03:25+08:00_
_Primary Mission: Make physical verification agent-executable._

## Understanding Confirmed

I have read the current PRD (`prd_v1.2.md` with v1.4 updates), architecture (`_bmad-output\architecture.md`), and task list (`tasks.md`). The Primary Mission is to make embedded physical verification executable by an AI Agent: AgentProbe must turn build, flash, capture, diagnosis, regression, and report evidence into stable machine-readable contracts so an Agent can prove whether firmware behavior works in the physical world. The Phase 1 North Star is the two-board self-hosting loop where a stable Golden AgentProbe helps an Agent develop and verify a DUT AgentProbe with auditable evidence. The product strategy now explicitly uses the observability formula: closed-loop capability is limited by the minimum of reasoning capability, observable range, executable range, and semantic translation quality.

## Progress

| Task | Name | Status | Completed At |
|------|------|--------|--------------|
| 01 | Close AI-native contracts | Done | 2026-05-06T10:30:57+08:00 |
| 02 | Bootstrap monorepo | Done | 2026-05-07T16:03:25+08:00 |
| 03 | Build replay-first loop | Done | 2026-05-07T16:03:25+08:00 |
| 04 | Implement device identity topology | Pending |  |
| 05 | Close SoM baseboard contract | Pending |  |
| 06 | Prove single-board loop | Pending |  |
| 07 | Implement DUT SWD control | Pending |  |
| 08 | Implement observation path | Pending |  |
| 09 | Implement diagnosis reporting | Pending |  |
| 10 | Prove self-hosting loop | Pending |  |
| 11 | Add SPI mock loop | Pending |  |
| 12 | Write Skill quickstart assets | Pending |  |
| 13 | Prepare external reference demo | Pending |  |

## Architecture & Contract Rewrite (v0.2.0) — 2026-06-06

The PRD-flavored, prose-heavy architecture documents were replaced with a single authoritative, module-based, Mermaid-driven [`ARCHITECTURE.md`](ARCHITECTURE.md). Driver: the previous architecture mixed PRD/debate content, lacked clean module decomposition, interface specs, and diagrams.

**Decisions (confirmed with user):**

- Clean-slate technical architecture rewrite; contracts redesigned alongside. V1 North Star unchanged (two-board self-hosting loop).
- **Mock Engine is the differentiator core** with a deep sub-architecture (ARCHITECTURE.md §7: three-layer execution model, declarative MockModel + script escape hatch, SPI slave internals, behavior state machine, fidelity model L1–L4, config sequence). SWD/analyzer/UART are must-be-solid base capabilities, each with a full sub-architecture (§8).
- Mock model format = declarative data model + script escape hatch (`mock_model.schema.json`). Mock fidelity = provenance declaration only in V1 (`mock_fidelity`); mock-vs-real auto diff detection is planned.

**Contract changes (0.1.0 → 0.2.0):**

- Evidence Envelope de-duplicated: removed redundant top-level `device_id`/`serial`/`firmware_version`/`bitstream_version` and `*_role`; identity now only in `source_device`/`target_device`. Added optional `bottleneck` and `mock_fidelity`.
- New `mock_model.schema.json`; `protocol.toml` gained `[mock_fidelity]` and `[bottleneck]`; all schema/`ap_shared.h`/package versions synced to 0.2.0. See `docs/protocol/version-matrix.md`.

**Code alignment:** new `models/evidence.py` (de-duplicated EvidenceEnvelope), `transport/` abstraction (`base.py` Protocol + USB/Mock stubs), `mock/` host module (load/validate model, fidelity provenance), updated replay fixture + tests + `generate_protocol.py`.

**Docs:** old PRD/architecture/analysis moved to `archive/`; `README.md`, `AGENTS.md`, `tasks.md` re-pointed to `ARCHITECTURE.md` and 0.2.0 contracts.

**Verification:** all schemas/TOML/fixture parse; fixture passes `evidence.schema.json` v0.2.0 (jsonschema); `compileall` OK; 2 unit tests pass (incl. new de-dup assertion); `scenario run --replay --json` returns `regression_pass` with de-duplicated envelope; version consistency 0.2.0 across protocol.toml / schemas / ap_shared.h / package; 19 Mermaid blocks lint-clean.

## AI-Native Service Layering (ARCHITECTURE.md §15) — 2026-06-06

Added the authoritative six-layer service stack to clarify how AgentProbe serves today's off-the-shelf Agents and a future self-built Agent + RAG on one base.

**Decisions (confirmed with user):**

- **Capability plane vs reasoning plane split (new principle P9):** the capability service layer is a headless core exposing one transport-agnostic semantic contract (Capability / Evidence / Verdict). CLI, GUI, MCP are peer clients — none is "the API". Source of truth is declarative files + the evidence store, not any single RPC.
- **MCP is a convenience binding, not the API** — justified because the source of truth is files + evidence, so a future self-built Agent/RAG reads the same artifacts and is not locked to MCP.
- **GUI retained as the human supervision/analysis client** (read-only observation + approvals), peer to the Agent, not the product itself.
- **Communication is transport-agnostic:** local cross-process IPC now (local-first), network bindings (gRPC/REST/WS) later by swapping the binding only — the four upper layers don't move.
- **Knowledge layer normalized now, RAG deferred:** diagnosis knowledge / Mock model library / failure catalog unified behind a `KnowledgeStore` interface (`list`/`get`/naive `search`); future RAG implements `search()` without touching callers. Only structural addition is `knowledge/`.
- **Reasoning layer seat reserved, empty in V1;** the §14.3 `agent_reasoning_gap` bottleneck is the signal for when to invest in a self-built reasoning layer.

**Doc edits:** new §15 (six-layer stack + service/client Mermaid + contract seam + knowledge normalization + reasoning seat + module projection + comms evolution); §12 收敛为演化路线时间轴并声明 §15 为权威分层(旧 Layer A/B/C/D 映射到 §15);§1/§3 旧"不自研 Agent/MCP/GUI"表述改为 headless core + 平级客户端 + 预留推理层座位 + GUI 保留;新增原则 P9。

**Bug fix:** the previous rewrite had silently dropped the §8 body (基础能力层 SWD/analyzer/UART) due to a placeholder collision — only a leftover orphan line remained between §7.7 and §9. Restored §8.1–§8.3 in full. ARCHITECTURE.md now has sections 0–15 with no gaps and 26 lint-clean Mermaid blocks.

## Task Details

### Task 01 — Close AI-native contracts

**Mission Link:** This task defines the machine contracts that let an Agent consume physical verification results without relying on human interpretation.

**What was built:** Created project-level Agent instructions, baseline task list, protocol SSOT, AXI address map SSOT, outcome/evidence/scenario/topology schemas, terminal taxonomy, and version matrix.

**Files created/modified:**

- `AGENTS.md`
- `tasks.md`
- `IMPLEMENTATION_LOG.md`
- `ISSUES_AND_DEVIATIONS.md`
- `protocol.toml`
- `address_map.toml`
- `scenarios\schemas\outcome.schema.json`
- `scenarios\schemas\evidence.schema.json`
- `scenarios\schemas\scenario.schema.json`
- `scenarios\schemas\topology.schema.json`
- `docs\protocol\terminal-taxonomy.md`
- `docs\protocol\version-matrix.md`

**Tests:** Parsed `protocol.toml`, `address_map.toml`, and all JSON schema files successfully with Python.

**Notes:** The user-provided prompt contained older SHT30/I2C-first V1 wording. It was incorporated into `AGENTS.md` but aligned to the current v1.3 self-hosting strategy to avoid reintroducing a PRD/architecture conflict.

`[TASK 01/13 COMPLETE] — Close AI-native contracts`: The project now has a machine-contract baseline for Agent-readable outcomes, evidence, scenario definitions, topology identity, terminal taxonomy, and version compatibility.

### Task 02 — Bootstrap monorepo

**Mission Link:** This task creates the repository boundaries that allow CLI, daemon, firmware, PL, scenarios, and Skill work to evolve without breaking the verification loop.

**What was built:** Created the monorepo skeleton for CLI, firmware, FPGA/PL, hardware, scenarios, skills, docs, scripts, and CI. Added a minimal Click-based CLI entrypoint with `ap device status --json`, protocol check tooling, firmware and FPGA placeholders, Skill capability boundary, and CI workflows for CLI compile and protocol sync.

**Files created/modified:**

- `README.md`
- `.gitignore`
- `.editorconfig`
- `Makefile`
- `cli\pyproject.toml`
- `cli\README.md`
- `cli\src\agentprobe\__init__.py`
- `cli\src\agentprobe\__main__.py`
- `cli\src\agentprobe\errors.py`
- `cli\src\agentprobe\cli\app.py`
- `cli\src\agentprobe\cli\options.py`
- `cli\tools\generate_protocol.py`
- `firmware\README.md`
- `firmware\CMakeLists.txt`
- `firmware\include\ap_shared.h`
- `fpga\README.md`
- `fpga\Makefile`
- `fpga\rtl\include\ap_protocol_generated.vh`
- `fpga\rtl\top\ap_top.v`
- `hardware\som-baseboard\README.md`
- `docs\quickstart\first-loop.md`
- `skills\agentprobe.skill.md`
- `scripts\bootstrap.ps1`
- `scripts\verify-env.ps1`
- `.github\workflows\ci-cli.yml`
- `.github\workflows\ci-protocol-sync.yml`

**Tests:** Parsed TOML/JSON contract files, compiled `cli\src`, ran protocol check, confirmed Click availability, and ran `python -m agentprobe device status --json` with `PYTHONPATH=cli\src`.

**Notes:** The bootstrap CLI returns `unknown` by design because hardware and replay transports are not initialized until later tasks.

`[TASK 02/13 COMPLETE] — Bootstrap monorepo`: The repository now has the cross-domain structure and initial tooling needed to begin replay, identity/topology, firmware, PL, and Skill implementation.

### Task 03 — Build replay-first loop

**Mission Link:** This task proves the Agent-facing loop before hardware is available, preventing JSON/evidence/report contracts from being deferred until late integration.

**What was built:** Implemented a no-hardware replay path with a canonical self-hosting fixture, Evidence Envelope output, `ReplayTransport`, `run_replay_scenario()`, and `ap scenario run --replay --json`.

**Files created/modified:**

- `cli\src\agentprobe\models\outcome.py`
- `cli\src\agentprobe\daemon\replay_transport.py`
- `cli\src\agentprobe\core\engine.py`
- `cli\src\agentprobe\cli\app.py`
- `scenarios\replay\nominal\self_hosting_replay.json`
- `scenarios\templates\self-hosting-replay\scenario.json`
- `cli\tests\__init__.py`
- `cli\tests\unit\__init__.py`
- `cli\tests\unit\test_replay_cli.py`

**Tests:** Compiled CLI source, ran unit test discovery, parsed replay fixtures, and ran `python -m agentprobe scenario run --replay --json`.

**Notes:** The replay fixture produces `regression_pass` with Golden/DUT `source_device` and `target_device` identities. Failure-path replay fixtures are deferred to diagnosis/regression tasks.

`[TASK 03/13 COMPLETE] — Build replay-first loop`: The Agent can now execute a no-hardware self-hosting replay and receive a stable JSON outcome with Evidence Envelope.
