# Copyright (c) 2022, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.

""" Proposal for ControlledArticulation interface for adding command APIs to Articulation objects.

Collaborative systems functional pipeline:
1. perception: sensor data --> entities and transforms
2. world model: entities and transforms --> USD
3. logical state monitoring: USD --> logical state
4. decisions: USD and logical state --> commands
5. command API: commands --> articulation actions
6. control: articulation --> actions to movement

These tools implement the command API. The command API is an API for commanding different subsets of
the articulation's joints. For instance, the MotionCommander (see motion_commander.py) gives a
command API for specifying target poses for the end-effector along with approach parameters and
C-space resolution parameters. Likewise, the GripperCommander (see below) gives a command API for
moving the gripper to a desired width at a specific speed. It can also close the gripper until it
feels a desired force.

These command APIs are available through the robot object added to the world and accessible from
the decision layer (inside state machines and decider networks).

See:
- commander.py for the base class interface.
- motion_commander.py and GripperCommander (below) for examples
- standalone_examples/cortex/task/{nullspace,peck_decider_netwrok,cortex_control_example}.py for
  example usage inside behaviors.
"""


from abc import abstractmethod
from collections import OrderedDict
import numpy as np
from typing import Optional, Sequence

from omni.isaac.core.objects import VisualCuboid
from omni.isaac.core.utils.nucleus import get_assets_root_path
from omni.isaac.core.utils.stage import add_reference_to_stage
from omni.isaac.core.articulations import Articulation, ArticulationSubset
from omni.isaac.cortex.commander import Commander
from omni.isaac.cortex.cortex_world import Behavior, CommandableArticulation, CortexWorld
from omni.isaac.cortex.motion_commander import MotionCommander
from omni.isaac.manipulators.grippers.surface_gripper import SurfaceGripper
from omni.isaac.motion_generation import ArticulationMotionPolicy, RmpFlowSmoothed, RmpFlow
import omni.isaac.motion_generation.interface_config_loader as icl
import omni.physics.tensors


class CortexGripper(Commander):
    """ A parallel gripper is a commander which provides a command API to controlling a parallel
    gripper.

    The two main commands are:
    1. Move-to: Servo the gripper to a specified width at a specified speed.
    2. Close-to-grasp: Close the gripper until a defined force is felt.

    These can be implemented by a general command which takes width, speed, and force parameters,
    with speed and force being optional. This class provides both a general API for these commands,
    and semantic commands such as open() close() move_to() and close_to_grasp().

    On construction, an articulation subset is given which defines which joints are controlled by
    this commander. The specific mapping from the width generalized coordinate to the joint angles
    (and back) are robot specified and need to be defined by the deriving class by overriding the
    abstract methods joints_to_width(joint_positions) and width_to_joints(width).

    Args:
        articulation_subset: The subset of joints controlled by this commander.
        opened_width: The width the gripper is opened to on open().
        closed_width: The width the gripper is closed to on close().
    """

    class Command:
        """ Specifies the command parameters, including width, speed, and force.

        Args:
            width: The width to servo the gripper to.
            speed: The speed to move at. Optional. If not specified, the underlying PD control
                defines the speed.
            force: Max contact force to control to. Optional: If not specified, this command is
                treated as a move-to servo command.
        """

        def __init__(self, width, speed=None, force=None):
            # TODO: the force is used for physical robots. Currently it's not yet implemented in
            # simulation. The action will just servo the desired position to the specified width and
            # physics will apply the force that's generated based on any contact constraints.
            self.width = width
            self.speed = speed
            self.force = force

    def __init__(self, articulation_subset, opened_width, closed_width):
        super().__init__(articulation_subset)

        self.opened_width = opened_width
        self.closed_width = closed_width

        self.width = None

    def get_width(self):
        return self.joints_to_width(self.articulation_subset.get_joint_positions())

    @abstractmethod
    def joints_to_width(self, joint_positions):
        """ Implemented by the deriving class to define how to map the joints in the articulation
        subset to the width value.
        """
        raise NotImplementedError()

    @abstractmethod
    def width_to_joints(self, width):
        """ Implemented by the deriving class to define how to map the width value to the joints in
        the articulation subset.
        """
        raise NotImplementedError()

    def move_to(self, width, speed=0.2):
        self.send(CortexGripper.Command(width, speed=speed))

    def open(self, speed=0.2):
        self.send(CortexGripper.Command(self.opened_width, speed=speed))

    def close(self, speed=0.2):
        self.send(CortexGripper.Command(self.closed_width, speed=speed))

    def close_to_grasp(self, speed=0.2, force=40.0):
        self.send(CortexGripper.Command(self.closed_width, speed=speed, force=force))

    def is_open(self, thresh=0.01):
        return self.opened_width - self.width <= thresh

    def is_closed(self, thresh=0.01):
        return self.width - self.closed_width <= thresh

    def reset(self):
        self.width = self.joints_to_width(self.articulation_subset.get_joint_positions())

    def step(self, dt):
        """ Step is called every cycle as the processing engine for the commands.
        """
        if self.command is None:
            return

        if self.command.speed is None:
            # Process the command, but clear it as well so future steps are aborted until a new
            # command is sent.
            self.articulation_subset.apply_action(joint_positions=self.width_to_joints(self.command.width))
            self.command = None

        if self.command.speed is not None:
            max_delta_width = dt * self.command.speed
            interval = self.command.width - self.width
            if abs(interval) > max_delta_width:
                delta_width = max_delta_width * interval / abs(interval)
                self.width += delta_width
            else:
                self.width = self.command.width
            self.articulation_subset.apply_action(joint_positions=self.width_to_joints(self.width))


