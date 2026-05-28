# AgentProbe Terminal Taxonomy

_Primary Mission: Make physical verification agent-executable._

Every non-interactive task must end in one explicit terminal state. Human-readable output and JSON output must use the same terminal semantics.

| Terminal State | Meaning | Required Evidence |
|----------------|---------|-------------------|
| `regression_pass` | Evidence supports the validation objective. | Build, flash, capture, diagnosis, regression, and report references. |
| `explicit_escalation` | Evidence is insufficient, recovery is unsafe, or the support boundary is exceeded. | Escalation reason, supporting evidence, and next human action. |
| `unsupported` | The request is outside the declared V1 boundary. | Boundary check result and unsupported dimension. |
| `unknown` | The system cannot determine the result or cannot verify identity/topology. | Unknown reason, missing evidence, and next diagnostic action. |
| `approval_pending` | Human authorization is required before continuing. | Requested action, target device identity, safety reason, and approval scope. |

## Minimum JSON Fields

Every outcome must include:

- `status`
- `terminal_state`
- `evidence`
- `verdict`
- `confidence`
- `next_action`

## Self-hosting Identity Requirements

Every self-hosting outcome must include:

- `source_device_role`
- `target_device_role`
- `device_id`
- `serial`
- `firmware_version`
- `bitstream_version`
- `connection_topology_id`

If any identity or topology field cannot be verified, the terminal state must be `unknown` or `approval_pending`, never `regression_pass`.
