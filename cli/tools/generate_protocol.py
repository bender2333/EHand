from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
import tomllib
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
PROTOCOL = ROOT / "protocol.toml"
ADDRESS_MAP = ROOT / "address_map.toml"
SCHEMA_DIR = ROOT / "scenarios" / "schemas"
SCHEMAS = [
    SCHEMA_DIR / "outcome.schema.json",
    SCHEMA_DIR / "evidence.schema.json",
    SCHEMA_DIR / "scenario.schema.json",
    SCHEMA_DIR / "topology.schema.json",
    SCHEMA_DIR / "mock_model.schema.json",
]
PYTHON_CONSTANTS = ROOT / "cli" / "src" / "agentprobe" / "protocol" / "_generated.py"
FIRMWARE_HEADER = ROOT / "firmware" / "include" / "ap_protocol_generated.h"
FPGA_DEFINES = ROOT / "fpga" / "rtl" / "include" / "ap_protocol_generated.vh"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_protocol() -> dict[str, Any]:
    with PROTOCOL.open("rb") as protocol_file:
        return tomllib.load(protocol_file)


def _constant_name(prefix: str, name: str) -> str:
    return f"{prefix}_{name.upper()}"


def write_python_constants(protocol: dict[str, Any], output: Path = PYTHON_CONSTANTS) -> None:
    versions = protocol["versions"]
    terminal_states = protocol["terminal_states"]["allowed"]
    error_codes = protocol["error_codes"]
    message_types = protocol["message_types"]
    state_actions = protocol["state_changing_actions"]["allowed_requires_identity"]

    lines = [
        '"""Generated from protocol.toml. Do not edit manually."""',
        "",
        f'PROTOCOL_VERSION = "{versions["protocol"]}"',
        "",
    ]
    lines.extend(
        f'{_constant_name("TERMINAL", state)} = "{state}"' for state in terminal_states
    )
    lines.append("")
    lines.extend(f'{_constant_name("ERR", name)} = {value}' for name, value in error_codes.items())
    lines.append("")
    lines.extend(f'{_constant_name("MSG", name)} = {value}' for name, value in message_types.items())
    lines.append("")
    lines.append("STATE_CHANGING_ACTIONS = frozenset([")
    for action in state_actions:
        lines.append(f'    "{action}",')
    lines.append("])")
    lines.append("")
    lines.append(
        "GOLDEN_UPGRADE_MODE_DEFAULT = "
        f'"{protocol["state_changing_actions"]["golden_upgrade_mode_default"]}"'
    )
    lines.append("")

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(lines), encoding="utf-8", newline="\n")


def write_firmware_header(protocol: dict[str, Any], output: Path = FIRMWARE_HEADER) -> None:
    error_codes = protocol["error_codes"]
    message_types = protocol["message_types"]
    lines = [
        "/* Generated from protocol.toml. Do not edit manually. */",
        "#ifndef AP_PROTOCOL_GENERATED_H",
        "#define AP_PROTOCOL_GENERATED_H",
        "",
        f'#define AP_PROTOCOL_VERSION "{protocol["versions"]["protocol"]}"',
        "",
        "typedef enum ap_err {",
    ]
    for name, value in error_codes.items():
        lines.append(f"    AP_ERR_{name.upper()} = {value},")
    lines.extend(["} ap_err_t;", ""])
    lines.append("typedef enum ap_msg {")
    for name, value in message_types.items():
        lines.append(f"    AP_MSG_{name.upper()} = 0x{value:04X},")
    lines.extend(["} ap_msg_t;", "", "#endif"])
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(lines), encoding="utf-8", newline="\n")


def write_fpga_defines(protocol: dict[str, Any], output: Path = FPGA_DEFINES) -> None:
    error_codes = protocol["error_codes"]
    message_types = protocol["message_types"]
    lines = [
        "// Generated from protocol.toml. Do not edit manually.",
        f'`define AP_PROTOCOL_VERSION "{protocol["versions"]["protocol"]}"',
    ]
    for name, value in error_codes.items():
        lines.append(f"`define AP_ERR_{name.upper()} {value}")
    for name, value in message_types.items():
        lines.append(f"`define AP_MSG_{name.upper()} 32'h{value:04X}")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")


def generate_all() -> None:
    protocol = load_protocol()
    write_python_constants(protocol)
    write_firmware_header(protocol)
    write_fpga_defines(protocol)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="Validate SSOT files are present.")
    parser.add_argument("--generate", action="store_true", help="Generate protocol constants.")
    args = parser.parse_args()

    sources = [PROTOCOL, ADDRESS_MAP, *SCHEMAS]
    missing = [str(path) for path in sources if not path.exists()]
    if missing:
        raise SystemExit(f"Missing SSOT files: {', '.join(missing)}")

    if args.generate:
        generate_all()

    if args.check:
        generated = [PYTHON_CONSTANTS, FIRMWARE_HEADER, FPGA_DEFINES]
        generated_missing = [str(path) for path in generated if not path.exists()]
        if generated_missing:
            raise SystemExit(f"Missing generated files: {', '.join(generated_missing)}")

        print(f"protocol_sha256={digest(PROTOCOL)}")
        print(f"address_map_sha256={digest(ADDRESS_MAP)}")
        for schema in SCHEMAS:
            print(f"{schema.name}_sha256={digest(schema)}")
        for path in generated:
            print(f"{path.relative_to(ROOT)}_sha256={digest(path)}")


if __name__ == "__main__":
    main()