class FrankaGripper(CortexGripper):
    """ Franka specific parallel gripper.

    Specifies the gripper joints, provides mappings from width to joints, and defines the franka
    opened and closed widths.

    Args:
        articulation: The Articulation object containing the finger joints that will be controlled
        by this parallel graipper.
    """

    def __init__(self, articulation):
        super().__init__(
            articulation_subset=ArticulationSubset(articulation, ["panda_finger_joint1", "panda_finger_joint2"]),
            opened_width=0.08,
            closed_width=0.0,
        )

    def joints_to_width(self, joint_positions):
        """ The width is simply the sum of the two prismatic joints.
        """
        return joint_positions[0] + joint_positions[1]

    def width_to_joints(self, width):
        """ Each joint is half of the width since the width is their sum.
        """
        return np.array([width / 2, width / 2])


class CortexRobot(CommandableArticulation):
    """ A robot is an Articulation with a collection of commanders commanding the collection of
    joints.

    Note: In the future, a robot will be multiple articulations (such as a mobile base, an arm, and
    a separate gripper. But for now we restrict it to a single Articulation which represents a
    single PhysX articulation.

    Note that position and orientation are both relative to the prim the robot sits on.
    """

    def __init__(
        self,
        name: str,
        prim_path: str,
        position: Optional[Sequence[float]] = None,
        orientation: Optional[Sequence[float]] = None,
    ):
        if position is None:
            position = np.zeros(3)
        super().__init__(name=name, prim_path=prim_path, translation=position, orientation=orientation)

        self.commanders_step_dt = CortexWorld.instance().get_physics_dt()
        self.commanders_reset_needed = False
        self.commanders = OrderedDict()

    def add_commander(self, name, commander, make_attr=True):
        if make_attr:
            # Makes attribute self.<name> containing the commander.
            setattr(self, name, commander)
        self.commanders[name] = commander

    def set_commanders_step_dt(self, commanders_step_dt):
        """ Set the internal dt member which is passed to each commander during their step(dt)
        calls.
        """
        self.commanders_step_dt = commanders_step_dt

    def flag_commanders_for_reset(self):
        self.commanders_reset_needed = True

    def step_commanders(self):
        if CortexWorld.instance().is_playing():
            self._reset_commanders_if_needed()
            for _, commander in self.commanders.items():
                commander.step(self.commanders_step_dt)

    def reset_commanders(self):
        for _, commander in self.commanders.items():
            commander.post_reset()

    def _reset_commanders_if_needed(self):
        """ Reset only if flagged.
        """
        if self.commanders_reset_needed:
            self.reset_commanders()
            self.commanders_reset_needed = False


class DirectSubsetCommander(Commander):
    class Command:
        def __init__(self, q, qd=None):
            self.q = q
            self.qd = qd

    def step(self, dt):
        if self.command is not None:
            self.articulation_subset.apply_action(self.command.q, self.command.qd)


class MotionCommandedRobot(CortexRobot):
    class Settings:
        def __init__(self, active_commander=True, smoothed_rmpflow=True, smoothed_commands=True):
            self.active_commander = active_commander
            self.smoothed_rmpflow = smoothed_rmpflow
            self.smoothed_commands = smoothed_commands

    def __init__(
        self,
        name: str,
        prim_path: str,
        motion_policy_config: dict,
        position: Optional[Sequence[float]] = None,
        orientation: Optional[Sequence[float]] = None,
        settings: Optional[Settings] = Settings(),
    ):
        super().__init__(name=name, prim_path=prim_path, position=position, orientation=orientation)
        self.settings = settings

        if settings.smoothed_rmpflow:
            self.motion_policy = RmpFlowSmoothed(**motion_policy_config)
        else:
            self.motion_policy = RmpFlow(**motion_policy_config)
        if self.settings.active_commander:
            articulation_motion_policy = ArticulationMotionPolicy(
                robot_articulation=self, motion_policy=self.motion_policy, default_physics_dt=self.commanders_step_dt
            )
            target_prim = VisualCuboid("/World/motion_commander_target", size=0.01, color=np.array([0.15, 0.15, 0.15]))
            self.arm_commander = MotionCommander(
                self, articulation_motion_policy, target_prim, use_smoothed_commands=self.settings.smoothed_commands
            )
        else:
            self.arm_commander = DirectSubsetCommander(ArticulationSubset(self, self.motion_policy.get_active_joints()))
        self.add_commander("arm", self.arm_commander)

    def initialize(self, physics_sim_view: omni.physics.tensors.SimulationView = None):
        super().initialize(physics_sim_view)
        self.disable_gravity()
        self.set_joints_default_state(positions=self.default_config)

    @property
    def default_config(self):
        q = np.zeros(self.num_dof)
        indices = self.arm.articulation_subset.joint_indices
        q[indices] = self.motion_policy.get_default_cspace_position_target()
        return q

    @property
    def registered_obstacles(self):
        return self.arm_commander.obstacles

    def register_obstacle(self, obs):
        self.arm_commander.add_obstacle(obs)


