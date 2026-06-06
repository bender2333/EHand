import json
import unittest
from pathlib import Path

from click.testing import CliRunner
import jsonschema

from agentprobe.cli.app import main


ROOT = Path(__file__).resolve().parents[3]


class ReplayCliTests(unittest.TestCase):
    def test_replay_scenario_returns_regression_pass(self) -> None:
        result = CliRunner().invoke(main, ["scenario", "run", "--replay", "--json"])

        self.assertEqual(result.exit_code, 0, result.output)
        payload = json.loads(result.output)
        self.assertEqual(payload["terminal_state"], "regression_pass")
        evidence = payload["evidence"]
        self.assertEqual(evidence["schema_version"], "0.2.0")
        self.assertEqual(evidence["source_device"]["role"], "golden")
        self.assertEqual(evidence["target_device"]["role"], "dut")

    def test_replay_evidence_has_no_redundant_identity_fields(self) -> None:
        # v0.2.0 contract: identity lives only in source_device/target_device.
        result = CliRunner().invoke(main, ["scenario", "run", "--replay", "--json"])
        evidence = json.loads(result.output)["evidence"]
        for removed in (
            "device_id",
            "serial",
            "firmware_version",
            "bitstream_version",
            "source_device_role",
            "target_device_role",
        ):
            self.assertNotIn(removed, evidence, f"{removed} should not be at top level")

    def test_replay_outcome_and_evidence_match_contract_schemas(self) -> None:
        result = CliRunner().invoke(main, ["scenario", "run", "--replay", "--json"])

        self.assertEqual(result.exit_code, 0, result.output)
        payload = json.loads(result.output)
        evidence_schema = json.loads(
            (ROOT / "scenarios" / "schemas" / "evidence.schema.json").read_text(encoding="utf-8")
        )
        outcome_schema = json.loads(
            (ROOT / "scenarios" / "schemas" / "outcome.schema.json").read_text(encoding="utf-8")
        )

        jsonschema.validate(instance=payload["evidence"], schema=evidence_schema)
        outcome_without_ref = {
            **outcome_schema,
            "properties": {
                **outcome_schema["properties"],
                "evidence": {"type": "object"},
            },
        }
        jsonschema.validate(instance=payload, schema=outcome_without_ref)


if __name__ == "__main__":
    unittest.main()
