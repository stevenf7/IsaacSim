# SPDX-FileCopyrightText: Copyright (c) 2022-2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
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

"""Tests for the trajectory optimizer example GUI (sliders + C-space planning)."""

from unittest.mock import patch

import isaacsim.robot_motion.cumotion.examples.trajectory_optimizer.scenario as traj_opt_scenario
import numpy as np
import omni.kit.app
import omni.kit.test
from isaacsim.robot_motion.cumotion import TrajectoryOptimizer
from isaacsim.robot_motion.cumotion.examples.trajectory_optimizer.ui_builder import UIBuilder

from .gui_test_support import assert_xyz_and_unit_quaternion_wxyz, wait_until


class TestTrajectoryOptimizerGui(omni.kit.test.AsyncTestCase):
    """Test suite for the trajectory optimizer example GUI."""

    async def setUp(self):
        """Set up the UI builder before each test."""
        await omni.kit.app.get_app().next_update_async()
        self.ui_builder = UIBuilder()
        self.ui_builder.build_ui()
        await omni.kit.app.get_app().next_update_async()

    async def tearDown(self):
        """Clean up the UI builder after each test."""
        self.ui_builder.cleanup()
        await omni.kit.app.get_app().next_update_async()

    async def test_widgets_built(self):
        """Verify that all expected widgets are created."""
        self.assertIsNotNone(self.ui_builder._load_btn)
        self.assertIsNotNone(self.ui_builder._to_cspace_btn)

    async def _load_until_sliders(self) -> None:
        """Trigger load and wait until joint sliders are built.

        Only waits for ``_joint_slider_models`` to be populated (requires
        ``_cumotion_robot`` only, not the full USD load).  Tests that need
        ``_articulation`` (e.g. task-space tests) must call
        :meth:`_load_until_articulation_ready` instead.
        """
        self.ui_builder._load_btn.trigger_click()
        ok = await wait_until(
            lambda: len(self.ui_builder._joint_slider_models) > 0,
            timeout_sec=120.0,
        )
        self.assertTrue(ok, "Timed out waiting for joint sliders")

    async def _load_until_articulation_ready(self) -> None:
        """Trigger load and wait until both sliders and articulation are ready.

        Waits for the full USD scene load (sets ``_articulation``), needed
        when the test exercises code paths that call
        ``_articulation.get_world_poses()`` or similar.
        """
        await self._load_until_sliders()
        ok = await wait_until(
            lambda: self.ui_builder._scenario._articulation is not None,
            timeout_sec=120.0,
        )
        self.assertTrue(ok, "Timed out waiting for articulation to be ready")

    async def test_cspace_button_passes_slider_joint_values(self):
        """Test that slider values are correctly passed to C-space planning."""
        await self._load_until_sliders()

        models = self.ui_builder._joint_slider_models
        self.assertGreater(len(models), 0)

        deltas = [0.05 * (i + 1) for i in range(len(models))]
        expected: list[float] = []
        for i, m in enumerate(models):
            base = m.get_value_as_float()
            new_val = base + deltas[i]
            m.set_value(float(new_val))
            expected.append(float(m.get_value_as_float()))

        captured: dict[str, object] = {}

        def record_and_skip_plan(q_target=None):
            captured["q"] = q_target
            return

        with patch.object(self.ui_builder._scenario, "plan_to_cspace_target", side_effect=record_and_skip_plan):
            self.ui_builder._on_to_cspace_target_btn()

        self.assertIn("q", captured)
        q = captured["q"]
        self.assertIsNotNone(q)
        got = np.asarray(q, dtype=np.float64)
        want = np.asarray(expected, dtype=np.float64)
        np.testing.assert_allclose(got, want, rtol=0.0, atol=1e-5)

    async def test_task_space_button_passes_cube_position_and_orientation(self):
        """World-frame pose from the target cube is a 3-vector and unit quaternion before base-frame conversion."""
        await self._load_until_articulation_ready()

        captured: dict[str, object] = {}
        _orig_convert = traj_opt_scenario.isaac_sim_to_cumotion_pose

        def capture_world_pose(*args, **kwargs):
            captured["position_world"] = kwargs["position_world_to_target"]
            captured["orientation_world"] = kwargs["orientation_world_to_target"]
            return _orig_convert(*args, **kwargs)

        def skip_plan_to_goal(self, q_initial, goal):
            return None

        with patch.object(TrajectoryOptimizer, "plan_to_goal", skip_plan_to_goal):
            with patch.object(traj_opt_scenario, "isaac_sim_to_cumotion_pose", side_effect=capture_world_pose):
                self.ui_builder._on_to_task_space_target_btn()

        self.assertIn("position_world", captured)
        self.assertIn("orientation_world", captured)
        assert_xyz_and_unit_quaternion_wxyz(captured["position_world"], captured["orientation_world"])
