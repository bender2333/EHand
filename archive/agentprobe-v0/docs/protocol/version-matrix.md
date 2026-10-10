# AgentProbe Version Matrix

_Primary Mission: Make physical verification agent-executable._

Version compatibility is part of the Agent-facing contract. A command may execute only when protocol, schema, Skill, firmware, bitstream, and topology versions are compatible.

| Contract | Current Version | Compatibility Rule |
|----------|-----------------|--------------------|
| Protocol | `0.1.0` | Exact match required during pre-V1 implementation. |
| Outcome schema | `0.1.0` | Exact match required. |
| Evidence schema | `0.1.0` | Exact match required. |
| Scenario schema | `0.1.0` | Exact match required. |
| Topology schema | `0.1.0` | Exact match required. |
| Skill schema | `0.1.0` | Exact match required. |
| Firmware | `0.1.x` | Must declare compatible protocol version. |
| Bitstream | `0.1.x` | Must declare compatible address map and protocol versions. |

## Compatibility Failure Behavior

If any compatibility check fails:

1. Do not execute state-changing hardware actions.
2. Return `unsupported` when the version is known incompatible.
3. Return `unknown` when version identity cannot be established.
4. Return `approval_pending` only when a human can safely approve a scoped action.

## Golden Device Policy

Golden AgentProbe firmware/bitstream update mode is disabled by default. A Golden update requires explicit human authorization scoped to:

- Golden serial
- Artifact hash
- Firmware or bitstream version
- Approval reason
- Single requested action
