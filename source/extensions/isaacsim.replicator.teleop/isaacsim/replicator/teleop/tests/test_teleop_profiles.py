# SPDX-FileCopyrightText: Copyright (c) 2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
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

"""Tests for unified teleop profile I/O."""

from __future__ import annotations

import os
from tempfile import TemporaryDirectory

import omni.kit.test
import yaml
from isaacsim.replicator.teleop import (
    BUILTIN_GRASP_CONFIG_SCHEME,
    BimanualControllerProfile,
    ControllerSideProfile,
    GraspControllerProfile,
    GraspSideProfile,
    LocomotionProfile,
    TeleopProfile,
    TeleopSettingsProfile,
    get_builtin_grasp_configs,
    load_grasp_config,
    load_teleop_profile,
    normalize_grasp_config_path,
    save_teleop_profile,
)


class TestTeleopProfiles(omni.kit.test.AsyncTestCase):
    """Verify teleop profiles round-trip through YAML."""

    async def test_teleop_profile_round_trip(self):
        profile = TeleopProfile(
            session=TeleopSettingsProfile(
                coordinate_system="raw",
                tracking_space_enabled=True,
                tracking_space_path="/World/TeleopSpace",
                marker_scale=0.08,
                anchor_x=1.0,
                anchor_y=2.0,
                anchor_z=3.0,
                anchor_rotation_mode="follow_prim_smoothed",
                anchor_smoothing=0.75,
                anchor_fixed_height=False,
            ),
            floating=BimanualControllerProfile(
                left=ControllerSideProfile(
                    enabled=True,
                    settings={
                        "prim_path": "/World/FloatingLeft",
                        "pos_kp": 12.0,
                        "target_rot_z_deg": 90,
                    },
                ),
                right=ControllerSideProfile(
                    enabled=False,
                    settings={"prim_path": "/World/FloatingRight"},
                ),
            ),
            ik=BimanualControllerProfile(
                left=ControllerSideProfile(
                    enabled=True,
                    settings={
                        "robot_path": "/World/RobotLeft",
                        "ee_link": "tool0",
                        "solver": "position-based",
                        "method": "svd",
                    },
                ),
                right=ControllerSideProfile(),
            ),
            grasp=GraspControllerProfile(
                left=GraspSideProfile(
                    enabled=True,
                    prim_path="/World/HandLeft",
                    config_path="builtin://xarm_grasp",
                ),
                right=GraspSideProfile(),
            ),
            locomotion=LocomotionProfile(
                enabled=True,
                settings={
                    "prim_path": "/World/Base",
                    "linear_speed": 1.25,
                    "angular_speed": 0.75,
                },
            ),
        )

        with TemporaryDirectory() as tmp_dir:
            profile_path = f"{tmp_dir}/teleop_profile.yaml"
            ok, message = save_teleop_profile(profile_path, profile)
            self.assertTrue(ok, message)

            loaded, errors = load_teleop_profile(profile_path)
            self.assertIsNotNone(loaded)
            self.assertEqual(errors, [])
            assert loaded is not None

            self.assertEqual(loaded.session.coordinate_system, "raw")
            self.assertEqual(loaded.session.tracking_space_path, "/World/TeleopSpace")
            self.assertAlmostEqual(loaded.session.marker_scale, 0.08)
            self.assertTrue(loaded.floating.left.enabled)
            self.assertEqual(loaded.floating.left.settings["prim_path"], "/World/FloatingLeft")
            self.assertEqual(loaded.ik.left.settings["ee_link"], "tool0")
            self.assertTrue(loaded.grasp.left.enabled)
            self.assertEqual(loaded.grasp.left.prim_path, "/World/HandLeft")
            self.assertEqual(loaded.grasp.left.config_path, "builtin://xarm_grasp")
            self.assertEqual(loaded.locomotion.settings["prim_path"], "/World/Base")

    async def test_extra_keys_are_ignored(self):
        """Files with unknown keys (e.g. from a newer schema) load without error."""

        data = {
            "future_field": True,
            "session": {"coordinate_system": "raw", "unknown_knob": 42},
            "floating": {"left": {"enabled": True, "settings": {"prim_path": "/A"}}},
        }
        with TemporaryDirectory() as tmp_dir:
            path = os.path.join(tmp_dir, "extra.yaml")
            with open(path, "w") as f:
                yaml.dump(data, f)

            loaded, errors = load_teleop_profile(path)
            self.assertEqual(errors, [])
            self.assertIsNotNone(loaded)
            assert loaded is not None
            self.assertEqual(loaded.session.coordinate_system, "raw")
            self.assertTrue(loaded.floating.left.enabled)
            self.assertFalse(loaded.locomotion.enabled)

    async def test_missing_keys_use_defaults(self):
        """A minimal YAML file still produces a fully populated profile."""

        data = {"locomotion": {"enabled": True}}
        with TemporaryDirectory() as tmp_dir:
            path = os.path.join(tmp_dir, "minimal.yaml")
            with open(path, "w") as f:
                yaml.dump(data, f)

            loaded, errors = load_teleop_profile(path)
            self.assertEqual(errors, [])
            self.assertIsNotNone(loaded)
            assert loaded is not None
            self.assertTrue(loaded.locomotion.enabled)
            self.assertFalse(loaded.floating.left.enabled)
            self.assertEqual(loaded.session.anchor_x, 0.0)

    async def test_builtin_grasp_config_paths_are_portable(self):
        """Built-in grasp configs should round-trip through a stable symbolic URI."""

        builtin_configs = dict(get_builtin_grasp_configs())
        self.assertIn("xarm_grasp", builtin_configs)
        builtin_uri = builtin_configs["xarm_grasp"]
        self.assertEqual(builtin_uri, "builtin://xarm_grasp")
        self.assertTrue(builtin_uri.startswith(BUILTIN_GRASP_CONFIG_SCHEME))

        normalized = normalize_grasp_config_path("/tmp/ext/data/grasp_configs/xarm_grasp.yaml")
        self.assertEqual(normalized, builtin_uri)

        config, errors = load_grasp_config(builtin_uri)
        self.assertEqual(errors, [])
        self.assertIsNotNone(config)
        assert config is not None
        self.assertEqual(config.name, "xarm_grasp")
