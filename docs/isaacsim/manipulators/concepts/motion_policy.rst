..
   Copyright (c) 2022-2026, NVIDIA CORPORATION. All rights reserved.
   NVIDIA CORPORATION and its licensors retain all intellectual property
   and proprietary rights in and to this software, related documentation
   and any modifications thereto. Any use, reproduction, disclosure or
   distribution of this software and related documentation without an express
   license agreement from NVIDIA CORPORATION is strictly prohibited.

.. _isaac_sim_motion_policy:

Motion Policy Algorithm
++++++++++++++++++++++++++++

.. note::
   For new development, consider using the newer experimental motion generation API in :doc:`Motion Generation (Experimental) <../../motion_generation/index>` and :doc:`cuMotion Integration <../../cumotion/index>`, which provide improved interfaces and additional features.

An |isaac-sim_short| motion policy is a collision aware algorithm that outputs actions on each frame to navigate a single robot to a single task-space target.
The `MotionPolicy` class is an interface that is designed to be basic to fulfill,
but complete enough that an implementation of a `MotionPolicy` can be used alongside the :ref:`isaac_sim_articulation_motion_policy` class
to start moving the simulated robot around with just a few lines of code.

A single flexible `MotionPolicy` is provided based on the implementation of **RMPflow**
in the NVIDIA-developed **Lula** library (see :doc:`rmpflow`).


Broadly defined, a *motion policy* is a mathematical function that takes the current
state of a robot (that is, position and velocity in generalized coordinates) and returns
a quantity representing a desired change in that state.  Such a policy can depend
implicitly on variables representing one or more objectives or constraints, the state of
the environment.  The `MotionPolicy` interface has two forms of state as input: 

* :ref:`isaac_sim_motion_policy_world_state`
* :ref:`isaac_sim_motion_policy_robot_state`
  
The main output of a `MotionPolicy` are position and velocity targets for the robot on the next frame.  A `MotionPolicy` is
expected to be able to perform an internal world update and compute joint targets in real time (a few ms per frame).

.. _isaac_sim_motion_policy_active_joints:

Active and Watched Joints
--------------------------------

The robot `Articulation` in Isaac Sim comes from a loaded USD file.  This robot specification is not expected to perfectly match the specification used internally by a `MotionPolicy`.
To perform the appropriate mapping, a `MotionPolicy` has two functions it must fulfill:   

* ``MotionPolicy.get_active_joints()``: joints that the `MotionPolicy` is going to directly control to achieve the desired end effector target.
* ``MotionPolicy.get_watched_joints()``: joints that the `MotionPolicy` observes to plan motions, but will not actively control.
 
Both functions return a list of joint names in the order that the `MotionPolicy` expects to receive them. 

For example, the Franka robot has nine degrees of freedom (DOFs): 

* seven revolute joints for controlling the arm
* two prismatic joints for controlling its gripper  
 
The robot `Articulation` exposes all nine degrees of freedom, but :ref:`isaac_sim_motion_generation_rmpflow` only cares about the seven revolute joints when navigating the robot to a position target. It is not appropriate for RMPflow to take control of the gripper DOFs, because those DOFs can be controlled separately when performing a task such as pick-and-place.  ``RmpFlow.get_active_joints()`` returns the names of the seven revolute joints
in the Franka robot.  ``RmpFlow.get_watched_joints()`` returns an empty list because the joint states of the gripper DOFs are irrelevant when navigating the Franka's hand to a target position.

Every time `RmpFlow` returns joint targets for the Franka, it is returning arrays of length seven.  When `RmpFlow` is passed an argument such as `active_joint_positions`, it is expecting a vector of seven numbers that describe the joint positions of the Franka robot in the order specified by ``RmpFlow.get_active_joints()``.

.. _isaac_sim_motion_policy_world_state:

Inputs: World State
--------------------------------

|isaac-sim| provides a set of objects in ``isaacsim.core.api.objects`` that are intended to fully describe the simulated world.  Only object primitives such as sphere and cone
are supported.  A `MotionPolicy` has an adder for each type of object that exists in
``isaacsim.core.api.objects`` for example, ``MotionPolicy.add_sphere(sphere: isaacsim.core.api.objects.sphere.*)``. Objects in ``isaacsim.core.api.objects`` wrap objects that exist on the USD stage.
As objects move around on the stage, their location can be retrieved on each frame using the representative object from ``isaacsim.core.api.objects``.  This means that after a
`MotionPolicy` has been passed an object, it can internally query the position of that object on the stage over time as needed.  A `MotionPolicy` queries all relevant obstacle positions
from the ``isaacsim.core.api.objects`` that have been passed in when ``MotionPolicy.update_world()`` is called, and passes the information to its internal world state.

