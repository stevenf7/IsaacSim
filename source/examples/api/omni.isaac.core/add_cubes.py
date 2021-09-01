from omni.isaac.kit import SimulationApp
import numpy as np

simulation_app = SimulationApp({"headless": False})

from omni.isaac.core import World
from omni.isaac.core.objects import VisualCube, DynamicCube

my_world = World()
cube_1 = my_world.scene.add(
    VisualCube(
        stage=my_world.stage,
        prim_path="/new_cube_1",
        name="visual_cube",
        position=np.array([0, 0, 15.0]),
        size=2.0,
        color=np.array([255, 255, 255]),
    )
)

cube_2 = my_world.scene.add(
    DynamicCube(
        stage=my_world.stage,
        prim_path="/new_cube_2",
        name="cube_1",
        position=np.array([0, 0, 3.0]),
        size=4.0,
        color=np.array([255, 0, 0]),
    )
)

cube_3 = my_world.scene.add(
    DynamicCube(
        stage=my_world.stage,
        prim_path="/new_cube_3",
        name="cube_2",
        position=np.array([0, 0, 8.0]),
        size=2.0,
        color=np.array([0, 0, 255]),
        linear_velocity=np.array([0, 0, 0.4]),
    )
)

for i in range(5):
    my_world.reset()
    for i in range(1000):
        my_world.step(render=True)
        print(cube_2.get_angular_velocity())
        print(cube_2.get_pose())

simulation_app.close()
