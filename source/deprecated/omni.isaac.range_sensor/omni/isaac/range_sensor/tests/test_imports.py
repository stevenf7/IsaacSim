# Import test file for omni.isaac.range_sensor
# This file was automatically generated to test imports from deprecated extensions
# Compiled from tests found in python/tests

import omni.kit.test


class TestImports(omni.kit.test.AsyncTestCase):
    async def setUp(self):
        pass

    async def tearDown(self):
        pass

    async def test_imports_for_omni_isaac_range_sensor_extension(self):
        # Testing all imports from original extension tests
        import carb
        import carb.tokens
        import numpy as np
        import omni.isaac.RangeSensorSchema as RangeSensorSchema
        import omni.kit.commands
        from omni.isaac.core.utils.physics import simulate_async
        from omni.isaac.core.utils.stage import open_stage_async
        from omni.isaac.nucleus import get_assets_root_path_async
        from omni.isaac.range_sensor import _range_sensor
        from omni.syntheticdata.tests.utils import add_semantics
        from pxr import Gf, PhysicsSchemaTools, Sdf, Usd, UsdGeom, UsdLux, UsdPhysics, UsdShade

        print("All imports successful for extension: omni.isaac.range_sensor")
