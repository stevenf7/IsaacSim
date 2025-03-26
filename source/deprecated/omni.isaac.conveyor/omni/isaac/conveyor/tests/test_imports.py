# Import test file for omni.isaac.conveyor
# This file was automatically generated to test imports from deprecated extensions
# Compiled from tests found in python/tests

import omni.kit.test


class TestImports(omni.kit.test.AsyncTestCase):
    async def setUp(self):
        pass

    async def tearDown(self):
        pass

    async def test_imports_for_omni_isaac_conveyor_extension(self):
        # Testing all imports from original extension tests
        import asyncio
        import time

        import carb.tokens
        import numpy as np
        import omni.kit.commands
        from omni.isaac.conveyor.commands import CreateConveyorBelt
        from pxr import Gf, PhysxSchema, UsdGeom, UsdPhysics
        from usdrt import Sdf, Usd

        print("All imports successful for extension: omni.isaac.conveyor")
