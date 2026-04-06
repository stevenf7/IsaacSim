# SPDX-FileCopyrightText: Copyright (c) 2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Tests for simulation time drift behavior in the production onPhysicsStep code path.

These tests verify that simulation time derived from integer step count and
steps-per-second (via IPhysicsSimulation APIs) does not accumulate floating-point
drift over many physics steps.
"""

import os
import unittest

import omni.kit.app
import omni.kit.test
import omni.timeline
from isaacsim.core.experimental.utils.stage import create_new_stage_async
from isaacsim.core.simulation_manager import SimulationManager


class TestSimulationTimeDrift(omni.kit.test.AsyncTestCase):
    """Test simulation time drift."""

    async def setUp(self):
        """Set up test environment."""
        super().setUp()
        await create_new_stage_async()
        SimulationManager.set_physics_dt(1.0 / 60.0)
        await omni.kit.app.get_app().next_update_async()

    async def tearDown(self):
        """Tear down test environment."""
        timeline = omni.timeline.get_timeline_interface()
        timeline.stop()
        await omni.kit.app.get_app().next_update_async()
        super().tearDown()

    async def test_simulation_time_drift_after_many_steps(self):
        """Verify simulation time stays accurate after many physics steps.

        With dt=1/60 and 12000 steps (200 seconds of sim time), the old
        float-additive approach would accumulate ~10us of drift. The integer
        step count approach should keep error well below 1us.
        """
        timeline = omni.timeline.get_timeline_interface()
        timeline.play()
        await omni.kit.app.get_app().next_update_async()

        # Step physics 12000 times (~200 seconds of sim time at 60Hz).
        # The old float-additive approach (g_simulationTime += timeElapsed) accumulates
        # ~8.69e-10 s of bias per step from the float representation of 1/60.
        # After 12000 steps that's ~10.4 us of drift, which exceeds the 1 us threshold.
        # The integer-rate approach (stepCount / stepsPerSecond) keeps error sub-microsecond.
        initial_steps = SimulationManager.get_num_physics_steps()
        SimulationManager.step(steps=12000, update_fabric=False)

        total_steps = SimulationManager.get_num_physics_steps()
        sim_time = SimulationManager.get_simulation_time()
        expected_time = total_steps / 60.0

        error = abs(sim_time - expected_time)
        self.assertLess(error, 1e-6, f"Drift of {error * 1e6:.3f} us exceeds 1 us after {total_steps} steps")

    async def test_simulation_time_resets_on_stop(self):
        """Verify simulation time resets to zero on stop."""
        timeline = omni.timeline.get_timeline_interface()
        timeline.play()
        await omni.kit.app.get_app().next_update_async()

        SimulationManager.step(steps=100, update_fabric=False)
        self.assertGreater(SimulationManager.get_simulation_time(), 0.0)

        timeline.stop()
        await omni.kit.app.get_app().next_update_async()
        self.assertEqual(SimulationManager.get_simulation_time(), 0.0)

    async def test_monotonic_time_persists_across_stop_start(self):
        """Verify monotonic simulation time does not reset on stop/start."""
        timeline = omni.timeline.get_timeline_interface()
        iface = SimulationManager._simulation_manager_interface

        # First run
        timeline.play()
        await omni.kit.app.get_app().next_update_async()
        SimulationManager.step(steps=100, update_fabric=False)
        mono_after_first_run = iface.get_simulation_time_monotonic()
        self.assertGreater(mono_after_first_run, 0.0)

        # Stop and restart
        timeline.stop()
        await omni.kit.app.get_app().next_update_async()
        timeline.play()
        await omni.kit.app.get_app().next_update_async()

        # Monotonic time should be >= what it was before stop
        mono_after_restart = iface.get_simulation_time_monotonic()
        self.assertGreaterEqual(mono_after_restart, mono_after_first_run)

        # Step more and verify it keeps increasing
        SimulationManager.step(steps=100, update_fabric=False)
        mono_final = iface.get_simulation_time_monotonic()
        self.assertGreater(mono_final, mono_after_first_run)
