# Import test file for omni.replicator.isaac
# This file was automatically generated to test imports from deprecated extensions
# Compiled from tests found in python/tests

import omni.kit.test


class TestImports(omni.kit.test.AsyncTestCase):
    async def setUp(self):
        pass

    async def tearDown(self):
        pass

    async def test_imports_for_omni_replicator_isaac_extension(self):
        # Testing all imports from original extension tests
        import math
        import os
        import random
        import unittest
        from itertools import chain
        from pathlib import Path

        import carb
        import numpy as np
        import omni.graph.core as og
        import omni.kit
        import omni.kit.commands
        import omni.physics.tensors
        import omni.physx
        import omni.replicator.core as rep
        import omni.replicator.isaac as dr
        import omni.timeline
        import omni.usd
        import torch
        from omni.isaac.core import World
        from omni.isaac.core.articulations import ArticulationView
        from omni.isaac.core.objects import DynamicCuboid
        from omni.isaac.core.prims.rigid_prim_view import RigidPrimView
        from omni.isaac.core.utils.stage import add_reference_to_stage, create_new_stage_async
        from omni.isaac.nucleus import get_assets_root_path_async
        from omni.replicator.core.scripts.utils import ReplicatorItem, ReplicatorWrapper, create_node, set_target_prims
        from omni.replicator.isaac.scripts.writers.pytorch_listener import PytorchListener
        from PIL import Image
        from pxr import UsdGeom

        print("All imports successful for extension: omni.replicator.isaac")
