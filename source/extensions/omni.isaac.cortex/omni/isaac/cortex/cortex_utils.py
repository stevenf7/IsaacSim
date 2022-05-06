# Copyright (c) 2022, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.

import numpy as np

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
from omni.isaac.universal_robots import UR10
from omni.isaac.motion_generation import MotionPolicyController, ArticulationMotionPolicy, RmpFlowSmoothed
import omni.isaac.motion_generation.interface_config_loader as icl
from pxr import Sdf, Gf, UsdPhysics, UsdGeom, Usd
from pxr.Vt import Bool, Double

from motion_commander import MotionCommander
from math_util import to_stage_units


def find_nucleus_server_with_error_checks():
    result, nucleus_server = find_nucleus_server()
    if result is False:
        err_str = "Could not find nucleus server with /Isaac folder"
        carb.log_error(err_str)
        raise RuntimeError(err_str)
    return nucleus_server


class PosVel:
    def __init__(self, pos, vel):
        self.pos = pos
        self.vel = vel

    def __str__(self):
        return "\nq: %s\nqd: %s" % (str(self.pos), str(self.vel))


class RobotInfo:
    def __init__(self, robot, verbose=False):
        self.robot = robot
        self.num_active_joints = get_num_arm_controlled_dofs(robot)

        self.active_joint_names = [
            name for (i, name) in enumerate(self.robot._dofs_infos) if i < self.num_active_joints
        ]
        self.joint_names = list(self.robot._dofs_infos)

        if verbose:
            for i, name in enumerate(self.active_joint_names):
                print("%d) n: %s" % (i, name))


def add_cortex_attributes_to_robot(robot, is_suppressed, adaptive_cycle_dt):
    robot_prim = get_prim_at_path(robot.prim_path)
    robot_prim.CreateAttribute("cortex:is_suppressed", Sdf.ValueTypeNames.Bool, False).Set(Bool(False))
    robot_prim.CreateAttribute("cortex:adaptive_cycle_dt", Sdf.ValueTypeNames.Double, False).Set(
        Double(adaptive_cycle_dt)
    )


def add_cortex_attributes_to_object_if_needed(obj):
    prim = obj.prim
    prim.CreateAttribute("cortex:measured_pose:position", Sdf.ValueTypeNames.Vector3d, False).Set(
        Gf.Vec3d(0.0, 0.0, 0.0)
    )
    prim.CreateAttribute("cortex:measured_pose:orient", Sdf.ValueTypeNames.Quatd, False).Set(
        Gf.Quatd(1.0, 0.0, 0.0, 0.0)
    )
    prim.CreateAttribute("cortex:measured_pose:stamp", Sdf.ValueTypeNames.Double, False).Set(Double(0.0))
    prim.CreateAttribute("cortex:measured_pose:timeout", Sdf.ValueTypeNames.Double, False).Set(Double(-1.0))
    prim.CreateAttribute("cortex:sync_sim", Sdf.ValueTypeNames.Bool, False).Set(Bool(False))


def add_cortex_attributes_to_objects_if_needed(objects):
    for _, obj in objects.items():
        add_cortex_attributes_to_object_if_needed(obj)


def get_robot_type(prim_path):
    robot_prim = get_prim_at_path(prim_path)
    robot_type = robot_prim.GetAttribute("cortex:robot_type").Get()
    return robot_type


def get_robot_hand_prim_path(robot):
    if isinstance(robot, Franka):
        return "/cortex/belief/robot/panda_hand"
    elif isinstance(robot, UR10):
        return "/cortex/belief/robot/ee_link"
    else:
        raise RuntimeError("unrecognized robot: %s" % str(robot))


def make_target_prim(prim_path="/cortex/belief/motion_controller_target"):
    width = 0.01
    target_prim = VisualCuboid(
        prim_path, size=100.0 * np.array([width, width, width]), color=np.array([0.15, 0.15, 0.15])
    )
    return target_prim


def set_home_config(robot):
    if isinstance(robot, Franka):
        home_config = np.array([0.00, -1.3, 0.00, -2.87, 0.00, 2.00, 0.75, 0.0, 0.0])
    elif isinstance(robot, UR10):
        # Using UR10's underlying default config as the home config.
        home_config = robot.get_joints_default_state().positions
    else:
        raise RuntimeError("unrecognized robot: %s" % str(robot))

    robot.set_joints_default_state(positions=home_config)


def get_num_arm_controlled_dofs(robot):
    """ These robots are often serial link manipulators followed by a gripper. At times, the gripper
    is part of the same USD, such as in the case of the Franka, with the arm degrees of freedom
    (DOFs) controlled differently from the gripper DOFs. In those cases, the arm DOFs are listed
    first and are a subset of the total number of DOFs. This method returns the number of arm
    controlled DOFs so we can distinguish between which DOFs are controlled by the arm and which are
    controlled separately (e.g. by the gripper controller).
    """

    if isinstance(robot, Franka):
        return 7  # The Franka consists of the 7-dof arm with a distal gripper.
    elif isinstance(robot, UR10):
        return 6  # UR robots are 6-dof arms.
    else:
        raise RuntimeError("unrecognized robot: %s" % str(robot))


