# Import test file for omni.isaac.examples
# This file was automatically generated to test imports from deprecated extensions
# Compiled from tests found in omni/isaac/examples/tests

import omni.kit.test


class TestImports(omni.kit.test.AsyncTestCase):
    async def setUp(self):
        pass

    async def tearDown(self):
        pass

    async def test_imports_for_omni_isaac_examples_extension(self):
        # Testing all imports from original extension tests
        import asyncio
        import os

        import carb
        import carb.tokens
        import numpy as np
        import omni.kit
        import omni.kit.commands
        from omni.isaac.core import World
        from omni.isaac.core.utils.extensions import get_extension_path_from_name
        from omni.isaac.core.utils.physics import simulate_async
        from omni.isaac.core.utils.prims import get_prim_at_path
        from omni.isaac.core.utils.rotations import quat_to_euler_angles
        from omni.isaac.core.utils.stage import create_new_stage_async, is_stage_loading, update_stage_async
        from omni.isaac.core.world.world import World
        from omni.isaac.examples.bin_filling import BinFilling
        from omni.isaac.examples.follow_target import FollowTarget
        from omni.isaac.examples.hello_world import HelloWorld
        from omni.isaac.examples.humanoid.h1 import H1FlatTerrainPolicy
        from omni.isaac.examples.kaya_gamepad import KayaGamepad
        from omni.isaac.examples.omnigraph_keyboard import OmnigraphKeyboard
        from omni.isaac.examples.path_planning import PathPlanning
        from omni.isaac.examples.replay_follow_target import ReplayFollowTarget
        from omni.isaac.examples.robo_factory import RoboFactory
        from omni.isaac.examples.robo_party import RoboParty
        from omni.isaac.examples.simple_stack import SimpleStack
        from pxr import UsdPhysics

        print("All imports successful for extension: omni.isaac.examples")
