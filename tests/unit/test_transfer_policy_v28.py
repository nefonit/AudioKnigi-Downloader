"""V28 transfer policy behavior and public network import contracts."""

import threading

import pytest

from audioknigi.core import Cancelled
from audioknigi.download import (
    AdaptiveRangeController as PackageController,
    BandwidthLimiter as PackageLimiter,
    SlidingSpeedMeter as PackageMeter,
)
from audioknigi.download.network import (
    AdaptiveRangeController as LegacyController,
    BandwidthLimiter as LegacyLimiter,
    SlidingSpeedMeter as LegacyMeter,
)
from audioknigi.download.transfer_policy import (
    AdaptiveRangeController,
    BandwidthLimiter,
    SlidingSpeedMeter,
)


def test_all_preexisting_transfer_policy_exports_preserve_class_identity():
    from audioknigi.downloader import (
        AdaptiveRangeController as FacadeController,
        BandwidthLimiter as FacadeLimiter,
        SlidingSpeedMeter as FacadeMeter,
    )

    for aliases in (
        (AdaptiveRangeController, LegacyController, PackageController, FacadeController),
        (BandwidthLimiter, LegacyLimiter, PackageLimiter, FacadeLimiter),
        (SlidingSpeedMeter, LegacyMeter, PackageMeter, FacadeMeter),
    ):
        assert all(alias is aliases[0] for alias in aliases)


def test_bandwidth_rate_limit_can_be_disabled_and_reenabled():
    limiter = BandwidthLimiter(0)
    limiter.consume(64 * 1024, None)
    limiter.set_rate(1024)
    assert limiter.rate == 1024
    assert limiter.capacity >= 64 * 1024
    limiter.set_rate(0)
    assert limiter.rate == 0
    assert limiter.tokens == 0
    limiter.consume(1000, None)


def test_bandwidth_wait_honors_pre_cancelled_event_without_sleeping():
    limiter = BandwidthLimiter(1)
    limiter.tokens = 0
    event = threading.Event()
    event.set()
    with pytest.raises(Cancelled, match="Операция отменена пользователем"):
        limiter.consume(1, event)


def test_adaptive_worker_count_reacts_to_persistent_slow_samples(monkeypatch):
    from audioknigi.download import transfer_policy

    clock = [100.0]
    monkeypatch.setattr(transfer_policy.time, "monotonic", lambda: clock[0])
    policy = AdaptiveRangeController(8, adaptive=True, min_per_worker=100)
    assert policy.current_workers() == 8
    clock[0] = 103.0
    for _ in range(5):
        policy.observe(10.0)
    assert policy.current_workers() == 4


def test_adaptive_worker_count_recovers_from_consistently_fast_samples(monkeypatch):
    from audioknigi.download import transfer_policy

    clock = [100.0]
    monkeypatch.setattr(transfer_policy.time, "monotonic", lambda: clock[0])
    policy = AdaptiveRangeController(8, adaptive=True, min_per_worker=100)
    clock[0] = 103.0
    for _ in range(5):
        policy.observe(10)
    assert policy.current_workers() == 4
    clock[0] = 108.0
    for _ in range(8):
        policy.observe(800)
    assert policy.current_workers() == 8


def test_adaptive_mode_can_be_disabled():
    policy = AdaptiveRangeController(8, adaptive=False)
    for _ in range(20):
        assert policy.observe(0.0) == 8


def test_sliding_speed_meter_clears_previous_samples_on_counter_reset(monkeypatch):
    from audioknigi.download import transfer_policy

    clock = [100.0]
    monkeypatch.setattr(transfer_policy.time, "monotonic", lambda: clock[0])
    meter = SlidingSpeedMeter(window_seconds=5)
    assert meter.update(0) == 0.0
    clock[0] = 101.0
    assert meter.update(200) == pytest.approx(200.0)
    clock[0] = 102.0
    assert meter.update(20) == 0.0
    clock[0] = 103.0
    assert meter.update(120) == pytest.approx(100.0)
