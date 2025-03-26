# Import test file for omni.isaac.wheeled_robots
# This file was automatically generated to test imports from deprecated extensions
# Compiled from tests found in python/tests

import omni.kit.test


class TestImports(omni.kit.test.AsyncTestCase):
    async def setUp(self):
        pass

    async def tearDown(self):
        pass

    async def test_imports_for_omni_isaac_wheeled_robots_extension(self):
        # Testing all imports from original extension tests
        import asyncio
        import sys
        from re import I

        import carb
        import numpy as np
        import omni.graph.core as og
        import omni.graph.core.tests as ogts
        import usdrt.Sdf
        from omni.isaac.core import World
        from omni.isaac.core.robots import Robot
        from omni.isaac.core.utils.physics import simulate_async
        from omni.isaac.core.utils.prims import delete_prim, get_prim_at_path
        from omni.isaac.core.utils.stage import create_new_stage_async, open_stage_async
        from omni.isaac.nucleus import get_assets_root_path, get_assets_root_path_async
        from omni.isaac.wheeled_robots.controllers.ackermann_controller import AckermannController
        from omni.isaac.wheeled_robots.controllers.differential_controller import DifferentialController
        from omni.isaac.wheeled_robots.controllers.holonomic_controller import HolonomicController
        from omni.isaac.wheeled_robots.robots import WheeledRobot

        print("All imports successful for extension: omni.isaac.wheeled_robots")
