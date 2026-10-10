# AgentProbe

_Primary Mission: Make physical verification agent-executable._

AgentProbe is an AI-native embedded verification infrastructure project. Its Phase 1 North Star is a two-board self-hosting loop: a stable Golden AgentProbe helps an Agent build, flash, observe, diagnose, and fix a DUT AgentProbe with auditable evidence.

## Current Contract Baseline

- Product hardware path: Zynq-7020 SoM + minimal baseboard.
- Target hardware path: DUT AgentProbe and STM32 M3/M4/M33 external targets.
- Agent interface: Python CLI (`ap`) + local daemon + Skill files.
- V1 loop: SPI-first Mock/Analyzer, UART bridge/snoop, 8-channel capture, CMSIS-DAP v2.
- Evidence contract: stable terminal states, Evidence Envelope, versioned schemas, and topology identity.

## Repository Layout

| Path | Purpose |
|------|---------|
| `cli\` | Python CLI, daemon, protocol models, output formatters, tests |
| `firmware\` | Zynq PS firmware, USB task, SWD task, event aggregation |
| `fpga\` | Zynq PL RTL, Vivado scripts, simulation, constraints |
| `hardware\` | SoM baseboard, fixtures, cables, mechanical assets |
| `scenarios\` | Versioned scenarios, replay fixtures, schemas |
| `skills\` | AgentProbe Skill files and capability boundary |
| `docs\` | Quickstarts, protocol docs, hardware docs, examples |
| `scripts\` | Cross-domain bootstrap, verification, packaging scripts |

## First Implementation Priority

1. Close contract/generator enforcement.
2. Build replay-first loop.
3. Enforce device identity/topology.
4. Prove single-board loop.
5. Prove two-board self-hosting loop.
