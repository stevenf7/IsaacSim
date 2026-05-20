import isaacsim.core.experimental.utils.stage as stage_utils
import numpy as np
from isaacsim.core.experimental.materials import PreviewSurfaceMaterial
from isaacsim.core.experimental.objects import Cube
from isaacsim.core.experimental.prims import GeomPrim, RigidPrim

# -- Begin loading SimulationManager -- #
from isaacsim.core.simulation_manager import SimulationManager

# -- End of loading SimulationManager -- #
from isaacsim.examples.base.base_sample_experimental import BaseSample
from isaacsim.storage.native import get_assets_root_path


class HelloWorld(BaseSample):
    def __init__(self) -> None:
        super().__init__()
        self._physics_callback_id = None

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

    async def setup_post_load(self):
        # -- Begin registering callback -- #
        # Register a physics callback using SimulationManager
        from isaacsim.core.simulation_manager.impl.isaac_events import IsaacEvents

        self._physics_callback_id = SimulationManager.register_callback(
            self.print_cube_info, IsaacEvents.POST_PHYSICS_STEP
        )
        # -- End of registering callback -- #

    # Physics callback function - called after each physics step
    # Takes dt (delta time) and context as arguments
    def print_cube_info(self, dt, context):
        positions, orientations = self._cube.get_world_poses()
        linear_velocities, angular_velocities = self._cube.get_velocities()

        print("Cube position is : " + str(positions.numpy()[0]))
        print("Cube's orientation is : " + str(orientations.numpy()[0]))
        print("Cube's linear velocity is : " + str(linear_velocities.numpy()[0]))

    def physics_cleanup(self):
        # -- Begin deregistering callback -- #
        # Clean up callback when the extension is unloaded
        if self._physics_callback_id is not None:
            SimulationManager.deregister_callback(self._physics_callback_id)
            self._physics_callback_id = None
        # -- End of deregistering callback -- #
