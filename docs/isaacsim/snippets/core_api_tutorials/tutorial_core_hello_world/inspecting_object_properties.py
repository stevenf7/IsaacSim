import isaacsim.core.experimental.utils.stage as stage_utils
import numpy as np
from isaacsim.core.experimental.materials import PreviewSurfaceMaterial
from isaacsim.core.experimental.objects import Cube
from isaacsim.core.experimental.prims import GeomPrim, RigidPrim
from isaacsim.examples.base.base_sample_experimental import BaseSample
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

        # Create a blue visual material for the cube
        visual_material = PreviewSurfaceMaterial("/World/Materials/blue")
        visual_material.set_input_values("diffuseColor", [0.0, 0.0, 1.0])

        # Create the cube geometry
        self._cube_shape = Cube(
            paths="/World/fancy_cube",
            positions=np.array([[0.0, 0.0, 1.0]]),
            sizes=[1.0],
            scales=np.array([[0.5015, 0.5015, 0.5015]]),
            reset_xform_op_properties=True,
        )

        # Apply collision and rigid body
        GeomPrim(paths=self._cube_shape.paths, apply_collision_apis=True)
        self._cube = RigidPrim(paths=self._cube_shape.paths)
        self._cube_shape.apply_visual_materials(visual_material)

    # This function is called after load button is pressed
    # It's called once, after both setup_scene and one physics time step has finished
    # to propagate physics handles needed to retrieve physical properties
    async def setup_post_load(self):
        # Query cube properties using RigidPrim methods
        positions, orientations = self._cube.get_world_poses()
        # get_velocities() returns a tuple: (linear_velocities, angular_velocities)
        linear_velocities, angular_velocities = self._cube.get_velocities()

        # Convert from warp arrays to numpy for printing
        # Note: experimental APIs return batched results (even for single objects)
        print("Cube position is : " + str(positions.numpy()[0]))
        print("Cube's orientation is : " + str(orientations.numpy()[0]))
        print("Cube's linear velocity is : " + str(linear_velocities.numpy()[0]))
