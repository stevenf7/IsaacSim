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

"""Tests for CollisionSphereEditor."""

import isaacsim.core.experimental.utils.prim as prim_utils
import isaacsim.core.experimental.utils.stage as stage_utils
import numpy as np
import omni.kit.test
from isaacsim.robot_setup.xrdf_editor.collision_sphere_editor import CollisionSphereEditor

_ROBOT_PATH = "/World/robot"
_LINK1_PATH = "/World/robot/link1"
_LINK2_PATH = "/World/robot/link2"


class TestCollisionSphereEditor(omni.kit.test.AsyncTestCase):
    """Test CollisionSphereEditor API."""

    async def setUp(self):
        super().setUp()
        await stage_utils.create_new_stage_async()
        stage_utils.define_prim(_ROBOT_PATH, "Xform")
        stage_utils.define_prim(_LINK1_PATH, "Xform")
        stage_utils.define_prim(_LINK2_PATH, "Xform")
        self.editor = CollisionSphereEditor()

    async def tearDown(self):
        self.editor.on_shutdown()
        super().tearDown()

    # -------------------------------------------------------------------------
    # add_sphere / delete_sphere
    # -------------------------------------------------------------------------

    async def test_add_sphere_returns_valid_path(self):
        sphere_path = self.editor.add_sphere(_LINK1_PATH, np.array([0.1, 0.0, 0.0]), 0.05)
        self.assertIsNotNone(sphere_path)
        self.assertIn(sphere_path, self.editor.path_2_spheres)
        prim = prim_utils.get_prim_at_path(sphere_path)
        self.assertTrue(prim and prim.IsValid())

    async def test_add_sphere_path_nested_under_link(self):
        sphere_path = self.editor.add_sphere(_LINK1_PATH, np.zeros(3), 0.05)
        self.assertTrue(sphere_path.startswith(_LINK1_PATH))

    async def test_add_multiple_spheres_unique_paths(self):
        path1 = self.editor.add_sphere(_LINK1_PATH, np.zeros(3), 0.05)
        path2 = self.editor.add_sphere(_LINK1_PATH, np.array([0.1, 0.0, 0.0]), 0.05)
        self.assertNotEqual(path1, path2)
        self.assertEqual(len(self.editor.path_2_spheres), 2)

    async def test_delete_sphere_removes_from_dict(self):
        sphere_path = self.editor.add_sphere(_LINK1_PATH, np.zeros(3), 0.05)
        self.editor.delete_sphere(sphere_path)
        self.assertNotIn(sphere_path, self.editor.path_2_spheres)

    async def test_delete_sphere_removes_prim(self):
        sphere_path = self.editor.add_sphere(_LINK1_PATH, np.zeros(3), 0.05)
        self.editor.delete_sphere(sphere_path)
        prim = prim_utils.get_prim_at_path(sphere_path)
        self.assertFalse(prim and prim.IsValid())

    async def test_delete_nonexistent_sphere_is_safe(self):
        # Should not raise even when the path is not tracked.
        self.editor.delete_sphere("/World/robot/link1/nonexistent_sphere")

    # -------------------------------------------------------------------------
    # clear_spheres / clear_link_spheres
    # -------------------------------------------------------------------------

    async def test_clear_spheres_removes_all(self):
        self.editor.add_sphere(_LINK1_PATH, np.zeros(3), 0.05)
        self.editor.add_sphere(_LINK2_PATH, np.ones(3) * 0.1, 0.05)
        self.editor.clear_spheres()
        self.assertEqual(len(self.editor.path_2_spheres), 0)

    async def test_clear_spheres_on_empty_editor_is_safe(self):
        self.editor.clear_spheres()
        self.assertEqual(len(self.editor.path_2_spheres), 0)

    async def test_clear_link_spheres_removes_only_target_link(self):
        self.editor.add_sphere(_LINK1_PATH, np.zeros(3), 0.05)
        self.editor.add_sphere(_LINK1_PATH, np.array([0.1, 0.0, 0.0]), 0.05)
        link2_path = self.editor.add_sphere(_LINK2_PATH, np.zeros(3), 0.05)
        self.editor.clear_link_spheres(_LINK1_PATH)
        remaining = list(self.editor.path_2_spheres.keys())
        self.assertEqual(remaining, [link2_path])

    # -------------------------------------------------------------------------
    # get_sphere_names_by_link
    # -------------------------------------------------------------------------

    async def test_get_sphere_names_by_link_returns_correct_count(self):
        self.editor.add_sphere(_LINK1_PATH, np.zeros(3), 0.05)
        self.editor.add_sphere(_LINK1_PATH, np.array([0.1, 0.0, 0.0]), 0.05)
        self.editor.add_sphere(_LINK2_PATH, np.zeros(3), 0.05)
        names = self.editor.get_sphere_names_by_link(_LINK1_PATH)
        self.assertEqual(len(names), 2)

    async def test_get_sphere_names_by_link_are_relative(self):
        self.editor.add_sphere(_LINK1_PATH, np.zeros(3), 0.05)
        names = self.editor.get_sphere_names_by_link(_LINK1_PATH)
        for name in names:
            self.assertTrue(name.startswith("/"), f"Expected relative path starting with '/', got: {name}")

    async def test_get_sphere_names_by_link_empty_when_none(self):
        self.editor.add_sphere(_LINK1_PATH, np.zeros(3), 0.05)
        names = self.editor.get_sphere_names_by_link(_LINK2_PATH)
        self.assertEqual(names, [])

    # -------------------------------------------------------------------------
    # scale_spheres
    # -------------------------------------------------------------------------

    async def test_scale_spheres_doubles_radius(self):
        sphere_path = self.editor.add_sphere(_LINK1_PATH, np.zeros(3), 0.1)
        self.editor.scale_spheres(_LINK1_PATH, 2.0)
        radius = self.editor.path_2_spheres[sphere_path].get_radii().numpy()[0]
        self.assertAlmostEqual(radius, 0.2, places=4)

    async def test_scale_spheres_only_affects_matching_prefix(self):
        path1 = self.editor.add_sphere(_LINK1_PATH, np.zeros(3), 0.1)
        path2 = self.editor.add_sphere(_LINK2_PATH, np.zeros(3), 0.1)
        self.editor.scale_spheres(_LINK1_PATH, 3.0)
        radius1 = self.editor.path_2_spheres[path1].get_radii().numpy()[0]
        radius2 = self.editor.path_2_spheres[path2].get_radii().numpy()[0]
        self.assertAlmostEqual(radius1, 0.3, places=4)
        self.assertAlmostEqual(radius2, 0.1, places=4)

    async def test_scale_spheres_records_operation(self):
        self.editor.add_sphere(_LINK1_PATH, np.zeros(3), 0.1)
        ops_before = len(self.editor._operations)
        self.editor.scale_spheres(_LINK1_PATH, 2.0)
        self.assertEqual(len(self.editor._operations), ops_before + 1)

    # -------------------------------------------------------------------------
    # undo / redo
    # -------------------------------------------------------------------------

    async def test_undo_add_removes_sphere(self):
        sphere_path = self.editor.add_sphere(_LINK1_PATH, np.zeros(3), 0.05)
        self.editor.undo()
        self.assertNotIn(sphere_path, self.editor.path_2_spheres)
        prim = prim_utils.get_prim_at_path(sphere_path)
        self.assertFalse(prim and prim.IsValid())

    async def test_undo_add_populates_redo_stack(self):
        self.editor.add_sphere(_LINK1_PATH, np.zeros(3), 0.05)
        self.editor.undo()
        self.assertEqual(len(self.editor._redo), 1)

    async def test_redo_after_undo_add_restores_sphere(self):
        sphere_path = self.editor.add_sphere(_LINK1_PATH, np.zeros(3), 0.05)
        self.editor.undo()
        self.editor.redo()
        self.assertIn(sphere_path, self.editor.path_2_spheres)
        prim = prim_utils.get_prim_at_path(sphere_path)
        self.assertTrue(prim and prim.IsValid())

    async def test_undo_scale_restores_original_radius(self):
        sphere_path = self.editor.add_sphere(_LINK1_PATH, np.zeros(3), 0.1)
        self.editor.scale_spheres(_LINK1_PATH, 3.0)
        self.editor.undo()
        radius = self.editor.path_2_spheres[sphere_path].get_radii().numpy()[0]
        self.assertAlmostEqual(radius, 0.1, places=4)

    async def test_undo_clear_spheres_restores_sphere(self):
        sphere_path = self.editor.add_sphere(_LINK1_PATH, np.zeros(3), 0.05)
        self.editor.clear_spheres()
        self.editor.undo()
        self.assertIn(sphere_path, self.editor.path_2_spheres)
        prim = prim_utils.get_prim_at_path(sphere_path)
        self.assertTrue(prim and prim.IsValid())

    async def test_undo_on_empty_stack_is_safe(self):
        self.editor.undo()
        self.assertEqual(len(self.editor.path_2_spheres), 0)

    async def test_redo_on_empty_stack_is_safe(self):
        self.editor.redo()
        self.assertEqual(len(self.editor.path_2_spheres), 0)

    async def test_add_sphere_clears_redo_stack(self):
        self.editor.add_sphere(_LINK1_PATH, np.zeros(3), 0.05)
        self.editor.undo()
        self.assertEqual(len(self.editor._redo), 1)
        self.editor.add_sphere(_LINK1_PATH, np.array([0.1, 0.0, 0.0]), 0.05)
        # New add should clear the redo stack
        self.assertEqual(len(self.editor._redo), 0)

    # -------------------------------------------------------------------------
    # interpolate_spheres
    # -------------------------------------------------------------------------

    async def test_interpolate_spheres_creates_correct_count(self):
        path1 = self.editor.add_sphere(_LINK1_PATH, np.array([0.0, 0.0, 0.0]), 0.05)
        path2 = self.editor.add_sphere(_LINK1_PATH, np.array([0.6, 0.0, 0.0]), 0.05)
        self.editor.interpolate_spheres(path1, path2, num_spheres=3)
        self.assertEqual(len(self.editor.path_2_spheres), 5)  # 2 original + 3 interpolated

    async def test_interpolate_spheres_positions_between_endpoints(self):
        p0 = np.array([0.0, 0.0, 0.0])
        p1 = np.array([1.0, 0.0, 0.0])
        path1 = self.editor.add_sphere(_LINK1_PATH, p0, 0.05)
        path2 = self.editor.add_sphere(_LINK1_PATH, p1, 0.05)
        self.editor.interpolate_spheres(path1, path2, num_spheres=1)
        # Collect interpolated sphere paths (those that are not path1 or path2)
        interp_paths = [p for p in self.editor.path_2_spheres if p not in (path1, path2)]
        self.assertEqual(len(interp_paths), 1)
        interp_sphere = self.editor.path_2_spheres[interp_paths[0]]
        center = interp_sphere.get_local_poses()[0].numpy()[0]
        # Midpoint should be between 0 and 1 on X axis
        self.assertGreater(center[0], 0.0)
        self.assertLess(center[0], 1.0)

    # -------------------------------------------------------------------------
    # set_sphere_colors
    # -------------------------------------------------------------------------

    async def test_set_sphere_colors_updates_filter(self):
        self.editor.set_sphere_colors(_LINK1_PATH)
        self.assertEqual(self.editor.filter, _LINK1_PATH)

    async def test_set_sphere_colors_updates_color_in(self):
        color = np.array([1.0, 0.0, 0.0])
        self.editor.set_sphere_colors(_LINK1_PATH, color_in=color)
        np.testing.assert_array_equal(self.editor.filter_in_sphere_color, color)

    async def test_set_sphere_colors_updates_color_out(self):
        color = np.array([0.0, 1.0, 0.0])
        self.editor.set_sphere_colors(_LINK1_PATH, color_out=color)
        np.testing.assert_array_equal(self.editor.filter_out_sphere_color, color)

    # -------------------------------------------------------------------------
    # write_spheres_to_dict
    # -------------------------------------------------------------------------

    async def test_write_spheres_to_dict_populates_link_key(self):
        self.editor.add_sphere(_LINK1_PATH, np.array([0.1, 0.2, 0.3]), 0.05)
        link_to_spheres = {}
        self.editor.write_spheres_to_dict(_ROBOT_PATH, link_to_spheres)
        self.assertIn("link1", link_to_spheres)

    async def test_write_spheres_to_dict_correct_radius(self):
        self.editor.add_sphere(_LINK1_PATH, np.zeros(3), 0.07)
        link_to_spheres = {}
        self.editor.write_spheres_to_dict(_ROBOT_PATH, link_to_spheres)
        sphere_data = link_to_spheres["link1"][0]
        self.assertAlmostEqual(sphere_data["radius"], 0.07, places=2)

    async def test_write_spheres_to_dict_multiple_links(self):
        self.editor.add_sphere(_LINK1_PATH, np.zeros(3), 0.05)
        self.editor.add_sphere(_LINK2_PATH, np.zeros(3), 0.05)
        link_to_spheres = {}
        self.editor.write_spheres_to_dict(_ROBOT_PATH, link_to_spheres)
        self.assertIn("link1", link_to_spheres)
        self.assertIn("link2", link_to_spheres)

    # -------------------------------------------------------------------------
    # load_xrdf_spheres
    # -------------------------------------------------------------------------

    async def test_load_xrdf_spheres_v1_creates_spheres(self):
        parsed = {
            "format_version": 1.0,
            "collision": {"geometry": "default"},
            "geometry": {
                "default": {
                    "spheres": {
                        "link1": [{"center": [0.0, 0.0, 0.1], "radius": 0.05}],
                    }
                }
            },
        }
        self.editor.load_xrdf_spheres(_ROBOT_PATH, parsed)
        self.assertEqual(len(self.editor.path_2_spheres), 1)
        sphere_path = next(iter(self.editor.path_2_spheres))
        self.assertTrue(sphere_path.startswith(_LINK1_PATH))

    async def test_load_xrdf_spheres_v2_creates_spheres(self):
        parsed = {
            "format_version": 2.0,
            "world_collision": {"geometry": "default"},
            "geometry": {
                "default": {
                    "spheres": {
                        "link1": [{"center": [0.0, 0.0, 0.1], "radius": 0.05}],
                        "link2": [{"center": [0.1, 0.0, 0.0], "radius": 0.04}],
                    }
                }
            },
        }
        self.editor.load_xrdf_spheres(_ROBOT_PATH, parsed)
        self.assertEqual(len(self.editor.path_2_spheres), 2)

    async def test_load_xrdf_spheres_clears_existing_spheres(self):
        self.editor.add_sphere(_LINK1_PATH, np.zeros(3), 0.05)
        parsed = {
            "format_version": 1.0,
            "collision": {"geometry": "default"},
            "geometry": {
                "default": {
                    "spheres": {
                        "link2": [{"center": [0.1, 0.0, 0.0], "radius": 0.04}],
                    }
                }
            },
        }
        self.editor.load_xrdf_spheres(_ROBOT_PATH, parsed)
        # Only the freshly loaded sphere should remain
        self.assertEqual(len(self.editor.path_2_spheres), 1)
        sphere_path = next(iter(self.editor.path_2_spheres))
        self.assertTrue(sphere_path.startswith(_LINK2_PATH))

    async def test_load_xrdf_spheres_resets_undo_history(self):
        self.editor.add_sphere(_LINK1_PATH, np.zeros(3), 0.05)
        parsed = {
            "format_version": 1.0,
            "collision": {"geometry": "default"},
            "geometry": {
                "default": {
                    "spheres": {
                        "link1": [{"center": [0.0, 0.0, 0.1], "radius": 0.05}],
                    }
                }
            },
        }
        self.editor.load_xrdf_spheres(_ROBOT_PATH, parsed)
        # After load, only the single ADD operation from the load should exist
        self.assertEqual(len(self.editor._operations), 1)
        self.assertEqual(self.editor._operations[0][0], "ADD")

    async def test_load_xrdf_spheres_missing_collision_key_is_safe(self):
        parsed = {"format_version": 1.0}
        self.editor.load_xrdf_spheres(_ROBOT_PATH, parsed)
        self.assertEqual(len(self.editor.path_2_spheres), 0)

    # -------------------------------------------------------------------------
    # on_shutdown
    # -------------------------------------------------------------------------

    async def test_on_shutdown_removes_all_spheres(self):
        self.editor.add_sphere(_LINK1_PATH, np.zeros(3), 0.05)
        self.editor.add_sphere(_LINK2_PATH, np.ones(3) * 0.1, 0.05)
        self.editor.on_shutdown()
        self.assertEqual(len(self.editor.path_2_spheres), 0)

    # -------------------------------------------------------------------------
    # clear_preview
    # -------------------------------------------------------------------------

    async def test_clear_preview_does_not_affect_regular_spheres(self):
        sphere_path = self.editor.add_sphere(_LINK1_PATH, np.zeros(3), 0.05)
        self.editor.clear_preview()
        self.assertIn(sphere_path, self.editor.path_2_spheres)
        self.assertEqual(len(self.editor._preview_spheres), 0)
