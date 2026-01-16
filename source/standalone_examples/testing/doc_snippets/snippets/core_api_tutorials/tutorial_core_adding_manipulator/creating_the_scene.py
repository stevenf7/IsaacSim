import isaacsim.core.experimental.utils.stage as stage_utils
import numpy as np
from isaacsim.core.experimental.materials import PreviewSurfaceMaterial
from isaacsim.core.experimental.objects import Cube
from isaacsim.core.experimental.prims import GeomPrim, RigidPrim
from isaacsim.examples.base.base_sample_experimental import BaseSample
from isaacsim.robot.manipulators.examples.franka import FrankaExperimental
from isaacsim.storage.native import get_assets_root_path


class HelloWorld(BaseSample):
    def __init__(self) -> None:
        super().__init__()

    def setup_scene(self):
        # Add ground plane
        ground_plane = stage_utils.add_reference_to_stage(
            usd_path=get_assets_root_path() + "/Isaac/Environments/Grid/default_environment.usd",
            path="/World/ground",
        )

        # Create the Franka robot - constructor spawns the robot when create_robot=True
        self._robot = FrankaExperimental(robot_path="/World/robot", create_robot=True)

        # Create a blue cube for the robot to pick up
        visual_material = PreviewSurfaceMaterial("/World/Materials/blue")
        visual_material.set_input_values("diffuseColor", [0.0, 0.0, 1.0])

        cube_shape = Cube(
            paths="/World/Cube",
            positions=np.array([[0.5, 0.0, 0.0258]]),
            sizes=[1.0],
            scales=np.array([[0.0515, 0.0515, 0.0515]]),
            reset_xform_op_properties=True,
        )

        GeomPrim(paths=cube_shape.paths, apply_collision_apis=True)
        RigidPrim(paths=cube_shape.paths)
        cube_shape.apply_visual_materials(visual_material)
