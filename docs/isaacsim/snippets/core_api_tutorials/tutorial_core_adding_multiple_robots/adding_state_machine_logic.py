import isaacsim.core.experimental.utils.stage as stage_utils
import numpy as np
from isaacsim.core.experimental.materials import PreviewSurfaceMaterial
from isaacsim.core.experimental.objects import Cube
from isaacsim.core.experimental.prims import Articulation, GeomPrim, RigidPrim, XformPrim
from isaacsim.core.simulation_manager import SimulationManager
from isaacsim.examples.base.base_sample_experimental import BaseSample
from isaacsim.robot.experimental.manipulators.examples.franka import Franka
from isaacsim.storage.native import get_assets_root_path


class HelloWorld(BaseSample):
    def __init__(self) -> None:
        super().__init__()
        self._physics_callback_id = None
        self._state = 0

    def setup_scene(self):
        assets_root_path = get_assets_root_path()

        # Add ground plane
        stage_utils.add_reference_to_stage(
            usd_path=assets_root_path + "/Isaac/Environments/Grid/default_environment.usd",
            path="/World/ground",
        )

        # Add Jetbot at origin
        stage_utils.add_reference_to_stage(
            usd_path=assets_root_path + "/Isaac/Robots/NVIDIA/Jetbot/jetbot.usd",
            path="/World/Jetbot",
        )

        # Add cube in front of Jetbot
        visual_material = PreviewSurfaceMaterial("/World/Materials/blue")
        visual_material.set_input_values("diffuseColor", [0.0, 0.0, 1.0])
        cube_shape = Cube(
            paths="/World/Cube",
            positions=np.array([[0.15, 0.0, 0.0258]]),
            sizes=[1.0],
            scales=np.array([[0.05, 0.05, 0.05]]),
            reset_xform_op_properties=True,
        )
        GeomPrim(paths=cube_shape.paths, apply_collision_apis=True)
        RigidPrim(paths=cube_shape.paths)
        cube_shape.apply_visual_materials(visual_material)

        # Add Franka using Franka for IK and gripper control
        self._franka = Franka(robot_path="/World/Franka", create_robot=True)
        franka_xform = XformPrim("/World/Franka")
        franka_xform.set_world_poses(positions=[[0.8, -0.3, 0.0]])

    async def setup_post_load(self):
        self._jetbot = Articulation("/World/Jetbot")
        self._cube = RigidPrim("/World/Cube")
        self._cube_goal = np.array([1.2, 0.0, 0.0])  # Target: Franka reaches from the side
        self._step_counter = 0
        self._pick_phase = 0

        from isaacsim.core.simulation_manager.impl.isaac_events import IsaacEvents

        self._physics_callback_id = SimulationManager.register_callback(
            self.physics_step, IsaacEvents.POST_PHYSICS_STEP
        )
        self._state = 0

    def physics_step(self, dt, context):
        if self._state == 0:
            # Jetbot pushes cube to Franka
            cube_pos = self._cube.get_world_poses()[0].numpy()[0]
            if np.linalg.norm(cube_pos[:2] - self._cube_goal[:2]) > 0.05:
                self._jetbot.set_dof_velocity_targets([[10.0, 10.0]])
            else:
                self._jetbot.set_dof_velocity_targets([[0.0, 0.0]])
                print("Cube delivered! Backing up...")
                self._state = 1
                self._step_counter = 0

        elif self._state == 1:
            # Jetbot backs up
            self._jetbot.set_dof_velocity_targets([[-8.0, -8.0]])
            self._step_counter += 1
            if self._step_counter > 100:
                self._jetbot.set_dof_velocity_targets(np.array([[0.0, 0.0]]))
                print("Franka starting pick-and-place...")
                self._state = 2
                self._step_counter = 0
                self._franka.open_gripper()

        elif self._state == 2:
            # Franka pick-and-place sequence using step counter
            cube_pos = self._cube.get_world_poses()[0].numpy()[0]
            down_orient = self._franka.get_downward_orientation()
            self._step_counter += 1

            if self._pick_phase == 0:
                # Move above cube (wait 120 steps)
                self._franka.set_end_effector_pose(
                    np.array([[cube_pos[0], cube_pos[1], cube_pos[2] + 0.2]]), down_orient
                )
                if self._step_counter > 120:
                    self._pick_phase = 1
                    self._step_counter = 0
            elif self._pick_phase == 1:
                # Lower to cube (wait 100 steps)
                self._franka.set_end_effector_pose(
                    np.array([[cube_pos[0], cube_pos[1], cube_pos[2] + 0.1]]), down_orient
                )
                if self._step_counter > 100:
                    self._franka.close_gripper()
                    self._pick_phase = 2
                    self._step_counter = 0
            elif self._pick_phase == 2:
                # Close the gripper (wait 50 steps)
                self._franka.close_gripper()
                if self._step_counter > 50:
                    self._pick_phase = 3
                    self._step_counter = 0
            elif self._pick_phase == 3:
                # Lift cube (wait 100 steps)
                self._franka.set_end_effector_pose(
                    np.array([[cube_pos[0], cube_pos[1], cube_pos[2] + 0.25]]), down_orient
                )
                if self._step_counter > 100:
                    self._pick_phase = 4
                    self._step_counter = 0
            elif self._pick_phase == 4:
                # Move to target (wait 150 steps)
                self._franka.set_end_effector_pose(np.array([[0.3, 0.3, 0.15]]), down_orient)
                if self._step_counter > 150:
                    self._franka.open_gripper()
                    self._pick_phase = 5
                    self._step_counter = 0
            elif self._pick_phase == 5:
                # Lift the arm (wait 150 steps)
                self._franka.set_end_effector_pose(
                    np.array([[cube_pos[0], cube_pos[1], cube_pos[2] + 0.5]]), down_orient
                )
                if self._step_counter > 150:
                    self._step_counter = 0

    async def setup_post_reset(self):
        self._state = 0
        self._step_counter = 0
        self._pick_phase = 0
        self._franka.reset_to_default_pose()

    def physics_cleanup(self):
        if self._physics_callback_id is not None:
            SimulationManager.deregister_callback(self._physics_callback_id)
            self._physics_callback_id = None
