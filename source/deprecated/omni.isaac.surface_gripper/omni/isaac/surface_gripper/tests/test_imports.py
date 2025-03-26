# Import test file for omni.isaac.surface_gripper
# This file was automatically generated to test imports from deprecated extensions
# Compiled from tests found in python/tests

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
        from omni.isaac.surface_gripper._surface_gripper import Surface_Gripper, Surface_Gripper_Properties
        from pxr import Gf, Sdf, Tf, Usd, UsdGeom, UsdLux, UsdPhysics

        print("All imports successful for extension: omni.isaac.surface_gripper")
