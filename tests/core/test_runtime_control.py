import pytest

from pytestflow.core.runtime_control import runtime_control


@pytest.fixture(autouse=True)
def reset_runtime_control_state():
    runtime_control.set_paused(False)
    runtime_control.set_stop_requested(False)
    runtime_control.set_throttle_ms(5.0)
    yield
    runtime_control.set_paused(False)
    runtime_control.set_stop_requested(False)
    runtime_control.set_throttle_ms(5.0)


def test_checkpoint_without_throttle_does_not_sleep(monkeypatch):
    sleep_calls = []

    def fake_sleep(delay_seconds):
        sleep_calls.append(delay_seconds)

    monkeypatch.setattr(runtime_control, "sleep_with_pause", fake_sleep)

    runtime_control.set_throttle_ms(50.0)
    runtime_control.checkpoint_before_step(1, apply_throttle=False)

    assert sleep_calls == []


def test_checkpoint_with_throttle_sleeps(monkeypatch):
    sleep_calls = []

    def fake_sleep(delay_seconds):
        sleep_calls.append(delay_seconds)

    monkeypatch.setattr(runtime_control, "sleep_with_pause", fake_sleep)

    runtime_control.set_throttle_ms(50.0)
    runtime_control.checkpoint_before_step(1, apply_throttle=True)

    assert len(sleep_calls) == 1
