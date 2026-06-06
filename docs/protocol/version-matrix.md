# AgentProbe Version Matrix

_Primary Mission: Make physical verification agent-executable._

Version compatibility is part of the Agent-facing contract. A command may execute only when protocol, schema, Skill, firmware, bitstream, and topology versions are compatible.

| Contract | Current Version | Compatibility Rule |
|----------|-----------------|--------------------|
| Protocol | `0.2.0` | Exact match required during pre-V1 implementation. |
| Outcome schema | `0.2.0` | Exact match required. |
| Evidence schema | `0.2.0` | Exact match required. |
| Scenario schema | `0.2.0` | Exact match required. |
| Topology schema | `0.2.0` | Exact match required. |
| Skill schema | `0.2.0` | Exact match required. |
| Mock model schema | `0.2.0` | Exact match required. |
| Firmware | `0.2.x` | Must declare compatible protocol version. |
| Bitstream | `0.2.x` | Must declare compatible address map and protocol versions. |

## Contract Change Log

### 0.1.0 → 0.2.0 (架构重写, 2026-06)

- **Evidence Envelope 去冗余**: 删除顶层冗余身份字段 `device_id` / `serial` / `firmware_version` / `bitstream_version` 与 `source_device_role` / `target_device_role`。设备身份现在仅存于 `source_device` / `target_device` 嵌套对象(共享 `$defs/device_identity`)。
- **Evidence Envelope 新增**: 可选 `bottleneck`(枚举: observation_gap / execution_gap / semantic_translation_gap / agent_reasoning_gap / support_boundary_gap)与 `mock_fidelity`(经 Mock Engine 产出的证据必填; level L1–L4 + model_id + model_version)。
- **新增 Mock Model schema** (`mock_model.schema.json`): 声明式外设 mock 模型 + 脚本逃生舱(架构 §7.2)。
- **protocol.toml 新增**: `[mock_fidelity]` 与 `[bottleneck]` 段;`[versions]` 新增 `mock_model_schema`。
- 所有 schema `const` 版本与 `ap_shared.h` 的 `AP_PROTOCOL_VERSION` 同步到 `0.2.0`。


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
