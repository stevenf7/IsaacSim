# Import test file for omni.isaac.tf_viewer
# This file was automatically generated to test imports from deprecated extensions
# Compiled from tests found in python/tests

import omni.kit.test


class TestImports(omni.kit.test.AsyncTestCase):
    async def setUp(self):
        pass

    async def tearDown(self):
        pass

    async def test_imports_for_omni_isaac_tf_viewer_extension(self):
        # Testing all imports from original extension tests
        import os

        import carb
        import omni.graph.core as og
        import omni.kit.app
        from omni.isaac.core.utils.physics import simulate_async
        from omni.isaac.core.utils.stage import add_reference_to_stage, create_new_stage_async
        from omni.isaac.nucleus import get_assets_root_path_async
        from pxr import Sdf

        print("All imports successful for extension: omni.isaac.tf_viewer")
