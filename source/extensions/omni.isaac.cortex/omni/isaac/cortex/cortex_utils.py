# Copyright (c) 2022, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.

from collections import OrderedDict
import numpy as np

from lula_ros.msg import JointPosVelAccCommand
from std_msgs.msg import Header

from omni.isaac.core import World
from omni.isaac.core.objects import VisualCuboid, DynamicCuboid
from omni.isaac.core.prims import XFormPrim
from omni.isaac.core.utils.nucleus import find_nucleus_server
from omni.isaac.core.utils.prims import (
    get_prim_at_path,
    get_prim_path,
    get_prim_children,
    define_prim,
    is_prim_path_valid,
)
from omni.isaac.core.utils.stage import get_stage_units, add_reference_to_stage
from omni.isaac.core.utils.types import JointsState, ArticulationAction
from omni.isaac.franka import Franka
from omni.isaac.motion_generation import MotionPolicyController, RmpFlowSmoothed
import omni.isaac.motion_generation.interface_config_loader as icl
from pxr import Sdf, Gf, UsdPhysics, UsdGeom, Usd
from pxr.Vt import Bool, Double

from motion_commander import MotionCommander

# TODO: organize this file to group methods / classes and add comments about context.


def make_target_prim(prim_path="/cortex/world/motion_controller_target"):
    width = 0.01
    target_prim = VisualCuboid(
        prim_path, size=100.0 * np.array([width, width, width]), color=np.array([0.15, 0.15, 0.15])
    )
    return target_prim


def add_end_effector_prim_to_franka(
    motion_commander, hand_prim_path="/cortex/world/franka/panda_hand", eff_prim_name="eff"
):
    eff_prim_path = hand_prim_path + "/" + eff_prim_name

    # Only add the prim if it doesn't already exist.
    if not is_prim_path_valid(eff_prim_path):
        print("No end effector detected. Adding one.")
        eff_prim = define_prim(prim_path=eff_prim_path, prim_type="Xform")
        xformable = UsdGeom.Xformable(eff_prim)
        xformable.AddXformOp(UsdGeom.XformOp.TypeTranslate, UsdGeom.XformOp.PrecisionDouble, "")
        xformable.AddXformOp(UsdGeom.XformOp.TypeOrient, UsdGeom.XformOp.PrecisionDouble, "")

        pose = motion_commander.calc_policy_eff_pose_rel_to_hand(hand_prim_path)
        p = pose.p / get_stage_units()
        q = pose.q

        transform = Gf.Transform()
        eff_prim.GetAttribute("xformOp:translate").Set(Gf.Vec3d(*p.tolist()))
        eff_prim.GetAttribute("xformOp:orient").Set(Gf.Quatd(*q.tolist()))
    else:
        print("End effector prim already exists.")


def build_motion_commander(physics_dt, robot, obstacles):
    motion_policy = RmpFlowSmoothed(**icl.load_supported_motion_policy_config("Franka", "RMPflowSmoothed"))

    # Setup the robot commander and replace its (xform) target prim with a visible version.
    motion_policy_controller = MotionPolicyController(
        name="rmpflow_controller",
        robot_prim_path="/cortex/world/franka",
        motion_policy=motion_policy,
        physics_dt=physics_dt,
    )
    target_prim = make_target_prim()
    commander = MotionCommander(robot, motion_policy_controller, target_prim)

    add_end_effector_prim_to_franka(commander)
    commander.add_obstacles(obstacles)

    return commander


class PosVel:
    def __init__(self, pos, vel):
        self.pos = pos
        self.vel = vel

    def __str__(self):
        return "\nq: %s\nqd: %s" % (str(self.pos), str(self.vel))


def find_nucleus_server_with_error_checks():
    result, nucleus_server = find_nucleus_server()
    if result is False:
        err_str = "Could not find nucleus server with /Isaac folder"
        carb.log_error(err_str)
        raise RuntimeError(err_str)
    return nucleus_server


class RobotInfo:
    def __init__(self, robot, verbose=False):
        # TODO: The robot object itself should know how many of its joints are active. Should also
        # have meta information about control decomposition (i.e. how the gripper works vs how the
        # arm works).
        self.robot = robot
        self.num_active_joints = 7

        self.active_joint_names = [
            name for (i, name) in enumerate(self.robot._dofs_infos) if i < self.num_active_joints
        ]
        self.joint_names = list(self.robot._dofs_infos)

        if verbose:
            for i, name in enumerate(self.active_joint_names):
                print("%d) n: %s" % (i, name))


