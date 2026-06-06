from __future__ import annotations

import argparse
import hashlib
from pathlib import Path


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


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="Validate SSOT files are present.")
    args = parser.parse_args()

    sources = [PROTOCOL, ADDRESS_MAP, *SCHEMAS]
    missing = [str(path) for path in sources if not path.exists()]
    if missing:
        raise SystemExit(f"Missing SSOT files: {', '.join(missing)}")

    if args.check:
        print(f"protocol_sha256={digest(PROTOCOL)}")
        print(f"address_map_sha256={digest(ADDRESS_MAP)}")
        for schema in SCHEMAS:
            print(f"{schema.name}_sha256={digest(schema)}")


if __name__ == "__main__":
    main()
