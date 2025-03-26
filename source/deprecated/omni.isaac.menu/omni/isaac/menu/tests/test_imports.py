# Import test file for omni.isaac.menu
# This file was automatically generated to test imports from deprecated extensions
# Compiled from tests found in omni/isaac/menu/tests

import omni.kit.test


class TestImports(omni.kit.test.AsyncTestCase):
    async def setUp(self):
        pass

    async def tearDown(self):
        pass

    async def test_imports_for_omni_isaac_menu_extension(self):
        # Testing all imports from original extension tests
        from pathlib import Path

        import carb
        import carb.settings
        import carb.tokens
        import omni.kit.commands
        import omni.usd
        from omni.isaac.core.objects import DynamicCuboid
        from omni.isaac.core.utils.prims import get_prim_path
        from omni.isaac.core.utils.stage import clear_stage, create_new_stage, traverse_stage
        from omni.isaac.core.utils.viewports import set_camera_view
        from omni.isaac.range_sensor import _range_sensor
        from omni.isaac.sensor import _sensor
        from omni.kit.mainwindow import get_main_window
        from omni.kit.viewport.utility import get_active_viewport, get_active_viewport_window
        from omni.kit.viewport.utility.tests.capture import capture_viewport_and_wait, finalize_capture_and_compare
        from pxr import UsdGeom, UsdPhysics

        print("All imports successful for extension: omni.isaac.menu")