def set_default_config_to_retracted(robot):
    retracted_config = np.array([0.00, -1.3, 0.00, -2.87, 0.00, 2.00, 0.75, 0.0, 0.0])
    robot.set_joints_default_state(positions=retracted_config)


def try_load_robot(prim_path, verbose=False):

    """ Try to load a robot at a given prim path. If the robot isn't there, then it returns None.
    Otherwise, it creates a Franka object wrapping the USD, initializes its handles, and returns it
    in a RobotInfo object. This method should only be called once dynamic control has been
    initialized (i.e. after the first call to world.reset().)
    """

    if get_prim_at_path(prim_path).IsValid():
        if verbose:
            print("Robot found at path:", prim_path)
        robot = Franka(prim_path=prim_path, name="robot")
        robot.initialize()

        if verbose:
            articulation_controller = robot.get_articulation_controller()
            kps, kds = articulation_controller.get_gains()
            print("Robot loaded. Gains:")
            print("kps:", kps)
            print("kds:", kds)

        return RobotInfo(robot, verbose)
    else:
        if verbose:
            print("No robot found at path:", prim_path)

    return None


def scale_gains(robot, kp_scalar=1.0, kd_scalar=1.0, indices=None, verbose=False):
    if verbose:
        print("...")
        print("scaling gains on robot:", robot.name)
    if indices is None:
        indices = list(range(robot.num_dof))

    articulation_controller = robot.get_articulation_controller()
    kps, kds = articulation_controller.get_gains()
    if verbose:
        print("kps_orig:", kps)
        print("kds_orig:", kds)

    kps[indices] *= kp_scalar
    kds[indices] *= kd_scalar
    articulation_controller.set_gains(kps, kds)
    kps_new, kds_new = articulation_controller.get_gains()

    if verbose:
        print("kps_new:", kps_new)
        print("kds_new:", kds_new)


def configure_franka(robot, verbose=False):
    """ Disable gravity on the Franka robot and set the gains. This method has to be called after
    the first call to world.reset().
    """
    robot.disable_gravity()

    # Scale the kd gains down for the wrist joints of the robot. Don't include the fingers.
    n = robot.num_dof
    indices = list(range(robot.num_dof))[4 : (n - 2)]
    scale_gains(robot, kd_scalar=0.3, indices=indices, verbose=verbose)

    # Scale all gains up by a factor. Just make the robot stiffer.
    indices = list(range(robot.num_dof))[0 : (n - 2)]
    scale_gains(robot, kp_scalar=100.0, kd_scalar=100.0, indices=indices, verbose=verbose)


def extract_joint_state_subset(joint_state, indices):
    return JointsState(joint_state.positions[indices], joint_state.velocities[indices], joint_state.efforts[indices])


class JointSubsetCommand:
    def __init__(self, topic, indices):
        self.topic = topic
        self.indices = indices

    def pack_msg(self, joint_names, action, msg_id, stamp, period):
        msg = JointPosVelAccCommand()
        msg.period = period

        msg.id = msg_id
        msg.header = Header()
        msg.header.seq = msg_id
        msg.header.stamp = stamp

        q = action.joint_positions[self.indices]
        qd = action.joint_velocities[self.indices]

        msg.q = q
        msg.qd = qd
        # TODO: hack - convert this back to []. Adding this here as a hack to get it to work with an
        # old build of lula_ros_franka.
        msg.qdd = np.zeros(len(qd))
        msg.names = [joint_names[i] for i in self.indices]
        msg.t = stamp

        return msg


def get_standard_split_joint_subset_commands(robot_info):
    """ Returns two subsets of joint commands, "active" joints controlled by the RMPs and "inactive"
    joints sent to a gripper controller.
    """
    n = robot_info.num_active_joints
    m = robot_info.robot.num_dof
    joint_subsets_commands = OrderedDict()
    joint_subsets_commands["arm"] = JointSubsetCommand("/rmpflow/commands/joint_command", list(range(0, n)))
    joint_subsets_commands["gripper"] = JointSubsetCommand("/rmpflow/commands/gripper", list(range(n, m)))
    return joint_subsets_commands


# TODO: verify these attributes don't already exist
def add_cortex_attributes_to_robot(robot, is_suppressed, adaptive_cycle_dt):
    robot_prim = get_prim_at_path(robot.prim_path)
    robot_prim.CreateAttribute("cortex:is_suppressed", Sdf.ValueTypeNames.Bool, False).Set(Bool(False))
    robot_prim.CreateAttribute("cortex:adaptive_cycle_dt", Sdf.ValueTypeNames.Double, False).Set(
        Double(adaptive_cycle_dt)
    )


