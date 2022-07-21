# Copyright (c) 2022, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.

""" Cortex-specific utilities and helper methods
"""

import numpy as np

from omni.isaac.core import World
from omni.isaac.core.objects import VisualCuboid, DynamicCuboid
from omni.isaac.core.prims import XFormPrim
from omni.isaac.core.utils.nucleus import get_assets_root_path
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

from omni.isaac.cortex.motion_commander import MotionCommander
from omni.isaac.cortex.math_util import to_stage_units

import carb


def find_assets_root_path_with_error_checks():
    """ Find the assets root path and check for errors.

    Raises a runtime error if the assets root could not be found. Otherwise, returns the asset
    root path.
    """
    assets_root_path = get_assets_root_path()
    if assets_root_path is None:
        err_str = "Could not find Isaac Sim assets folder"
        carb.log_error(err_str)
        raise RuntimeError(err_str)
    return assets_root_path


class PosVel:
    """ Convenient paring of a position and velocity. Provides a string conversion method which
    gives it semantics of configuration q: <pos>\n qd: <vel>.
    """

    def __init__(self, pos, vel):
        self.pos = pos
        self.vel = vel

    def __str__(self):
        return "\nq: %s\nqd: %s" % (str(self.pos), str(self.vel))


class RobotInfo:
    """ Collected information about a robot useful for handling robots in extensions.
    """

    def __init__(self, robot, verbose=False):
        self.robot = robot
        self.is_configured = False
        self.verbose = verbose

        self.num_active_joints = get_num_arm_controlled_dofs(robot)

    @property
    def joint_names(self):
        """ The names of the joints.
        """
        return self.robot.dof_names

    @property
    def ready_to_configure(self):
        """ Is true if the robot handles are initialized. This will happen only once world.reset() is
        called for the first time.
        """
        return self.robot.handles_initialized

    def configure(self):
        """ Extract the active joint names and set the property self.is_configured to True.

        Verify the robot object is ready to be configured using a call to self.ready_to_configure()
        before calling this method. 
        """
        self.active_joint_names = [name for (i, name) in enumerate(self.robot.dof_names) if i < self.num_active_joints]

        if self.verbose:
            for i, name in enumerate(self.active_joint_names):
                print("%d) n: %s" % (i, name))
        self.is_configured = True


def add_cortex_attributes_to_robot(robot, is_suppressed, adaptive_cycle_dt):
    """ Add cortex attributes to the robot USD.

    Cortex attributes:
    - cortex:is_suppressed -- True when the robot is being actively suppressed by an external
      controller during the syncing process.
    - cortex:adaptive_cycle_dt -- The current adaptive cycle dt used in the motion commander. This
      value synchronizes online with the the controller so the effective clock of cortex matches the
      real world wall-clock time independent of whether the cortex system is running slow/fast, or
      whether the clocks between the cortex machine and the control machine run at slightly
      different rates.

    Note there is also a cortex:robot_type attribute that should be added to each robot. But that
    attribute needs to be added manually to the robot USD to specify to the cortex system what type
    of robot the USD prim represents.
    """
    robot_prim = get_prim_at_path(robot.prim_path)
    robot_prim.CreateAttribute("cortex:is_suppressed", Sdf.ValueTypeNames.Bool, False).Set(Bool(False))
    robot_prim.CreateAttribute("cortex:adaptive_cycle_dt", Sdf.ValueTypeNames.Double, False).Set(
        Double(adaptive_cycle_dt)
    )


def add_cortex_attributes_to_object(obj):
    """ Add cortex attributes to the underlying prim of the provided core API object.

    Cortex attributes:
    - cortex:measured_pose:position -- Position vector of the measured pose in meters.
    - cortex:measured_pose:orient -- Orientation quaternion of the measured pose.
    - cortex:measured_pose:stamp -- Timestamp of the measured pose from the incoming message.
    - cortex:measured_pose:timeout -- Timeout. Duration the measured pose is valid.
    - cortex:sync_sim -- A command (suggestion) from the behavior script to the cortex_sim extension
      to synchronize the simulated poses with the belief poses. Useful when resetting the world from
      the behavior script which runs independently of whether a simulated world is available.
    """

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


def add_cortex_attributes_to_objects(objects):
    """ Add cortex attributes to all objects in the provided objects dictionary.

    See also add_cortex_attributes_to_object()
    """
    for _, obj in objects.items():
        add_cortex_attributes_to_object(obj)


