import isaacsim.core.experimental.utils.stage as stage_utils
import numpy as np
from isaacsim.core.experimental.objects import Cube, DomeLight, GroundPlane
from isaacsim.core.experimental.prims import Articulation, GeomPrim, RigidPrim, XformPrim
from isaacsim.core.simulation_manager import SimulationEvent, SimulationManager
from isaacsim.examples.base.base_sample_experimental import BaseSample
from isaacsim.robot.manipulators.examples.franka import FrankaExperimental
from isaacsim.storage.native import get_assets_root_path


class RobotScenario:
    """Encapsulates a Jetbot + Franka + Cube scenario with an offset."""

    def __init__(self, name: str, offset: np.ndarray = np.array([0.0, 0.0, 0.0]), randomize: bool = False):
        self.name = name
        self.offset = offset
        self.state = 0
        self.step_counter = 0
        self.randomize = randomize
        self.pick_phase = 0
        self.jetbot = None
        self.franka = None
        self.cube = None
        self.cube_goal = np.array([1.2, 0.0, 0.0]) + offset

        # Randomize cube goal position if enabled
        if self.randomize:
            random_x = np.random.uniform(1.0, 1.6)
            self.cube_goal = np.array([random_x, 0.0, 0.0]) + offset
        else:
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
        jetbot_xform.set_world_poses(positions=self.offset.tolist())

        # Add cube in front of Jetbot
        cube_pos = self.offset + np.array([0.15, 0.0, 0.025])
        cube_shape = Cube(
            paths=f"{base_path}/Cube",
            positions=cube_pos.tolist(),
            sizes=1.0,
            scales=[0.05, 0.05, 0.05],
            colors="red",
        )
        GeomPrim(paths=cube_shape.paths, apply_collision_apis=True)
        RigidPrim(paths=cube_shape.paths)

        # Add Franka
        franka_pos = self.offset + np.array([0.8, -0.3, 0.0])
        self.franka = FrankaExperimental(robot_path=f"{base_path}/Franka", create_robot=True)
        franka_xform = XformPrim(f"{base_path}/Franka")
        franka_xform.reset_xform_op_properties()
        franka_xform.set_world_poses(positions=franka_pos.tolist())

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
                self.jetbot.set_dof_velocity_targets([10.0, 10.0])
            else:
                self.jetbot.set_dof_velocity_targets([0.0, 0.0])
                self.state = 1
                self.step_counter = 0

        elif self.state == 1:
            # Jetbot backs up
            self.jetbot.set_dof_velocity_targets([-8.0, -8.0])
            self.step_counter += 1
            if self.step_counter > 100:
                self.jetbot.set_dof_velocity_targets([0.0, 0.0])
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
            self.franka.set_end_effector_pose(np.array([cube_pos[0], cube_pos[1], cube_pos[2] + 0.2]), down_orient)
            if self.step_counter > 120:
                self.pick_phase = 1
                self.step_counter = 0
        elif self.pick_phase == 1:
            self.franka.set_end_effector_pose(np.array([cube_pos[0], cube_pos[1], cube_pos[2] + 0.1]), down_orient)
            if self.step_counter > 100:
                self.pick_phase = 2
                self.step_counter = 0
        elif self.pick_phase == 2:
            self.franka.close_gripper()
            if self.step_counter > 100:
                self.pick_phase = 3
                self.step_counter = 0
        elif self.pick_phase == 3:
            _, current_position, _ = self.franka.get_current_state()
            target = current_position + np.array([0.1, 0.0, 0.08])
            self.franka.set_end_effector_pose(position=target, orientation=down_orient)
            if self.step_counter > 150:
                self.step_counter = 0
                self.pick_phase = 4
        elif self.pick_phase == 4:
            _, current_position, _ = self.franka.get_current_state()
            target = current_position + np.array([0.1, 0.0, 0.01])
            self.franka.set_end_effector_pose(position=target, orientation=down_orient)
            if self.step_counter > 150:
                self.step_counter = 0
                self.pick_phase = 5
        elif self.pick_phase == 5:
            self.franka.open_gripper()
            if self.step_counter > 150:
                self.step_counter = 0
                self.state = 6  # Done


class HelloWorld(BaseSample):
    def __init__(self) -> None:
        super().__init__()
        self._physics_callback_id = None
        self._scenarios = []
        self._num_scenarios = 3  # Number of parallel scenarios

    def setup_scene(self):
        GroundPlane("/World/ground_plane")
        dome_light = DomeLight("/World/DomeLight")
        dome_light.set_intensities(1000)

        # Create multiple scenarios with Y-axis offsets
        for i in range(self._num_scenarios):
            offset = np.array([0.0, (i - 1) * 2.0, 0.0])  # Spread along Y-axis
            scenario = RobotScenario(name=f"scenario_{i}", offset=offset, randomize=False)
            scenario.setup_scene()
            self._scenarios.append(scenario)

    async def setup_post_load(self):
        # Initialize all scenarios
        for scenario in self._scenarios:
            scenario.initialize()

        self._physics_callback_id = SimulationManager.register_callback(
            self.physics_step, event=SimulationEvent.PHYSICS_POST_STEP
        )

    def physics_step(self, dt, context):
        # Step all scenarios
        for scenario in self._scenarios:
            scenario.step()

    async def setup_post_reset(self):
        # Reset all scenarios
        for scenario in self._scenarios:
            scenario.reset()

    def physics_cleanup(self):
        if self._physics_callback_id is not None:
            SimulationManager.deregister_callback(self._physics_callback_id)
            self._physics_callback_id = None
        self._scenarios = []
