# Import test file for omni.isaac.benchmarks
# This file was automatically generated to test imports from deprecated extensions
# Compiled from tests found in omni/isaac/benchmarks/tests

import omni.kit.test


class TestImports(omni.kit.test.AsyncTestCase):
    async def setUp(self):
        pass

    async def tearDown(self):
        pass

    async def test_imports_for_omni_isaac_benchmarks_extension(self):
        # Testing all imports from original extension tests
        import sys

        import numpy as np
        from omni.isaac.benchmark.services import BaseIsaacBenchmarkAsync
        from omni.isaac.core.utils.rotations import euler_angles_to_quat
        from omni.isaac.core.utils.stage import is_stage_loading
        from omni.isaac.sensor import Camera
        from omni.kit.viewport.utility import get_active_viewport

        print("All imports successful for extension: omni.isaac.benchmarks")
