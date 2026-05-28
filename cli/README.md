# AgentProbe CLI

The CLI is the official Agent-facing automation surface. Every command must support human-readable output and `--json` with equivalent terminal semantics.

Initial command surface:

- `ap device status`
- `ap scenario run --replay`
- `ap diagnose`
- `ap report`

The daemon owns device access; CLI commands must not bypass daemon transport boundaries.
