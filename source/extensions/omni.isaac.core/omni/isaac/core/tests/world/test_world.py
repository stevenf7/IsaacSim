import omni.kit.test
from scipy.spatial.transform import Rotation
import numpy as np
from omni.isaac.core import World
from omni.isaac.core.objects import VisualCube, DynamicCube
from omni.isaac.core.utils.stage import clear_stage, create_new_stage_async


class TestScene(omni.kit.test.AsyncTestCaseFailOnLogError):
    # Before running each test
    async def setUp(self):
        pass

    # After running each test
    async def tearDown(self):
        pass

    async def test_create_new_stage(self):
        await create_new_stage_async()
        my_world = World()
        await my_world.init_simulation_context_async()
        await omni.kit.app.get_app().next_update_async()
        cube_1 = my_world.scene.add(
            VisualCube(
                prim_path="/new_cube_1",
                name="visual_cube",
                position=np.array([0, 0, 0.5]),
                size=0.3,
                color=np.array([255, 255, 255]),
            )
        )
        await omni.kit.app.get_app().next_update_async()
        await my_world.reset_async()
        await omni.kit.app.get_app().next_update_async()
        my_world.set_physics_dt(1.0 / 120.0)
        await omni.kit.app.get_app().next_update_async()
        clear_stage()
        await omni.kit.app.get_app().next_update_async()
        self.assertTrue(my_world.get_physics_dt() == 1.0 / 120.0)
        await omni.kit.app.get_app().next_update_async()
        await my_world.reset_async()
        await omni.kit.app.get_app().next_update_async()
        cube_1 = my_world.scene.add(
            VisualCube(
                prim_path="/new_cube_1",
                name="visual_cube",
                position=np.array([0, 0, 0.5]),
                size=0.3,
                color=np.array([255, 255, 255]),
            )
        )
        await omni.kit.app.get_app().next_update_async()
        await my_world.reset_async()
        self.assertTrue(my_world.get_physics_dt() == 1.0 / 120.0)
        await create_new_stage_async()
        await my_world.reset_async()
        return
