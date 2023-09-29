import os

from omni.isaac.kit import SimulationApp

simulation_app = SimulationApp({"headless": True})

import numpy as np
from omni.isaac.core import World
from omni.isaac.core.articulations import Articulation
from omni.isaac.core.utils.stage import add_reference_to_stage

asset_path = "data/orientation_bug.usd"

my_world = World(stage_units_in_meters=1.0)
add_reference_to_stage(usd_path=asset_path, prim_path="/World")
articulated = Articulation(prim_path="/World/microwave")
my_world.scene.add(articulated)
my_world.reset()
for i in range(3):
    my_world.step(render=True)
if not (np.isclose(articulated.get_world_pose()[1], [-0.50, -0.49, 0.49, 0.50], atol=1e-02)).all():
    raise (
        ValueError(
            f"ArticulationView is not using the correct default state due to a mismatch in the ArticualtionRoot representation"
        )
    )
simulation_app.close()