It is not required that a specific `MotionPolicy` actually implement an adder for every type of object that exists in ``isaacsim.core.api.objects``.  When a class inherits from `MotionPolicy`,
any unimplemented adder functions will throw warnings.  For example, :ref:`isaac_sim_motion_generation_rmpflow`  supports spheres, capsules, and cuboids in its world representation.
In environments with cones, RMPflow will ignore the cone objects, and a warning will be printed for each cone object that gets added.

.. _isaac_sim_motion_policy_robot_state:

Inputs: Robot State
--------------------------------

There are two methods for specifying robot state in a MotionPolicy:

* The base pose of the robot can be specified to a `MotionPolicy` using ``MotionPolicy.set_robot_base_pose()``.  If this function is never called, the policy implementation can make a reasonable assumption about the position of the robot. :ref:`isaac_sim_motion_generation_rmpflow` assumes that the robot is at the origin of the stage until it is told otherwise.

* ``MotionPolicy.compute_joint_targets(active_joint_positions, active_joints_velocities, watched_joint_positions, watched_joint_velocities,...)`` expects robot joint positions and velocities to be passed in using the order specified by ``MotionPolicy.get_active_joints()`` and ``MotionPolicy.get_watched_joints()``.

.. _isaac_sim_motion_policy_joint_targets:

Outputs: Robot Joint Targets
--------------------------------

``MotionPolicy.compute_joints_targets(active_joint_positions, active_joints_velocities, watched_joint_positions, watched_joint_velocities,...)`` returns position and velocity targets for the robot `Articulation`
on the next frame.  The joint targets are for the active joints, and so they will have the same shape as the `active_joint_positions` argument.  By passing a `MotionPolicy`
to the :ref:`isaac_sim_articulation_motion_policy` helper class, the work of translating the robot state between the robot `Articulation` and the `MotionPolicy` is done automatically using the outputs of
``MotionPolicy.get_active_joints()`` and ``MotionPolicy.get_watched_joints()``.  A `MotionPolicy` might expect joint targets to be used in a standard PD controller:

.. math::

   kp*(joint_position_targets-joint_positions) + kd*(joint_velocity_targets-joint_velocities)

Both position and velocity targets must always be returned by a `MotionPolicy`.  |isaac-sim| supports providing only position targets or only velocity targets.
To match the default behavior of the Isaac Sim controller when only one target is set, you can set the `joint_velocity_targets` to zero for pure damping,
and it can set the `joint_position_targets` to be equal to the current `joint_positions` to effectively remove the position term from the PD equation.

.. _isaac_sim_articulation_motion_policy:

Articulation Motion Policy
===========================

An `ArticulationMotionPolicy` is initialized using a robot `Articulation` object that represents the simulated robot, and a `MotionPolicy`.  The purpose of this class is to handle the mapping of joints
between the robot articulation and the policy automatically by using the outputs of ``MotionPolicy.get_active_joints()`` and ``MotionPolicy.get_watched_joints()``.  There is a single important function in
this class: ``ArticulationMotionPolicy.get_next_articulation_action()``.  Calling this function queries the robot state from the robot `Articulation`, extracts and arranges the appropriate joints from the joint state
to use the ``MotionPolicy.compute_joint_targets()`` function, and then creates a valid `ArticulationAction` that can be passed to the robot `Articulation` to generate motions.

In the Franka example discussed in :ref:`isaac_sim_motion_policy_active_joints`, the robot `Articulation` that represents the Franka expects nine DOF joint targets.  `RmpFlow` only controls seven of the DOFs.  The appropriate
seven DOFs are passed to `RmpFlow`, and seven DOF joint position and velocity targets are returned.  This 7-vector is mapped to a 9-vector, padding with `None` when no action is supposed to be taken for a particular joint.  The
`ArticulationAction` object that is returned contains a 9-vector for position and velocity targets, and this can be applied to the robot `Articulation` using ``Articulation.get_articulation_controller().apply_action(articulation_action)``.

.. _isaac_sim_motion_policy_controller:

Motion Policy Controller
=========================

The `MotionPolicyController` class wraps a motion policy into an instance of ``isaacsim.core.api.controllers.BaseController``.  Extensions representing individual robots such as ``isaacsim.robot.manipulators.franka`` have an instance of
a `BaseController` for moving the robot around.  The Franka robot can be moved to a target by importing ``isaacsim.robot.manipulators.franka.controllers.RMPFlowController`` and using the `forward` function.


