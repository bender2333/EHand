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
