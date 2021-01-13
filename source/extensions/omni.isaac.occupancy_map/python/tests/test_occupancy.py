# NOTE:
#   omni.kit.test - std python's unittest module with additional wrapping to add suport for async/await tests
#   For most things refer to unittest docs: https://docs.python.org/3/library/unittest.html
import omni.kit.test

import omni.kit.usd
import carb.tokens
import os
import asyncio
import numpy as np
from omni.physx.scripts import utils

from pxr import UsdPhysics, Sdf, UsdGeom, PhysxSchema

# Import extension python module we are testing with absolute import path, as if we are external user (other extension)
from omni.isaac.occupancy_map import _occupancy_map
from omni.isaac.occupancy_map.scripts.utils import update_location, compute_coordinates, generate_image
from omni.isaac.utils.scripts.nucleus_utils import find_nucleus_server
from omni.isaac.utils.scripts.test_utils import load_test_file

# Having a test class dervived from omni.kit.test.AsyncTestCase declared on the root of module will make it auto-discoverable by omni.kit.test
class TestOccupancyMapGenerator(omni.kit.test.AsyncTestCaseFailOnLogError):
    # Before running each test
    async def setUp(self):
        self._om = _occupancy_map.acquire_occupancy_map_interface()
        self._timeline = omni.timeline.get_timeline_interface()

        result, nucleus_server = find_nucleus_server()
        if result is False:
            carb.log_error("Could not find nucleus server with /Isaac folder")
            return
        self._nucleus_path = nucleus_server + "/Isaac"
        pass

    # After running each test
    async def tearDown(self):
        # In some cases the test will end before the asset is loaded, in this case wait for assets to load
        while omni.kit.editor.get_editor_interface().get_current_renderer_status()[3] > 0:
            print("tearDown, assets still loading, waiting to finish...")
            await asyncio.sleep(1.0)
        pass

    def compute_index(self, p, scale, size, min_b):
        return int(p[1] / scale - min_b[1] / scale) * int(size[0] / scale) + int(p[0] / scale - min_b[0] / scale)

    def add_cube(self, path, size, offset):

        cubeGeom = UsdGeom.Cube.Define(self._stage, path)
        cubePrim = self._stage.GetPrimAtPath(path)

        cubeGeom.CreateSizeAttr(size)
        cubeGeom.AddTranslateOp().Set(offset)
        utils.setCollider(cubePrim)

        return cubeGeom

    # Actual test, notice it is "async" function, so "await" can be used if needed
    async def test_simple_room(self):
        (result, error) = await load_test_file(self._nucleus_path + "/Environments/Simple_Room/simple_room.usd")
        stage = omni.usd.get_context().get_stage()
        await omni.kit.app.get_app().next_update_async()
        UsdPhysics.Scene.Define(stage, Sdf.Path("/World/physicsScene"))
        await omni.kit.app.get_app().next_update_async()
        self._timeline.play()
        update_location(self._om, (0, 0, 40), (-500, -500), (500, 500))
        cell_size = 5
        await omni.kit.app.get_app().next_update_async()
        self._om.generate(cell_size, 5, 1, 1, 1000000)
        await omni.kit.app.get_app().next_update_async()
        self._timeline.stop()

        points = self._om.get_occupied_positions()
        self.assertEqual(len(points), 825)
        scale = cell_size
        top_left, top_right, bottom_left, bottom_right, image_coords = compute_coordinates(self._om, scale)
        min_b = self._om.get_min_bound()
        max_b = self._om.get_max_bound()

        self.assertEqual(top_left, (442.5, -332.5))
        self.assertEqual(top_right, (-442.5, -332.5))
        self.assertEqual(bottom_left, (442.5, 477.5))
        self.assertEqual(bottom_right, (-442.5, 477.5))
        self.assertEqual((float(image_coords[0][0]), float(image_coords[1][0])), (332.5, 442.5))

        size = [0, 0, 0]

        size[0] = max_b[0] - min_b[0]
        size[1] = max_b[1] - min_b[1]

        # raw data: computed index, point value, point index
        # no reason for picking these specific points
        # 368 (-382.5,-322.5,42.5) 0
        # 98 (47.5,-332.5,42.5) 200
        # 14952 (-442.5,87.5,42.5) 400
        # 28922 (-12.5,477.5,42.5) 600
        # 27937 (402.5,447.5,42.5) 824

        self.assertEqual(self.compute_index(points[0], scale, size, min_b), 368)
        self.assertEqual(self.compute_index(points[200], scale, size, min_b), 98)
        self.assertEqual(self.compute_index(points[400], scale, size, min_b), 14952)
        self.assertEqual(self.compute_index(points[600], scale, size, min_b), 28922)
        self.assertEqual(self.compute_index(points[824], scale, size, min_b), 27937)

        # This test currently fails from PIL not loading on TC
        # im = generate_image(self._om, scale, [0, 0, 0, 255], [127, 127, 127, 255], [255, 255, 255, 255], [0, 0])
        # # randomly selected pixels to check
        # self.assertEqual(im.getpixel((62, 62)), (127, 127, 127, 255))
        # self.assertEqual(im.getpixel((174, 4)), (127, 127, 127, 255))
        # self.assertEqual(im.getpixel((112, 72)), (127, 127, 127, 255))
        # self.assertEqual(im.getpixel((92, 130)), (255, 255, 255, 255))
        # self.assertEqual(im.getpixel((0, 104)), (0, 0, 0, 255))
        # self.assertEqual(im.getpixel((60, 63)), (0, 0, 0, 255))
        pass

    async def test_synthetic(self):
        await omni.usd.get_context().new_stage_async()
        context = omni.usd.get_context()
        self._stage = context.get_stage()
        self.add_cube("/cube_1", 100, (100, 0, 0))
        self.add_cube("/cube_2", 100, (100, 200, 0))
        self.add_cube("/cube_3", 100, (-150, -150, 0))
        self._physx = omni.physx.acquire_physx_interface()

        await omni.kit.app.get_app().next_update_async()
        UsdPhysics.Scene.Define(self._stage, Sdf.Path("/World/physicsScene"))
        physxSceneAPI = PhysxSchema.PhysxSceneAPI.Get(self._stage, "/World/physicsScene")
        physxSceneAPI.CreateEnableCCDAttr(True)
        physxSceneAPI.CreateEnableStabilizationAttr(True)
        physxSceneAPI.CreateEnableGPUDynamicsAttr(False)
        physxSceneAPI.CreateBroadphaseTypeAttr("MBP")
        physxSceneAPI.CreateSolverTypeAttr("TGS")
        await omni.kit.app.get_app().next_update_async()
        self._timeline.play()
        await omni.kit.app.get_app().next_update_async()
        generator = _occupancy_map.Generator(self._physx, context.get_stage_id())
        generator.update_settings(5, 1, 2, 5, 1000000, 4, 5, 6)
        generator.set_transform((0, 0, 0), (-200, -200), (200, 200))
        for frame in range(1):
            await omni.kit.app.get_app().next_update_async()
            generator.generate()

        min_bounds = generator.get_min_bound()
        self.assertEqual(min_bounds[0], -200)
        self.assertEqual(min_bounds[1], -200)
        max_bounds = generator.get_max_bound()
        self.assertEqual(max_bounds[0], 200)
        self.assertEqual(max_bounds[1], 200)

        dims = generator.get_dimensions()
        self.assertEqual(dims[0], 80)
        self.assertEqual(dims[1], 80)
        # TODO: add raw occupied position checks
        # print(generator.get_occupied_positions())
        buffer = np.array(generator.get_buffer())
        self.assertEqual(len(buffer), dims[0] * dims[1])
        buffer = np.reshape(buffer, (dims[0], dims[1]))

        self.assertEqual(buffer[0, 79], 6)
        self.assertEqual(buffer[5, 75], 6)
        self.assertEqual(buffer[10, 59], 4)
        self.assertEqual(buffer[50, 20], 4)
        self.assertEqual(buffer[75, 29], 4)
        self.assertEqual(buffer[40, 40], 5)
        self.assertEqual(buffer[75, 20], 6)
