# Import test file for omni.isaac.occupancy_map
# This file was automatically generated to test imports from deprecated extensions
# Compiled from tests found in python/tests

import omni.kit.test


class TestImports(omni.kit.test.AsyncTestCase):
    async def setUp(self):
        pass

    async def tearDown(self):
        pass

    async def test_imports_for_omni_isaac_occupancy_map_extension(self):
        # Testing all imports from original extension tests
        import carb.tokens
        import numpy as np
        import omni.kit.usd
        from omni.isaac.core.utils.stage import open_stage_async
        from omni.isaac.nucleus import get_assets_root_path_async
        from omni.isaac.occupancy_map.bindings import _occupancy_map
        from omni.isaac.occupancy_map.utils import compute_coordinates, generate_image, update_location
        from pxr import PhysxSchema, Sdf, UsdGeom, UsdPhysics

        print("All imports successful for extension: omni.isaac.occupancy_map")
