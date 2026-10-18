from ehand.models.sources import PulseSource, SwitchSource


def test_sources() -> None:
    # 1. SwitchSource test
    sw = SwitchSource("sw1", {"initial_state": "open", "bounce_ms": 5.0})
    assert sw.state == "open"
    evs = sw.set_state("closed")
    assert sw.state == "closed"
    assert len(evs) == 2  # bounce event + state changed event
    assert evs[0]["event"] == "bounce_start"
    assert evs[1]["event"] == "state_changed"
    print("SwitchSource OK")

    # 2. PulseSource test
    pulse = PulseSource("pulse1", {"frequency_hz": 1000.0, "duty_cycle": 0.5})
    assert pulse.frequency_hz == 1000.0
    evs = pulse.emit_pulses(5)
    assert len(evs) == 10  # 5 high + 5 low
    assert pulse.total_pulses_emitted == 5
    # Period of 1000Hz is 1000us, high is 500us
    assert evs[1]["time_us"] - evs[0]["time_us"] == 500
    assert evs[2]["time_us"] - evs[1]["time_us"] == 500
    print("PulseSource OK")

    print("ALL SOURCE TESTS PASSED!")


if __name__ == "__main__":
    test_sources()
