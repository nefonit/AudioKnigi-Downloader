from __future__ import annotations

"""GUI-neutral transfer tuning policies for HTTP and Range downloads.

Keep pure policy decisions here: neither the filesystem resume state nor
HTTP session and response lifecycle belong in this module.
"""

import threading
import time
from collections import deque

from ..core import Cancelled


class BandwidthLimiter:
    """Aggregate token-bucket limiter shared by all HTTP workers."""

    def __init__(self, bytes_per_second=0):
        self.rate = max(0.0, float(bytes_per_second or 0))
        self.capacity = self._capacity(self.rate)
        self.tokens = self.capacity
        self.updated = time.monotonic()
        self.lock = threading.Lock()

    @staticmethod
    def _capacity(rate):
        if rate <= 0:
            return 0.0
        return max(64 * 1024.0, min(rate * 0.35, 2 * 1024 * 1024.0))

    def set_rate(self, bytes_per_second):
        new_rate = max(0.0, float(bytes_per_second or 0))
        with self.lock:
            if abs(new_rate - self.rate) < 1.0:
                return
            self.rate = new_rate
            self.capacity = self._capacity(new_rate)
            self.tokens = min(self.tokens, self.capacity) if new_rate else 0.0
            self.updated = time.monotonic()

    def consume(self, amount, cancel_event):
        remaining = max(0, int(amount or 0))
        while remaining > 0:
            with self.lock:
                if self.rate <= 0:
                    return
                quantum = min(remaining, max(1, int(self.capacity)))
                now = time.monotonic()
                elapsed = max(0.0, now - self.updated)
                self.updated = now
                self.tokens = min(self.capacity, self.tokens + elapsed * self.rate)
                if self.tokens >= quantum:
                    self.tokens -= quantum
                    remaining -= quantum
                    continue
                wait_for = max(0.005, min(0.15, (quantum - self.tokens) / self.rate))
            if cancel_event is not None:
                if cancel_event.wait(wait_for):
                    raise Cancelled("Операция отменена пользователем.")
            else:
                time.sleep(wait_for)


class AdaptiveRangeController:
    """Adjust Range concurrency from observed per-worker throughput."""

    def __init__(self, initial_workers, adaptive=True, min_per_worker=256 * 1024):
        self.initial_workers = max(1, int(initial_workers))
        self.target_workers = self.initial_workers
        self.adaptive = bool(adaptive)
        self.min_per_worker = float(min_per_worker)
        self.slow_samples = 0
        self.fast_samples = 0
        self.last_change = time.monotonic()
        self.lock = threading.Lock()

    def current_workers(self):
        with self.lock:
            return self.target_workers

    def observe(self, aggregate_speed):
        if not self.adaptive:
            return self.current_workers()
        with self.lock:
            target = self.target_workers
            per_worker = float(aggregate_speed or 0.0) / max(1, target)
            now = time.monotonic()
            if per_worker < self.min_per_worker:
                self.slow_samples += 1
                self.fast_samples = 0
            else:
                self.slow_samples = max(0, self.slow_samples - 1)
                if target < self.initial_workers and per_worker >= self.min_per_worker * 1.25:
                    self.fast_samples += 1
                else:
                    self.fast_samples = max(0, self.fast_samples - 1)
            if target > 2 and self.slow_samples >= 5 and now - self.last_change >= 3.0:
                self.target_workers = max(2, target // 2)
                self.slow_samples = 0
                self.fast_samples = 0
                self.last_change = now
            elif target < self.initial_workers and self.fast_samples >= 8 and now - self.last_change >= 4.0:
                self.target_workers = min(self.initial_workers, max(target + 1, target * 2))
                self.slow_samples = 0
                self.fast_samples = 0
                self.last_change = now
            return self.target_workers


class SlidingSpeedMeter:
    def __init__(self, window_seconds=5.0):
        self.window = float(window_seconds)
        self.samples = deque()
        self.lock = threading.Lock()

    def update(self, total_done):
        now = time.monotonic()
        current = int(total_done)
        with self.lock:
            # A resumed/restarted transfer can legitimately reset its aggregate
            # counter.  Do not mix samples from before and after that reset.
            if self.samples and current < self.samples[-1][1]:
                self.samples.clear()
            self.samples.append((now, current))
            cutoff = now - self.window
            while len(self.samples) > 2 and self.samples[0][0] < cutoff:
                self.samples.popleft()
            if len(self.samples) < 2:
                return 0.0
            t0, b0 = self.samples[0]
            t1, b1 = self.samples[-1]
            return max(0.0, (b1 - b0) / max(0.001, t1 - t0))
