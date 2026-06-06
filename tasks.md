# AgentProbe — Baseline Implementation Tasks

_Primary Mission: Make physical verification agent-executable._
_Authoritative architecture: [`ARCHITECTURE.md`](ARCHITECTURE.md) (v0.2.0). Contracts: `protocol.toml` / `address_map.toml` / `scenarios/schemas/` (v0.2.0)._

These tasks prove the AI-native physical verification loop with the least unnecessary scope: contract/replay-first, then single-board bring-up, then two-board self-hosting, then SPI Mock/Analyzer expansion. **Mock Engine is the differentiator core (ARCHITECTURE.md §7); SWD/analyzer/UART are the must-be-solid base capabilities (§8).**

## Task List

| Task | ID | Name | Depends On | Module(s) (ARCHITECTURE.md) |
|------|----|------|------------|------------------------------|
| 01 | `contract-closure` | Close AI-native contracts | None | §10 契约层 |
| 02 | `repo-bootstrap` | Bootstrap monorepo | T-01 | §13 目录映射 |
| 03 | `replay-first-loop` | Build replay-first loop | T-01 | `transport` (§5.3), `core` |
| 04 | `device-identity-topology` | Implement device identity topology | T-01 | `devices` (§10.4) |
| 05 | `som-baseboard-closure` | Close SoM baseboard contract | T-01 | §6 Device 架构 |
| 06 | `single-board-loop` | Prove single-board loop | T-02, T-04, T-05 | `transport.usb` (§5.3, §6) |
| 07 | `swd-dut-control` | Implement DUT SWD control | T-06 | §8.1 SWD/烧录 |
| 08 | `analyzer-uart-observation` | Implement observation path | T-06 | §8.2 分析仪 / §8.3 UART |
| 09 | `diagnosis-reporting` | Implement diagnosis reporting | T-03 | `diagnosis` / `evidence` (§14.3) |
| 10 | `self-hosting-loop` | Prove self-hosting loop | T-07, T-08, T-09 | §11 Self-Hosting Loop |
| 11 | `spi-mock-loop` | Add SPI mock loop | T-10 | **§7 Mock Engine (`mock`)** |
| 12 | `skill-quickstart` | Write Skill quickstart assets | T-03, T-10 | §14.4 Skill boundary |
| 13 | `external-reference-demo` | Prepare external reference demo | T-11 | §7.7 演化预留 |

## Task Details

### T-01 — Close AI-native contracts

**Mission Link:** Defines the machine contracts that let an Agent consume physical verification results without human interpretation.

Define `protocol.toml`, `address_map.toml`, outcome/evidence/scenario/topology/mock_model schemas, terminal taxonomy, version matrix, and generated-hash enforcement before feature work. Contract version 0.2.0; Evidence Envelope identity is de-duplicated into `source_device`/`target_device` (ARCHITECTURE.md §10.2).

### T-02 — Bootstrap monorepo

**Mission Link:** Creates repository boundaries so CLI, daemon, firmware, PL, scenarios, and Skill work can evolve without breaking the loop.

Create the monorepo structure (`cli`, `firmware`, `fpga`, `hardware`, `scenarios`, `skills`, `docs`, `scripts`) and CI skeleton following the module map (ARCHITECTURE.md §13).

### T-03 — Build replay-first loop

**Mission Link:** Proves the Agent-facing loop before hardware exists, preventing JSON/evidence/report contracts from being deferred to late integration.

Implement CLI + daemon + `ReplayTransport` + canonical replay fixture so an Agent runs a no-hardware closed loop and gets a stable Outcome + Evidence Envelope. Honor replay parity (ARCHITECTURE.md P3 / §5.3).

### T-04 — Implement device identity topology

**Mission Link:** Prevents Golden/DUT confusion — essential for safe agent-executable physical actions (P5).

Add the `devices` registry and topology validator for `golden`/`dut`/`external_target`/`host` roles, serials, firmware/bitstream versions, `connection_topology_id`, and state-changing action guards (ARCHITECTURE.md §10.4).

### T-05 — Close SoM baseboard contract

**Mission Link:** Constrains hardware to the minimum rig needed to prove agent-executable physical verification.

Select the Zynq-7020 SoM/dev-kit path and define minimal baseboard/topology for self-hosting, SWD, UART, SPI, analyzer, power, and protection (ARCHITECTURE.md §6).

### T-06 — Prove single-board loop

**Mission Link:** Establishes the first real hardware evidence path from Agent command to PL event and back.

Bring up CLI → daemon → USB → PS → AXI → PL → event → Evidence Envelope on one board with device status and PL selftest. Implements `UsbTransport` (ARCHITECTURE.md §5.3, §6, §9).

### T-07 — Implement DUT SWD control

**Mission Link:** Gives the Agent controlled hands to flash and reset the DUT through Golden.

Implement CMSIS-DAP v2/SWD so Golden can identify, flash, reset, and verify a DUT under role/topology enforcement (ARCHITECTURE.md §8.1).

### T-08 — Implement observation path

**Mission Link:** Gives the Agent eyes on the DUT through structured signal and UART evidence.

Implement the 8ch analyzer minimal event stream plus UART bridge/snoop so Golden can observe DUT logs and signals and correlate them into evidence (ARCHITECTURE.md §8.2, §8.3).

### T-09 — Implement diagnosis reporting

**Mission Link:** Turns raw evidence into terminal outcomes an Agent and engineer can audit.

Implement `ap diagnose`, evidence summary, final report, confidence/evidence linkage, bottleneck classification (ARCHITECTURE.md §14.3), and `regression_pass` / `explicit_escalation` / `unsupported` / `unknown` / `approval_pending` outputs.

### T-10 — Prove self-hosting loop

**Mission Link:** The core proof that AgentProbe enables an Agent to participate in developing and verifying AgentProbe itself.

Run Golden → DUT loop where the Agent changes DUT behavior, builds, flashes, observes, diagnoses, fixes or escalates, and produces an auditable Evidence Envelope (ARCHITECTURE.md §11). Cover ≥1 nominal + ≥1 failure path.

### T-11 — Add SPI mock loop ★ (differentiator core)

**Mission Link:** Adds the first hard-real-time Mock/Analyzer closed loop for agent-executable peripheral verification — the AgentProbe moat.

Implement the SPI Slave mock (three-layer execution model, declarative MockModel + script escape hatch) and SPI decoder as the first hard-real-time Mock/Analyzer closed loop, with nominal and failure-path scenarios. Inject `mock_fidelity` provenance into every mock-derived Evidence Envelope (ARCHITECTURE.md §7, P7/P8). Implements `MockTransport` and `mock.configure()`.

### T-12 — Write Skill quickstart assets

**Mission Link:** Lets Agents discover and safely use AgentProbe capabilities without hidden human knowledge.

Create the AgentProbe Skill and quickstarts for the replay loop, single-board loop, and two-board self-hosting loop with explicit safety/approval guidance and machine-readable `supported_capabilities` / `not_supported` / `planned_capabilities` (ARCHITECTURE.md §14.4).

### T-13 — Prepare external reference demo

**Mission Link:** Translates the self-hosting proof into an externally understandable demo without weakening the Phase 1 North Star.

After self-hosting proof, prepare a temperature-sensor or equivalent external demo; add I2C Mock/decoder only if that demo is I2C/SHT30 based. New mock types reuse the same three-layer model + MockModel format (ARCHITECTURE.md §7.7).
