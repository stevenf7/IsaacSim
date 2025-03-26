# Import test file for omni.isaac.grasp_editor
# This file was automatically generated to test imports from deprecated extensions
# Compiled from tests found in omni/isaac/grasp_editor/tests

import omni.kit.test


class TestImports(omni.kit.test.AsyncTestCase):
    async def setUp(self):
        pass

    async def tearDown(self):
        pass

    async def test_imports_for_omni_isaac_grasp_editor_extension(self):
        # Testing all imports from original extension tests
        import asyncio

        import numpy as np
        from omni.isaac.core.objects import GroundPlane
        from omni.isaac.core.prims import XFormPrim, XFormPrimView
        from omni.isaac.core.utils.viewports import set_camera_view
        from omni.isaac.grasp_editor import GraspSpec, import_grasps_from_file
        from omni.isaac.grasp_editor.util import move_rb_subframe_to_position
        from omni.isaac.nucleus import get_assets_root_path_async
        from pxr import Sdf, UsdLux, UsdPhysics

        print("All imports successful for extension: omni.isaac.grasp_editor")
