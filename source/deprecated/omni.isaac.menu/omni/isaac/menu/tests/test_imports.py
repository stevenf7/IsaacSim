# SPDX-FileCopyrightText: Copyright (c) 2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: LicenseRef-NvidiaProprietary
#
# NVIDIA CORPORATION, its affiliates and licensors retain all intellectual
# property and proprietary rights in and to this material, related
# documentation and any modifications thereto. Any use, reproduction,
# disclosure or distribution of this material and related documentation
# without an express license agreement from NVIDIA CORPORATION or
# its affiliates is strictly prohibited.

import omni.kit.test


class TestImports(omni.kit.test.AsyncTestCase):
    async def setUp(self):
        pass

    async def tearDown(self):
        pass

    async def test_imports_for_omni_isaac_menu_extension(self):
        # Testing all imports from original extension tests
        from pathlib import Path

        import carb
        import carb.settings
        import carb.tokens
        import omni.kit.commands
        import omni.usd
        from omni.isaac.core.objects import DynamicCuboid
        from omni.isaac.core.utils.prims import get_prim_path
        from omni.isaac.core.utils.stage import clear_stage, create_new_stage, traverse_stage
        from omni.isaac.core.utils.viewports import set_camera_view
        from omni.isaac.range_sensor import _range_sensor
        from omni.isaac.sensor import _sensor
        from omni.kit.mainwindow import get_main_window
        from pxr import UsdGeom, UsdPhysics

        print("All imports successful for extension: omni.isaac.menu")
