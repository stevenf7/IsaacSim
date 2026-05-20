import isaacsim.core.experimental.utils.stage as stage_utils
import numpy as np
from isaacsim.core.experimental.materials import PreviewSurfaceMaterial
from isaacsim.core.experimental.objects import Cube
from isaacsim.core.experimental.prims import Articulation, GeomPrim, RigidPrim, XformPrim
from isaacsim.core.simulation_manager import SimulationManager
from isaacsim.examples.base.base_sample_experimental import BaseSample
from isaacsim.storage.native import get_assets_root_path


class HelloWorld(BaseSample):
    def __init__(self) -> None:
        super().__init__()
        self._physics_callback_id = None
        self._step_counter = 0

    def setup_scene(self):
        assets_root_path = get_assets_root_path()

        # Add ground plane
        stage_utils.add_reference_to_stage(
            usd_path=assets_root_path + "/Isaac/Environments/Grid/default_environment.usd",
            path="/World/ground",
        )

        # Add Jetbot mobile robot
        stage_utils.add_reference_to_stage(
            usd_path=assets_root_path + "/Isaac/Robots/NVIDIA/Jetbot/jetbot.usd",
            path="/World/Jetbot",
        )

        # Add a cube in front of Jetbot for it to push
        visual_material = PreviewSurfaceMaterial("/World/Materials/red")
        visual_material.set_input_values("diffuseColor", [1.0, 0.0, 0.0])
        cube_shape = Cube(
            paths="/World/Cube",
            positions=np.array([[0.15, 0.0, 0.025]]),
            sizes=[1.0],
            scales=np.array([[0.05, 0.05, 0.05]]),
            reset_xform_op_properties=True,
        )
        GeomPrim(paths=cube_shape.paths, apply_collision_apis=True)
        RigidPrim(paths=cube_shape.paths)
        cube_shape.apply_visual_materials(visual_material)

        # Add Franka manipulator
        stage_utils.add_reference_to_stage(
            usd_path=assets_root_path + "/Isaac/Robots/FrankaRobotics/FrankaPanda/franka.usd",
            path="/World/Franka",
        )

        # Position Franka forward and to the right of Jetbot's path
        franka_xform = XformPrim("/World/Franka")
        franka_xform.set_world_poses(positions=np.array([[0.8, -0.5, 0.0]]))

    async def setup_post_load(self):
        # Create Articulation handles
        self._jetbot = Articulation("/World/Jetbot")
        self._franka = Articulation("/World/Franka")
        self._cube = RigidPrim("/World/Cube")
        self._step_counter = 0

        # Register physics callback
        from isaacsim.core.simulation_manager.impl.isaac_events import IsaacEvents

        self._physics_callback_id = SimulationManager.register_callback(
            self.physics_step, IsaacEvents.POST_PHYSICS_STEP
        )

    def physics_step(self, dt, context):
        # -- Begin control Jetbot -- #
        self._step_counter += 1
        if self._step_counter < 300:
            # Drive Jetbot forward to push the cube
            self._jetbot.set_dof_velocity_targets([[10.0, 10.0]])
        else:
            # Stop the Jetbot after pushing
            self._jetbot.set_dof_velocity_targets([[0.0, 0.0]])
        # -- End of control Jetbot -- #

    def physics_cleanup(self):
        if self._physics_callback_id is not None:
            SimulationManager.deregister_callback(self._physics_callback_id)
            self._physics_callback_id = None
