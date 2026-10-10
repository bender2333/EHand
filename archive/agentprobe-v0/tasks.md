# AgentProbe — Baseline Implementation Tasks

_Primary Mission: Make physical verification agent-executable._

These tasks are ordered to prove the AI-native physical verification loop with the least unnecessary scope. The sequence is contract/replay-first, then single-board bring-up, then two-board self-hosting, then SPI Mock/Analyzer expansion.

## Task List

| Task | ID | Name | Depends On |
|------|----|------|------------|
| 01 | `contract-closure` | Close AI-native contracts | None |
| 02 | `repo-bootstrap` | Bootstrap monorepo | T-01 |
| 03 | `replay-first-loop` | Build replay-first loop | T-01 |
| 04 | `device-identity-topology` | Implement device identity topology | T-01 |
| 05 | `som-baseboard-closure` | Close SoM baseboard contract | T-01 |
| 06 | `single-board-loop` | Prove single-board loop | T-02, T-04, T-05 |
| 07 | `swd-dut-control` | Implement DUT SWD control | T-06 |
| 08 | `analyzer-uart-observation` | Implement observation path | T-06 |
| 09 | `diagnosis-reporting` | Implement diagnosis reporting | T-03 |
| 10 | `self-hosting-loop` | Prove self-hosting loop | T-07, T-08, T-09 |
| 11 | `spi-mock-loop` | Add SPI mock loop | T-10 |
| 12 | `skill-quickstart` | Write Skill quickstart assets | T-03, T-10 |
| 13 | `external-reference-demo` | Prepare external reference demo | T-11 |

## Task Details

### T-01 — Close AI-native contracts

**Mission Link:** This task defines the machine contracts that let an Agent consume physical verification results without relying on human interpretation.

Define `protocol.toml`, `address_map.toml`, outcome/evidence/scenario schemas, terminal taxonomy, version matrix, and generated-hash enforcement before feature work starts.

### T-02 — Bootstrap monorepo

**Mission Link:** This task creates the repository boundaries that allow CLI, daemon, firmware, PL, scenarios, and Skill work to evolve without breaking the verification loop.

Create the monorepo structure with `cli`, `firmware`, `fpga`, `hardware`, `scenarios`, `skills`, `docs`, `scripts`, and CI skeleton following the updated architecture.

### T-03 — Build replay-first loop

**Mission Link:** This task proves the Agent-facing loop before hardware is available, preventing JSON/evidence/report contracts from being deferred until late integration.

Implement CLI + daemon + `replay_transport` + canonical replay fixture so an Agent can run a no-hardware closed loop and receive stable JSON outcome, Evidence Envelope, evidence pack, and report.

### T-04 — Implement device identity topology

**Mission Link:** This task prevents Golden/DUT confusion, which is essential for safe agent-executable physical actions.

Add device registry and topology schema for `golden`, `dut`, and `external_target` roles, serials, firmware/bitstream versions, `connection_topology_id`, and state-changing action guards.

### T-05 — Close SoM baseboard contract

**Mission Link:** This task constrains hardware choices to the minimum rig needed to prove agent-executable physical verification.

Select or contract the Zynq-7020 SoM/dev-kit path and define minimal baseboard/topology requirements for self-hosting, SWD, UART, SPI, analyzer, power, and protection.

### T-06 — Prove single-board loop

**Mission Link:** This task establishes the first real hardware evidence path from Agent command to PL event and back to auditable output.

Bring up CLI -> daemon -> USB -> PS -> AXI -> PL -> event -> evidence pack on one AgentProbe board with device status and PL selftest.

### T-07 — Implement DUT SWD control

**Mission Link:** This task gives the Agent controlled hands to flash and reset the DUT through Golden AgentProbe.

Implement CMSIS-DAP v2/SWD path so Golden AgentProbe can identify, flash, reset, and verify a DUT under role/topology enforcement.

### T-08 — Implement observation path

**Mission Link:** This task gives the Agent eyes on the DUT through structured signal and UART evidence.

Implement 8ch analyzer minimal event stream plus UART bridge/snoop so Golden can observe DUT logs and signals and correlate them into evidence.

### T-09 — Implement diagnosis reporting

**Mission Link:** This task turns raw evidence into terminal outcomes that an Agent and engineer can audit.

Implement `ap diagnose`, evidence summary, final report, confidence/evidence linkage, bottleneck classification (`observation_gap`, `execution_gap`, `semantic_translation_gap`, `agent_reasoning_gap`, `support_boundary_gap`), and `regression_pass` / `explicit_escalation` / `unsupported` / `unknown` / `approval_pending` outputs.

### T-10 — Prove self-hosting loop

**Mission Link:** This task is the core proof that AgentProbe enables an Agent to participate in developing and verifying AgentProbe itself.

Run Golden AgentProbe -> DUT AgentProbe loop where Agent changes DUT behavior, builds, flashes, observes, diagnoses, fixes or escalates, and produces an auditable evidence pack.

### T-11 — Add SPI mock loop

**Mission Link:** This task adds the first hard-real-time Mock/Analyzer closed loop for agent-executable peripheral verification.

Implement SPI Slave mock and SPI decoder as the first hard-real-time Mock/Analyzer closed loop with nominal and failure-path scenarios.

### T-12 — Write Skill quickstart assets

**Mission Link:** This task lets Agents discover and safely use AgentProbe capabilities without hidden human knowledge.

Create AgentProbe Skill and quickstarts for replay loop, single-board loop, and two-board self-hosting loop with explicit safety, approval guidance, `supported_capabilities`, `not_supported`, and `planned_capabilities`.

### T-13 — Prepare external reference demo

**Mission Link:** This task translates the self-hosting proof into an externally understandable demo without weakening the Phase 1 North Star.

After self-hosting proof, prepare temperature-sensor or equivalent external demo; add I2C Mock/decoder only if that demo remains I2C/SHT30 based.
