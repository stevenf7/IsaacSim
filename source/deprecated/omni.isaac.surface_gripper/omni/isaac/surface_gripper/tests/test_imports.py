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

    async def test_imports_for_omni_isaac_surface_gripper_extension(self):
        # Testing all imports from original extension tests
        import asyncio
        import os

        import carb
        import carb.tokens
        import numpy as np
        import omni.kit.commands
        import omni.kit.usd
        import omni.physics.tensors
        from omni.isaac.core.prims.rigid_prim import RigidPrim
        from omni.isaac.core.utils.physics import simulate_async
        from omni.isaac.surface_gripper import _surface_gripper
        from pxr import Gf, Sdf, Tf, Usd, UsdGeom, UsdLux, UsdPhysics

        print("All imports successful for extension: omni.isaac.surface_gripper")
