# Import test file for omni.isaac.robot_assembler
# This file was automatically generated to test imports from deprecated extensions
# Compiled from tests found in omni/isaac/robot_assembler/tests

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