def get_robot_type(prim_path):
    """Returns the cortex:robot_type attribute's value from the provided prim path.

    Does not check whether the attribute exists; will thrown an exception if not.
    """
    robot_prim = get_prim_at_path(prim_path)
    robot_type = robot_prim.GetAttribute("cortex:robot_type").Get()
    return robot_type


def get_robot_hand_prim_path(robot):
    """ Returns the prim path to the prim of the robot considered to be the hand. This prim is the
    prim the end-effector is rigidly attached to (specifically the command frame used by the motion
    commander).
    """
    if isinstance(robot, Franka):
        return "/cortex/belief/robot/panda_hand"
    elif isinstance(robot, UR10):
        return "/cortex/belief/robot/ee_link"
    else:
        raise RuntimeError("unrecognized robot: %s" % str(robot))


def make_target_prim(prim_path="/cortex/belief/motion_controller_target"):
    """ Create the prim to be used as the motion controller target and add it to the stage.

    Creates a visible grey cube with 1cm sides.
    """
    width = 0.01
    target_prim = VisualCuboid(prim_path, size=to_stage_units(width), color=np.array([0.15, 0.15, 0.15]))
    return target_prim


def set_home_config(robot):
    """ Set the home configuration of the specified robot.

    Currently only supports Franka and UR10 robot types. Uses the underlying Articulation object's
    default state property, so the robots return to this home configuration when world.reset() is
    called.
    """
    if isinstance(robot, Franka):
        home_config = np.array([0.00, -1.3, 0.00, -2.87, 0.00, 2.00, 0.75, 0.0, 0.0])
    elif isinstance(robot, UR10):
        home_config = np.array([-np.pi / 2, -np.pi / 2, -np.pi / 2, -np.pi / 2, np.pi / 2, 0])
    else:
        raise RuntimeError("unrecognized robot: %s" % str(robot))

    robot.set_joints_default_state(positions=home_config)