class CortexFranka(MotionCommandedRobot):
    """ A Franka is a ControlledArticulation with commanders for commanding the end-effector
    (governing the full arm) and the gripper (governing the fingers).

    Each of these commanders are accessible via members commander and gripper.

    Obstacles to be avoided should be added to the commander.

    This object only wraps an existing USD Franka on the stage at the specified prim_path. To
    add it to the stage first then wrap it, use the add_franka_to_stage() method.

    Note that position and orientation are both relative to the prim the Franka sits on.
    """

    def __init__(
        self,
        name: str,
        prim_path: str,
        position: Optional[Sequence[float]] = None,
        orientation: Optional[Sequence[float]] = None,
        use_motion_commander=True,
    ):
        motion_policy_config = icl.load_supported_motion_policy_config("Franka", "RMPflowCortex")
        super().__init__(
            name=name,
            prim_path=prim_path,
            motion_policy_config=motion_policy_config,
            position=position,
            orientation=orientation,
            settings=MotionCommandedRobot.Settings(
                active_commander=use_motion_commander, smoothed_rmpflow=True, smoothed_commands=True
            ),
        )

        self.gripper_commander = FrankaGripper(self)
        self.add_commander("gripper", self.gripper_commander)

    def initialize(self, physics_sim_view: omni.physics.tensors.SimulationView = None):
        super().initialize(physics_sim_view)

        verbose = True
        kps = np.array([6000000.0, 6000000.0, 6000000.0, 6000000.0, 2500000.0, 1500000.0, 500000.0, 6000.0, 6000.0])
        kds = np.array([300000.0, 300000.0, 300000.0, 300000.0, 90000.0, 90000.0, 90000.0, 1000.0, 1000.0])
        if verbose:
            print("setting franka gains:")
            print("- kps: {}".format(kps))
            print("- kds: {}".format(kds))
        self.get_articulation_controller().set_gains(kps, kds)


def add_franka_to_stage(
    name: str,
    prim_path: str,
    usd_path: Optional[str] = None,
    position: Optional[Sequence[float]] = None,
    orientation: Optional[Sequence[float]] = None,
    use_motion_commander=True,
):
    """ Adds a Franka to the stage at the specified prim_path, then wrap it as a Franka object.

    Note that position and orientation are both relative to the prim the Franka sits on.

    Returns the Franka object.
    """
    if usd_path is not None:
        add_reference_to_stage(usd_path=usd_path, prim_path=prim_path)
    else:
        # Use the default USD
        assets_root_path = get_assets_root_path()
        if assets_root_path is None:
            raise RuntimeError("Could not find Isaac Sim assets folder")
        usd_path = assets_root_path + "/Isaac/Robots/Franka/franka.usd"
        add_reference_to_stage(usd_path=usd_path, prim_path=prim_path)

    return CortexFranka(name, prim_path, position, orientation, use_motion_commander)


class CortexUr10(MotionCommandedRobot):
    """ A Franka is a ControlledArticulation with commanders for commanding the end-effector
    (governing the full arm) and the gripper (governing the fingers).

    Each of these commanders are accessible via members commander and gripper.

    Obstacles to be avoided should be added to the commander.

    This object only wraps an existing USD Franka on the stage at the specified prim_path. To
    add it to the stage first then wrap it, use the add_franka_to_stage() method.

    Note that position and orientation are both relative to the prim the Franka sits on.
    """

    def __init__(
        self,
        name: str,
        prim_path: str,
        position: Optional[Sequence[float]] = None,
        orientation: Optional[Sequence[float]] = None,
    ):
        motion_policy_config = icl.load_supported_motion_policy_config("UR10", "RMPflowCortex")
        super().__init__(
            name=name,
            prim_path=prim_path,
            motion_policy_config=motion_policy_config,
            position=position,
            orientation=orientation,
            settings=MotionCommandedRobot.Settings(smoothed_rmpflow=False, smoothed_commands=False),
        )

        self._end_effector_prim_path = prim_path + "/ee_link"
        self.suction_gripper = SurfaceGripper(
            end_effector_prim_path=self._end_effector_prim_path, translate=0.162, direction="x"
        )

    def initialize(self, physics_sim_view=None):
        super().initialize(physics_sim_view)
        self.suction_gripper.initialize(physics_sim_view=physics_sim_view, articulation_num_dofs=self.num_dof)

    def post_reset(self) -> None:
        super().post_reset()
