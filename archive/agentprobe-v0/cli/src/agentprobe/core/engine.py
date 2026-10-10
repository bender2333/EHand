from __future__ import annotations

from agentprobe.daemon.replay_transport import ReplayTransport
from agentprobe.models.outcome import Outcome


def run_replay_scenario() -> Outcome:
    return ReplayTransport().run()