def add_cortex_attributes_to_object_if_needed(obj):
    prim = obj.prim
    if not prim.HasAttribute("cortex:measured_pose:position"):
        prim.CreateAttribute("cortex:measured_pose:position", Sdf.ValueTypeNames.Vector3d, False).Set(
            Gf.Vec3d(0.0, 0.0, 0.0)
        )
    if not prim.HasAttribute("cortex:measured_pose:orient"):
        prim.CreateAttribute("cortex:measured_pose:orient", Sdf.ValueTypeNames.Quatd, False).Set(
            Gf.Quatd(1.0, 0.0, 0.0, 0.0)
        )
    if not prim.HasAttribute("cortex:measured_pose:stamp"):
        prim.CreateAttribute("cortex:measured_pose:stamp", Sdf.ValueTypeNames.Double, False).Set(Double(0.0))
    if not prim.HasAttribute("cortex:measured_pose:timeout"):
        prim.CreateAttribute("cortex:measured_pose:timeout", Sdf.ValueTypeNames.Double, False).Set(Double(-1.0))
    if not prim.HasAttribute("cortex:sync_sim"):
        prim.CreateAttribute("cortex:sync_sim", Sdf.ValueTypeNames.Bool, False).Set(Bool(False))


def add_cortex_attributes_to_objects_if_needed(objects):
    for _, obj in objects.items():
        add_cortex_attributes_to_object_if_needed(obj)


def load_cortex_default_world():
    world = World(stage_units_in_meters=0.01)
    world.scene.add_default_ground_plane()
    return world


def make_empty_world():
    world = World(stage_units_in_meters=0.01)
    return world


def set_robot_default_config_to_retracted(robot):
    retracted_config = np.array([0.00, -1.3, 0.00, -2.87, 0.00, 2.00, 0.75, 0.0, 0.0])
    robot.set_joints_default_state(positions=retracted_config)


def load_franka_to_stage(robot_name="franka", prim_path="/cortex/world/franka"):
    result, nucleus_server = find_nucleus_server()
    if result is False:
        raise RuntimeError("Could not find nucleus server with /Isaac folder")

    asset_path = nucleus_server + "/Isaac/Robots/Franka/franka_alt_fingers.usd"
    add_reference_to_stage(usd_path=asset_path, prim_path=prim_path)


def make_franka(robot_name="franka", prim_path="/cortex/world/franka", load_if_not_found=False):
    # If the prim path already exists, then just use that. Otherwise, load the default robot and
    if is_prim_path_valid(prim_path):
        robot = Franka(prim_path=prim_path, name=robot_name)
    elif load_if_not_found:
        load_franka_to_stage(robot_name=robot_name, prim_path=prim_path)
        robot = Franka(usd_path=asset_path, prim_path=prim_path, name=robot_name)
    else:
        raise RuntimeError("Franka not found at prim path: " + prim_path)

    return robot


# TODO: move to a repro of the issues
def add_cortex_franka_to_world(world, robot_name="franka", prim_path="/cortex/world/franka", load_if_not_found=False):
    """ Adds a cortex configured Franka robot to the world. By default, if the robot isn't found
    at the specified prim_path in the USD stage, an error is thrown. If load_if_not_found is set to
    True, then it will load a default version of the robot one is not already found at the specified
    prim_path.
    """

    robot = world.scene.add(
        make_franka(robot_name=robot_name, prim_path=prim_path, load_if_not_found=load_if_not_found)
    )
    world.reset()

    configure_franka(robot, verbose=True)
    physics_dt = world.get_physics_dt()
    add_cortex_attributes_to_robot(robot, is_suppressed=False, adaptive_cycle_dt=physics_dt)

    set_robot_default_config_to_retracted(robot)
    world.reset()

    return robot


# TODO: move to a repro of the issues
def add_franka_to_world(world, robot_name="franka", prim_path="/cortex/world/franka"):
    """ Adds the franka robot at the specified prim path to the world's scene without modification
    (aside from setting the default config).  Returns the resulting Franka object. If no prim is
    found at that path, returns None.  """

    if is_prim_path_valid(prim_path):
        robot = world.scene.add(Franka(prim_path=prim_path, name=robot_name))
        world.reset()
        set_robot_default_config_to_retracted(robot)
        world.reset()

        return robot
    return None