def add_end_effector_prim_to_robot(motion_commander, hand_prim_path, eff_prim_name):
    eff_prim_path = hand_prim_path + "/" + eff_prim_name

    # Only add the prim if it doesn't already exist.
    if not is_prim_path_valid(eff_prim_path):
        print("No end effector detected. Adding one.")
        eff_prim = define_prim(prim_path=eff_prim_path, prim_type="Xform")
        xformable = UsdGeom.Xformable(eff_prim)
        xformable.AddXformOp(UsdGeom.XformOp.TypeTranslate, UsdGeom.XformOp.PrecisionDouble, "")
        xformable.AddXformOp(UsdGeom.XformOp.TypeOrient, UsdGeom.XformOp.PrecisionDouble, "")

        pose = motion_commander.calc_policy_eff_pose_rel_to_hand(hand_prim_path)
        p = to_stage_units(pose.p)
        q = pose.q

        transform = Gf.Transform()
        eff_prim.GetAttribute("xformOp:translate").Set(Gf.Vec3d(*p.tolist()))
        eff_prim.GetAttribute("xformOp:orient").Set(Gf.Quatd(*q.tolist()))
    else:
        print("End effector prim already exists.")


def build_motion_commander(physics_dt, robot, obstacles):
    motion_policy = RmpFlowSmoothed(
        **icl.load_supported_motion_policy_config(robot.__class__.__name__, "RMPflowCortex")
    )

    # Setup the robot commander and replace its (xform) target prim with a visible version.
    motion_policy_controller = MotionPolicyController(
        name="rmpflow_controller",
        articulation_motion_policy=ArticulationMotionPolicy(
            robot_articulation=robot, motion_policy=motion_policy, physics_dt=physics_dt
        ),
    )
    target_prim = make_target_prim()
    commander = MotionCommander(robot, motion_policy_controller, target_prim)

    hand_prim_path = get_robot_hand_prim_path(robot)
    add_end_effector_prim_to_robot(commander, hand_prim_path, "eff")
    commander.add_obstacles(obstacles)

    return commander


def scale_gains_franka(robot, kp_scalar=1.0, kd_scalar=1.0, indices=None, verbose=False):
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
    scale_gains_franka(robot, kd_scalar=0.3, indices=indices, verbose=verbose)

    # Scale all gains up by a factor. Just make the robot stiffer.
    indices = list(range(robot.num_dof))[0 : (n - 2)]
    scale_gains_franka(robot, kp_scalar=100.0, kd_scalar=100.0, indices=indices, verbose=verbose)


def configure_ur10(robot, verbose=False):
    """ Disable gravity on the UR10 robot and set the gains (todo). This method has to be called after
    the first call to world.reset().
    """
    robot.disable_gravity()


def configure_robot(robot, verbose=False):
    if isinstance(robot, Franka):
        print("<configuring franka>")
        configure_franka(robot, verbose=verbose)
    elif isinstance(robot, UR10):
        print("<configuring ur10>")
        configure_ur10(robot, verbose=verbose)
    else:
        raise RuntimeError("unrecognized robot: %s" % str(robot))


def extract_joint_state_subset(joint_state, indices):
    return JointsState(joint_state.positions[indices], joint_state.velocities[indices], joint_state.efforts[indices])


def make_empty_world():
    world = World(stage_units_in_meters=0.01)
    return world


def make_cortex_default_world():
    world = World(stage_units_in_meters=0.01)
    world.scene.add_default_ground_plane()
    return world


def load_franka_to_stage(robot_name="franka", prim_path="/cortex/belief/robot"):
    nucleus_server = find_nucleus_server_with_error_checks()

    asset_path = nucleus_server + "/Isaac/Robots/Franka/franka_alt_fingers.usd"
    add_reference_to_stage(usd_path=asset_path, prim_path=prim_path)


def wrap_robot(domain, robot_type, prim_path):
    robot_name = "%s_%s" % (robot_type, domain)
    print(">> wrap robot:", robot_name)

    if robot_type == "franka":
        print("<wrapping franka>")
        robot = Franka(prim_path=prim_path, name=robot_name)
    elif robot_type == "ur10":
        print("<wrapping ur10>")
        robot = UR10(prim_path=prim_path, name=robot_name, attach_gripper=True)
    else:
        raise RuntimeError("unrecognized robot: %s" % robot_type)

    return robot


def try_wrap_cortex_robot(domain):
    prim_path = "/cortex/%s/robot" % domain
    if not is_prim_path_valid(prim_path):
        return None
    robot_type = get_robot_type(prim_path)
    robot = wrap_robot(domain, robot_type, prim_path)
    return robot


def wrap_cortex_robot_or_die(domain):
    robot = try_wrap_cortex_robot(domain)
    if robot is None:
        raise RuntimeError("could not find %s robot" % domain)
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


def make_core_objects(domain="belief", additional_paths={}, verbose=False):
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
            if domain != "belief":
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


# ==============================================================================
# Blocks world creation utilities
# ==============================================================================


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
