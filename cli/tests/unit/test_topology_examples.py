from __future__ import annotations

import json
import unittest
from pathlib import Path

import jsonschema


ROOT = Path(__file__).resolve().parents[3]


class TopologyExampleTests(unittest.TestCase):
    def test_self_hosting_two_board_topology_matches_schema(self) -> None:
        schema = json.loads((ROOT / "scenarios" / "schemas" / "topology.schema.json").read_text())
        topology = json.loads(
            (ROOT / "scenarios" / "topologies" / "self-hosting-two-board.json").read_text()
        )

        jsonschema.validate(instance=topology, schema=schema)
        roles = {device["role"] for device in topology["devices"]}
        self.assertIn("golden", roles)
        self.assertIn("dut", roles)
        self.assertIn("host", roles)


if __name__ == "__main__":
    unittest.main()
