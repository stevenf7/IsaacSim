# NOTE:
#   omni.kit.test - std python's unittest module with additional wrapping to add suport for async/await tests
#   For most things refer to unittest docs: https://docs.python.org/3/library/unittest.html
import omni.kit.test

import omni.kit.usd
import omni.kit.commands
import os
import carb
import asyncio
from omni.isaac.utils import _isaac_utils
from pxr import Usd, UsdLux, UsdGeom, Sdf, Gf, Tf, UsdPhysics
import random
import itertools

# Having a test class dervived from omni.kit.test.AsyncTestCase declared on the root of module will make it auto-discoverable by omni.kit.test
class TestDebugDraw(omni.kit.test.AsyncTestCaseFailOnLogError):

    # Before running each test
    async def setUp(self):
        self._draw = _isaac_utils.debug_draw.acquire_debug_draw_interface()
        pass

    # After running each test
    async def tearDown(self):
        await omni.kit.app.get_app().next_update_async()
        pass

    # Actual test, notice it is "async" function, so "await" can be used if needed
    async def test_draw_points(self):
        N = 10000
        point_list_1 = [
            (random.uniform(-1000, 1000), random.uniform(-1000, 1000), random.uniform(-1000, 1000)) for _ in range(N)
        ]
        point_list_2 = [
            (random.uniform(-1000, 1000), random.uniform(1000, 3000), random.uniform(-1000, 1000)) for _ in range(N)
        ]
        point_list_3 = [
            (random.uniform(-1000, 1000), random.uniform(-3000, -1000), random.uniform(-1000, 1000)) for _ in range(N)
        ]
        colors = [(random.uniform(0.5, 1), random.uniform(0.5, 1), random.uniform(0.5, 1), 1) for _ in range(N)]
        sizes = [random.randint(1, 50) for _ in range(N)]
        self._draw.draw_points(point_list_1, [(1, 0, 0, 1)] * N, [10] * N)
        self._draw.draw_points(point_list_2, [(0, 1, 0, 1)] * N, [10] * N)
        self._draw.draw_points(point_list_3, colors, sizes)
        print(self._draw.get_num_points())
        # TODO: Check number of points, then clear and check again
        pass

    async def test_draw_lines(self):
        N = 10000
        point_list_1 = [
            (random.uniform(1000, 3000), random.uniform(-1000, 1000), random.uniform(-1000, 1000)) for _ in range(N)
        ]
        point_list_2 = [
            (random.uniform(1000, 3000), random.uniform(-1000, 1000), random.uniform(-1000, 1000)) for _ in range(N)
        ]
        colors = [(random.uniform(0, 1), random.uniform(0, 1), random.uniform(0, 1), 1) for _ in range(N)]
        sizes = [random.randint(1, 25) for _ in range(N)]
        self._draw.draw_lines(point_list_1, point_list_2, colors, sizes)
        print(self._draw.get_num_lines())
        # TODO: Check number of points, then clear and check again
        pass

    async def test_draw_spline(self):
        point_list_1 = [
            (random.uniform(-300, -100), random.uniform(-100, 100), random.uniform(-100, 100)) for _ in range(10)
        ]
        self._draw.draw_lines_spline(point_list_1, (1, 1, 1, 1), 10, False)
        point_list_1 = [
            (random.uniform(-300, -100), random.uniform(-100, 100), random.uniform(-100, 100)) for _ in range(10)
        ]
        self._draw.draw_lines_spline(point_list_1, (1, 1, 1, 1), 5, True)

        # TODO: Check number of points, then clear and check again
        pass
