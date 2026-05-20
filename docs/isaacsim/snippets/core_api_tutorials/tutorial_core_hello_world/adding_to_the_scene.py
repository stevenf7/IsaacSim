# -- Import Isaac sim packages -- #
import isaacsim.core.experimental.utils.stage as stage_utils
import numpy as np
from isaacsim.core.experimental.materials import PreviewSurfaceMaterial
from isaacsim.core.experimental.objects import Cube
from isaacsim.core.experimental.prims import GeomPrim, RigidPrim
from isaacsim.examples.base.base_sample_experimental import BaseSample
from isaacsim.storage.native import get_assets_root_path

# -- End of import Isaac sim packages -- #


class HelloWorld(BaseSample):
    def __init__(self) -> None:
        super().__init__()

    def setup_scene(self):
        # Add ground plane
        ground_plane = stage_utils.add_reference_to_stage(
            usd_path=get_assets_root_path() + "/Isaac/Environments/Grid/default_environment.usd",
            path="/World/ground",
        )

        # -- Creating a cube and apply materials -- #
        # Create a blue visual material for the cube
        visual_material = PreviewSurfaceMaterial("/World/Materials/blue")
        visual_material.set_input_values("diffuseColor", [0.0, 0.0, 1.0])

        # Create the cube geometry
        self._cube_shape = Cube(
            paths="/World/fancy_cube",
            positions=np.array([[0.0, 0.0, 1.0]]),  # Starting position 1m above ground
            sizes=[1.0],
            scales=np.array([[0.5015, 0.5015, 0.5015]]),  # Scale the cube
            reset_xform_op_properties=True,
        )

        # Apply collision APIs to enable physics collision
        GeomPrim(paths=self._cube_shape.paths, apply_collision_apis=True)

        # Make it a rigid body (dynamic object that responds to physics)
        self._cube = RigidPrim(paths=self._cube_shape.paths)

        # Apply the blue material
        self._cube_shape.apply_visual_materials(visual_material)
        # -- End of creating a cube and apply materials -- #