# TODO: reconcile make_franka with the above
def make_franka(robot_name, prim_path):
    if not is_prim_path_valid(prim_path):
        return None

    robot = Franka(prim_path=prim_path, name=robot_name)
    robot.initialize()
    configure_franka(robot, verbose=True)

    return robot


def make_cortex_franka_or_die2(robot_name, prim_path, physics_dt):
    robot = make_franka(robot_name, prim_path)
    if robot is None:
        raise RuntimeError("Robot not found at prim path:" + prim_path)
    configure_franka(robot, verbose=True)
    add_cortex_attributes_to_robot(robot, is_suppressed=False, adaptive_cycle_dt=physics_dt)

    return robot


def wrap_cortex_franka_or_die(world, robot_name, prim_path, physics_dt):
    if not is_prim_path_valid(prim_path):
        return None

    robot = world.scene.add(Franka(prim_path=prim_path, name=robot_name))
    world.reset()

    configure_franka(robot, verbose=True)
    add_cortex_attributes_to_robot(robot, is_suppressed=False, adaptive_cycle_dt=physics_dt)

    return robot


def is_a_rigid_prim(prim):
    return prim.HasAPI(UsdPhysics.RigidBodyAPI) and prim.HasAPI(UsdPhysics.MassAPI)


def make_core_object_from_prim(prim_path, name):
    prim = get_prim_at_path(prim_path)
    if prim.IsA(UsdGeom.Cube):
        if is_a_rigid_prim(prim):
            return DynamicCuboid(prim_path=prim_path, name=name)
        else:
            return FixedCuboid(prim_path=prim_path, name=name)
    return XFormPrim(prim_path=prim_path, name=name)


def make_core_objects(domain="world", additional_paths={}, verbose=False):
    """ Creates an objects dict mapping object name to XFormPrim wrapping existing xform prims in
    the stage.
    
    Looks up a collection of objects at the specified stage path and creates XFormPrim wrappers for
    them. Adds them to an objects dict mapping the name (under the objects_path) to the XFormPrim
    object. Creates XFormPrim objects for each path specified in the additional_paths dict as well,
    using the key from that dict as the key for the new objects dict. Returns the resulting objects
    dict.
    """

    objects_path = "/cortex/%s/objects" % domain

    objects = {}
    obstacles = {}
    if is_prim_path_valid(objects_path):
        if verbose:
            print("core objs path is valid:", objects_path)
        objects_prim = get_prim_at_path(objects_path)
        prim_children = get_prim_children(objects_prim)
        for prim in prim_children:
            prim_path = get_prim_path(prim)

            name = prim_path[len(objects_path + "/") :]
            if domain != "world":
                name = domain + "_" + name
            print("adding object:", name)
            objects[name] = make_core_object_from_prim(prim_path=prim_path, name=name)

            is_obs_attr = "cortex:is_obstacle"
            if prim.HasAttribute(is_obs_attr) and prim.GetAttribute(is_obs_attr).Get():
                print("Adding object prim as obstacle:", prim_path)
                obstacles[name] = objects[name]
    else:
        print("core objs path is invalid:", objects_path)

    for name, path in additional_paths.items():
        objects[name] = make_core_object_from_prim(prim_path=path, name=name)

    return objects, obstacles


class NamedColor:
    def __init__(self, name, color):
        self.name = name
        self.color = np.array(color)


def add_blocks_to_scene(domain):
    stage_units = get_stage_units()

    c = 0.3
    color_sequence = [
        NamedColor("red", (c, 0.0, 0.0)),
        NamedColor("yellow", (c, c, 0.0)),
        NamedColor("green", (0.0, c, 0)),
        NamedColor("blue", (0.0, 0.0, c)),
    ]

    side = 0.0515  # Taken from old gtc china 2019 script
    obj_dims = np.array([side, side, side])

    start_p = np.array([0.25, -0.4, 0.025])
    blocks = {}
    for i, named_color in enumerate(color_sequence):
        p = start_p + i * np.array([0.3 / (len(color_sequence) - 1), 0.0, 0.0])
        q = np.array([1.0, 0.0, 0.0, 0.0])

        path_prefix = "/cortex/%s/objects" % domain
        name = "%s_block" % named_color.name
        path = "%s/%s" % (path_prefix, name)
        blocks[name] = DynamicCuboid(
            prim_path=path,
            name=name,
            mass=0.05,
            translation=p / stage_units,
            orientation=q,
            size=obj_dims / stage_units,
            color=named_color.color,
            static_friction=2.0,
            dynamic_friction=2.0,
        )

    return blocks
