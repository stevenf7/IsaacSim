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

    async def test_imports_for_omni_isaac_robot_assembler_extension(self):
        # Testing all imports from original extension tests
        import asyncio
        import os
        from typing import List

        import carb
        import numpy as np
        from omni.isaac.core.articulations import Articulation
        from omni.isaac.core.prims.xform_prim import XFormPrim
        from omni.isaac.core.utils.prims import get_prim_at_path
        from omni.isaac.core.utils.types import ArticulationAction
        from omni.isaac.core.world import World
        from omni.isaac.nucleus import get_assets_root_path_async
        from omni.isaac.robot_assembler import AssembledRobot, RobotAssembler
        from pxr import PhysxSchema, Sdf, UsdLux, UsdPhysics

        print("All imports successful for extension: omni.isaac.robot_assembler")
