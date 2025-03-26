# Import test file for omni.isaac.quadruped
# This file was automatically generated to test imports from deprecated extensions
# Compiled from tests found in omni/isaac/quadruped/tests

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
        from omni.isaac.quadruped.utils.rot_utils import get_xyz_euler_from_quaternion
        from pxr import UsdPhysics

        print("All imports successful for extension: omni.isaac.quadruped")
