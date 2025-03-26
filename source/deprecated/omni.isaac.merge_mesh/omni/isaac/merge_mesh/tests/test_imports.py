# Import test file for omni.isaac.merge_mesh
# This file was automatically generated to test imports from deprecated extensions
# Compiled from tests found in omni/isaac/merge_mesh/tests

import omni.kit.test


class TestImports(omni.kit.test.AsyncTestCase):
    async def setUp(self):
        pass

    async def tearDown(self):
        pass

    async def test_imports_for_omni_isaac_merge_mesh_extension(self):
        # Testing all imports from original extension tests
        from pxr import Sdf, UsdGeom, UsdShade

        from ..mesh_merger import MeshMerger

        print("All imports successful for extension: omni.isaac.merge_mesh")
