import isaacsim.core.experimental.utils.stage as stage_utils
import numpy as np
from isaacsim.core.experimental.materials import PreviewSurfaceMaterial
from isaacsim.core.experimental.objects import Cube
from isaacsim.core.experimental.prims import Articulation, GeomPrim, RigidPrim, XformPrim
from isaacsim.core.simulation_manager import SimulationManager
from isaacsim.examples.base.base_sample_experimental import BaseSample
from isaacsim.robot.manipulators.examples.franka import FrankaExperimental
from isaacsim.storage.native import get_assets_root_path


class RobotScenario:
    """Encapsulates a Jetbot + Franka + Cube scenario with an offset."""

    def __init__(self, name: str, offset: np.ndarray = np.array([0.0, 0.0, 0.0])):
        self.name = name
        self.offset = offset
        self.state = 0
        self.step_counter = 0
        self.pick_phase = 0
        self.jetbot = None
        self.franka = None
        self.cube = None
        self.cube_goal = np.array([1.2, 0.0, 0.0]) + offset

    def setup_scene(self):
        """Create the robots and cube for this scenario."""
        assets_root_path = get_assets_root_path()
        base_path = f"/World/{self.name}"

        # Add Jetbot
        stage_utils.add_reference_to_stage(
            usd_path=assets_root_path + "/Isaac/Robots/NVIDIA/Jetbot/jetbot.usd",
            path=f"{base_path}/Jetbot",
        )
        jetbot_xform = XformPrim(f"{base_path}/Jetbot")
        jetbot_xform.reset_xform_op_properties()
        jetbot_xform.set_world_poses(positions=[self.offset.tolist()])

        # Add cube in front of Jetbot
        cube_pos = self.offset + np.array([0.15, 0.0, 0.025])
        visual_material = PreviewSurfaceMaterial(f"{base_path}/Materials/red")
        visual_material.set_input_values("diffuseColor", [1.0, 0.0, 0.0])
        cube_shape = Cube(
            paths=f"{base_path}/Cube",
            positions=np.array([cube_pos]),
            sizes=[1.0],
            scales=np.array([[0.05, 0.05, 0.05]]),
            reset_xform_op_properties=True,
        )
        GeomPrim(paths=cube_shape.paths, apply_collision_apis=True)
        RigidPrim(paths=cube_shape.paths)
        cube_shape.apply_visual_materials(visual_material)

        # Add Franka
        franka_pos = self.offset + np.array([0.8, -0.3, 0.0])
        self.franka = FrankaExperimental(robot_path=f"{base_path}/Franka", create_robot=True)
        franka_xform = XformPrim(f"{base_path}/Franka")
        franka_xform.reset_xform_op_properties()
        franka_xform.set_world_poses(positions=[franka_pos.tolist()])

    def initialize(self):
        """Initialize articulation handles after scene load."""
        base_path = f"/World/{self.name}"
        self.jetbot = Articulation(f"{base_path}/Jetbot")
        self.cube = RigidPrim(f"{base_path}/Cube")

    def reset(self):
        """Reset the scenario state."""
        self.state = 0
        self.step_counter = 0
        self.pick_phase = 0
        self.franka.reset_to_default_pose()

    def step(self):
        """Execute one step of the scenario logic."""
        if self.state == 0:
            # Jetbot pushes cube
            cube_pos = self.cube.get_world_poses()[0].numpy()[0]
            if np.linalg.norm(cube_pos[:2] - self.cube_goal[:2]) > 0.05:
                self.jetbot.set_dof_velocity_targets([[10.0, 10.0]])
            else:
                self.jetbot.set_dof_velocity_targets([[0.0, 0.0]])
                self.state = 1
                self.step_counter = 0

        elif self.state == 1:
            # Jetbot backs up
            self.jetbot.set_dof_velocity_targets([[-8.0, -8.0]])
            self.step_counter += 1
            if self.step_counter > 100:
                self.jetbot.set_dof_velocity_targets([[0.0, 0.0]])
                self.state = 2
                self.step_counter = 0
                self.franka.open_gripper()

        elif self.state == 2:
            # Franka pick-and-place
            self._franka_pick_place()

    def _franka_pick_place(self):
        """Execute Franka pick-and-place state machine."""
        cube_pos = self.cube.get_world_poses()[0].numpy()[0]
        down_orient = self.franka.get_downward_orientation()
        self.step_counter += 1

        if self.pick_phase == 0:
            self.franka.set_end_effector_pose(np.array([[cube_pos[0], cube_pos[1], cube_pos[2] + 0.2]]), down_orient)
            if self.step_counter > 120:
                self.pick_phase = 1
                self.step_counter = 0
        elif self.pick_phase == 1:
            self.franka.set_end_effector_pose(np.array([[cube_pos[0], cube_pos[1], cube_pos[2] + 0.1]]), down_orient)
            if self.step_counter > 100:
                self.franka.close_gripper()
                self.pick_phase = 2
                self.step_counter = 0
        elif self.pick_phase == 2:
            self.franka.close_gripper()
            if self.step_counter > 50:
                self.pick_phase = 3
                self.step_counter = 0
        elif self.pick_phase == 3:
            self.franka.set_end_effector_pose(np.array([[cube_pos[0], cube_pos[1], cube_pos[2] + 0.25]]), down_orient)
            if self.step_counter > 100:
                self.pick_phase = 4
                self.step_counter = 0
        elif self.pick_phase == 4:
            target = self.offset + np.array([0.3, 0.3, 0.15])
            self.franka.set_end_effector_pose(np.array([target]), down_orient)
            if self.step_counter > 150:
                self.franka.open_gripper()
                self.step_counter = 0
                self.pick_phase = 5
        elif self.pick_phase == 5:
            # Lift the arm from target position (don't use cube_pos - cube was dropped)
            target = self.offset + np.array([0.3, 0.3, 0.4])  # Lift above drop location
            self.franka.set_end_effector_pose(np.array([target]), down_orient)
            if self.step_counter > 150:
                self.step_counter = 0
                self.state = 5  # Done


class HelloWorld(BaseSample):
    def __init__(self) -> None:
        super().__init__()
        self._physics_callback_id = None
        self._scenario = None

    def setup_scene(self):
        # Add ground plane
        stage_utils.add_reference_to_stage(
            usd_path=get_assets_root_path() + "/Isaac/Environments/Grid/default_environment.usd",
            path="/World/ground",
        )
        # Create a single scenario
        self._scenario = RobotScenario(name="scenario_0", offset=np.array([0.0, 0.0, 0.0]))
        self._scenario.setup_scene()

    async def setup_post_load(self):
        self._scenario.initialize()

        from isaacsim.core.simulation_manager.impl.isaac_events import IsaacEvents

        self._physics_callback_id = SimulationManager.register_callback(
            self.physics_step, IsaacEvents.POST_PHYSICS_STEP
        )

    def physics_step(self, dt, context):
        self._scenario.step()

    async def setup_post_reset(self):
        self._scenario.reset()

    def physics_cleanup(self):
        if self._physics_callback_id is not None:
            SimulationManager.deregister_callback(self._physics_callback_id)
            self._physics_callback_id = None
