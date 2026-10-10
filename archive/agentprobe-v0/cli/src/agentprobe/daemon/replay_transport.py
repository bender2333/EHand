from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from agentprobe.models.outcome import Outcome, make_outcome


DEFAULT_REPLAY_FIXTURE = (
    Path(__file__).resolve().parents[4]
    / "scenarios"
    / "replay"
    / "nominal"
    / "self_hosting_replay.json"
)


class ReplayTransport:
    """No-hardware transport that replays canonical evidence fixtures."""

    def __init__(self, fixture_path: Path = DEFAULT_REPLAY_FIXTURE) -> None:
        self.fixture_path = fixture_path

    def run(self) -> Outcome:
        data = self._load_fixture()
        evidence = data["evidence"]
        return make_outcome(
            status=data["status"],
            terminal_state=data["terminal_state"],
            evidence=evidence,
            verdict=data["verdict"],
            confidence=data["confidence"],
            next_action=data["next_action"],
        )

    def _load_fixture(self) -> dict[str, Any]:
        with self.fixture_path.open("r", encoding="utf-8") as fixture:
            data = json.load(fixture)
        self._validate_minimum_contract(data)
        return data

    @staticmethod
    def _validate_minimum_contract(data: dict[str, Any]) -> None:
        required = {"status", "terminal_state", "evidence", "verdict", "confidence", "next_action"}
        missing = sorted(required - data.keys())
        if missing:
            raise ValueError(f"Replay outcome missing required fields: {', '.join(missing)}")

        evidence = data["evidence"]
        evidence_required = {
            "schema_version",
            "run_id",
            "trace_id",
            "source_device",
            "target_device",
            "connection_topology_id",
            "build_result",
            "flash_result",
            "capture_result",
            "diagnosis_result",
            "regression_result",
            "verdict",
            "confidence",
        }
        missing_evidence = sorted(evidence_required - evidence.keys())
        if missing_evidence:
            raise ValueError(
                "Replay evidence missing required fields: " + ", ".join(missing_evidence)
            )
