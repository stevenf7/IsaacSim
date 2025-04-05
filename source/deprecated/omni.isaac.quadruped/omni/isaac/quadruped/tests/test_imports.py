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

    async def test_imports_for_omni_isaac_quadruped_extension(self):
        # Testing all imports from original extension tests
        import asyncio

        import carb.tokens
        import numpy as np
        import omni.kit.commands
        from omni.isaac.core import World
        from omni.isaac.core.utils.physics import simulate_async
        from omni.isaac.core.utils.prims import get_prim_at_path
        from omni.isaac.core.utils.rotations import quat_to_euler_angles
        from omni.isaac.core.utils.stage import create_new_stage_async
        from omni.isaac.quadruped.robots import AnymalFlatTerrainPolicy, SpotFlatTerrainPolicy
        from pxr import UsdPhysics

        print("All imports successful for extension: omni.isaac.quadruped")