def get_num_arm_controlled_dofs(robot):
    """ Returns the number of (proximal) degrees of freedom that will be controlled by the motion
    policy underlying the motion commander. 
    
    These robots are often serial link manipulators followed by a gripper. At times, the gripper
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
    """ Add an end-effector prim as a child of the specified hand prim.

    In general, a motion policy consuming commands from the motion commander may not use an
    end-effector explicitly represented as a prim in the underlying robot USD. This method measures
    the location of the underlying policy's end-effector, computes the relative transform between
    the specified hand prim and that end-effector, and adds an explicit end-effector prim as a child
    of the hand prim to represent the end-effector in USD.

    This call uses MotionCommander.calc_policy_eff_pose_rel_to_hand(hand_prim_path) to calculate
    where the end-effector transform used by the underlying motion policy is relative to the
    specified hand prim.

    The end-effector prim is added to the path <hand_prim_path>/<eff_prim_name>
    """
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
    """ Build the motion commander object.

    Creates an RmpFlowSmoothed motion policy to govern the motion generation using the
    RMPflowCortex motion policy config. This policy is a wrapped version of RmpFlowSmoothed which
    measures jerk and both dynamically adjusts the system's speed if a large jerk is predicted,
    and truncates small/medium sized jerks.

    Also, adds the target prim, adds end-effector prim to the hand prim returned by
    get_robot_hand_prim_path(robot), and adds the provided obstacles to the underlying policy.

    Params:
    - physics_dt: The time delta used by physics in seconds. Default: 1./60 seconds.
    - robot: The robot object. Supported robots are currently Franka and UR10.
    - obstacles: A dictionary of obstacles to be added to the underlying motion policy.
    """
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


def scale_gains(robot, kp_scalar=1.0, kd_scalar=1.0, indices=None, verbose=False):
    """ Scale the gains of robot object's articulation controller.

    robot should be an Articulation object created with an articulation controller. Note that the
    existing gains are _scaled_, not explicitly set. The relative weights of the gains will remain
    the same, but their overall scale will be adjusted by the provided scalar. Both kp_scalar and
    kd_scalar default to 1.0 meaning the gains remain the same. This also means that calling this
    method with the same gain scalars twice will scale the original gains by the square of the
    scalar.

    Optionally, an indices list can be provided, in which case only the joints specified in the list
    will be scaled by the provided scalars.

    Params:
    - robot: The robot whose articulation controller's gains will be scaled.
    - kp_scalar: The scalar on the position gains. Defaults to 1.0 (no scaling).
    - kd_scalar: The scalar on the derivative gains. Defaults to 1.0 (no scaling).
    - indices:
    """
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
    scalar = 100.0
    scale_gains(robot, kp_scalar=scalar, kd_scalar=scalar, indices=indices, verbose=verbose)


def configure_ur10(robot, verbose=False):
    """ Disable gravity on the UR10 robot and set the gains (todo). This method has to be called after
    the first call to world.reset().
    """
    robot.disable_gravity()


def configure_robot(robot, verbose=False):
    """ Configure the robot for cortex control.
    
    Performs different configuration steps, such as disabling gravity and scaling gains, depending
    on the robot. Currently supported robots are Franka, UR10.
    """
    if isinstance(robot, Franka):
        print("<configuring franka>")
        configure_franka(robot, verbose=verbose)
    elif isinstance(robot, UR10):
        print("<configuring ur10>")
        configure_ur10(robot, verbose=verbose)
    else:
        raise RuntimeError("unrecognized robot: %s" % str(robot))


def extract_joint_state_subset(joint_state, indices):
    """ Extract the joint state subset corresponding to the specified indices. If any of positions,
    velocities, or efforts are unavailable in the provided joint_state object, those are left as
    None in the returned JointsState subset object.
    """
    positions = None
    if joint_state.positions is not None:
        positions = joint_state.positions[indices]

    velocities = None
    if joint_state.velocities is not None:
        velocities = joint_state.velocities[indices]

    efforts = None
    if joint_state.efforts is not None:
        efforts = joint_state.efforts[indices]

    return JointsState(positions, velocities, efforts)


def make_cortex_default_world():
    """ Construct and return a simple default empty world with a ground plane.
    """
    world = World(stage_units_in_meters=1.0)
    world.scene.add_default_ground_plane()
    return world


def load_franka_to_stage(robot_name="franka", prim_path="/cortex/belief/robot"):
    """ Load a franka USD into the stage. This method makes the USD avaiable; it needs to be
    subsequently wrapped in a Franka object and configured to be used by cortex.
    """
    assets_root_path = find_assets_root_path_with_error_checks()
    asset_path = assets_root_path + "/Isaac/Robots/Franka/franka_alt_fingers.usd"
    add_reference_to_stage(usd_path=asset_path, prim_path=prim_path)


def wrap_robot(domain, robot_type, prim_path):
    """ Wrap a robot of the given type at the specified prim_path using the cortex naming
    conventions.

    The name of the robot is set to 'robot_<domain>', such as 'robot_belief' and 'robot_sim', so
    they can be accessed from the World singleton from extensions and behavior scripts.

    params:
    - domain: Either 'belief' or 'sim'
    - robot_type: The type of the robot -- should match possible values of the cortex:robot_type
      attribute. Currently supported values are 'franka' and 'ur10'.
    - prim_path: The path to the USD prim representing the robot. Note that the prim at that path
      need not have the cortex:robot_type attribute. The robot_type is usually extracted from the
      belief robot and assumed for the sim robot.
    """
    robot_name = "robot_%s" % domain
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
    """ Try to wrap the robot prim at the standard path /cortex/<domain>/robot. Returns None if that
    path doesn't exist.

    domain should be either 'belief' or 'sim'.
    """
    prim_path = "/cortex/%s/robot" % domain
    if not is_prim_path_valid(prim_path):
        return None
    robot_type = get_robot_type(prim_path)
    robot = wrap_robot(domain, robot_type, prim_path)
    return robot


def wrap_cortex_robot_or_die(domain):
    """ Try to wrap the robot at the standard path /cortex/<domain>/robot. If there is not robot at
    that path, raises a runtime error.
    """
    robot = try_wrap_cortex_robot(domain)
    if robot is None:
        raise RuntimeError("could not find %s robot" % domain)
    return robot


def is_a_rigid_prim(prim):
    """ Returns True if the prim is a rigid prim.

    A prim is designated as a rigid prim if it has a rigid body API and a mass API.
    """
    return prim.HasAPI(UsdPhysics.RigidBodyAPI) and prim.HasAPI(UsdPhysics.MassAPI)


def make_core_object_from_prim(prim_path, name):
    """ Create a core object from the USD at the specified prim path.

    If the prim at the prim path is a cube, then it returns a DynamicCuboid wraping the prim if
    it's also a rigid prim, or a FixedCuboid if it's not.

    If the prim is not a cube, then simply wraps it in a generic XFormPrim object.

    Note that to add an object to the motion commander as an obstacle, it needs to be a core API
    object type. This method currently only supports wrapping UsdGeom.Cube USD types this way, so
    only cubes can be obstacles.
    """
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
            if prim_path.endswith("/properties"):
                continue

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
