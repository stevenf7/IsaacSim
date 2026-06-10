# SPDX-FileCopyrightText: Copyright (c) 2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

"""Tests for the lightweight scoped timer used by NuRec utility tests."""

from __future__ import annotations

import time

import omni.kit.test
from isaacsim.replicator.nurec_utils.metrics.scoped_timer import ScopedTimer


class TestScopedTimer(omni.kit.test.AsyncTestCase):
    """Scoped timer aggregation behavior."""

    async def test_context_records_sample(self) -> None:
        """A scoped timer records one sample under its name."""
        name = f"TestScopedTimer.context.{time.perf_counter_ns()}"

        timer = ScopedTimer(name)
        with timer:
            pass

        num_events, avg_time_ms = ScopedTimer.get_values_for_timer(name)
        self.assertEqual(num_events, 1)
        self.assertGreaterEqual(avg_time_ms, 0.0)
        self.assertIsNotNone(timer.elapsed_time_ms)

    async def test_repeated_name_aggregates_samples(self) -> None:
        """Repeated uses of the same timer name aggregate into one row."""
        name = f"TestScopedTimer.repeated.{time.perf_counter_ns()}"

        with ScopedTimer(name):
            pass
        with ScopedTimer(name):
            pass

        num_events, avg_time_ms = ScopedTimer.get_values_for_timer(name)
        self.assertEqual(num_events, 2)
        self.assertGreaterEqual(avg_time_ms, 0.0)
        self.assertIn(name, ScopedTimer.format_table())

    async def test_disabled_timer_records_nothing(self) -> None:
        """When timing is disabled, a scoped timer is a no-op and records no sample."""
        name = f"TestScopedTimer.disabled.{time.perf_counter_ns()}"

        ScopedTimer.set_enabled(False)
        try:
            with ScopedTimer(name):
                pass
        finally:
            ScopedTimer.set_enabled(True)

        num_events, _ = ScopedTimer.get_values_for_timer(name)
        self.assertEqual(num_events, 0)
