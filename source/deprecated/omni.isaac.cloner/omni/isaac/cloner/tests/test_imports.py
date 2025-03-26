# Import test file for omni.isaac.cloner
# This file was automatically generated to test imports from deprecated extensions
# Compiled from tests found in omni/isaac/cloner/tests

import omni.kit.test


class TestImports(omni.kit.test.AsyncTestCase):
    async def setUp(self):
        pass

    async def tearDown(self):
        pass

    async def test_imports_for_omni_isaac_cloner_extension(self):
        # Testing all imports from original extension tests
        import unittest

        import numpy as np
        import omni.kit
        from omni.isaac.cloner import Cloner, GridCloner
        from omni.isaac.nucleus import get_assets_root_path_async
        from pxr import Gf, Usd, UsdGeom, UsdPhysics, Vt

        print("All imports successful for extension: omni.isaac.cloner")
