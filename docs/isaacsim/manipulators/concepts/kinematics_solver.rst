..
   Copyright (c) 2022-2026, NVIDIA CORPORATION. All rights reserved.
   NVIDIA CORPORATION and its licensors retain all intellectual property
   and proprietary rights in and to this software, related documentation
   and any modifications thereto. Any use, reproduction, disclosure or
   distribution of this software and related documentation without an express
   license agreement from NVIDIA CORPORATION is strictly prohibited.


.. _isaac_sim_kinematics_solver:


Kinematics Solvers
+++++++++++++++++++++++++++++++

.. note::
   For new development, consider using the newer experimental motion generation API in :doc:`Motion Generation (Experimental) <../../motion_generation/index>`, which provides improved interfaces and additional features.

Like a :ref:`isaac_sim_motion_policy`, a :ref:`isaac_sim_kinematics_solver` is an interface class with a single provided implementation.  A `KinematicsSolver`
is able to compute forward and inverse kinematics.  A single implementation is provided using the NVIDIA-developed **Lula** library. (see :ref:`isaac_sim_lula_kinematics_solver`)

includes:

* Kinematics Solver
* Articulation Kinematics Solver
* Lula Kinematics Solver


Kinematics Solver
=================

The `KinematicsSolver` interface specifies functions for computing both forward and inverse kinematics at any available frame in the robot.  Like a :ref:`isaac_sim_motion_policy`,
an instance of the `KinematicsSolver` class is not expected to use the same USD robot representation as |isaac-sim|.  A `KinematicsSolver` can have its own internal
representation of the robot, and there are necessary interface functions for performing the mapping between the internal robot representation and the robot
`Articulation`.

Joint Names
----------------

An instance of the `KinematicsSolver` class must fulfill a function `KinematicsSolver.get_joint_names()` that specifies the joints of interest to the solver, and the order in which it
expects them.  Think of a robot arm mounted on a moving base.  A `KinematicsSolver` can use only the URDF for the robot arm without knowing about the robot base.  In this case, many of
the joints in the robot `Articulation` would not be recognized by the `KinematicsSolver`.

When computing forward kinematics, the joint positions that are passed to the solver must correspond to the output of `KinematicsSolver.get_joint_names()`.  Likewise, the output of
inverse kinematics will have the same shape as `KinematicsSolver.get_joint_names()`.  A mapping layer between the robot `Articulation` and the `KinematicsSolver` is provided in the
:ref:`isaac_sim_articulation_kinematics_solver` class.

Frame Names
---------------

An instance of the `KinematicsSolver` class must fulfill a function `KinematicsSolver.get_all_frame_names()` to provide a list of frames in the robot's kinematics chain that can have their positions
referenced by name when solving either forward or inverse kinematics.  The frame names returned by a `KinematicsSolver` do not have to match the frames present in the robot `Articulation`.  Like joint names,
the frame names come from the individual solver's config file structure.

Robot Base Pose
----------------

As with a :ref:`isaac_sim_motion_policy`, a the `KinematicsSolver` interface includes a function `set_robot_base_pose()` that allows the caller to specify the location of the robot base.  If this function has been called,
the `KinematicsSolver` must apply appropriate transformations when computing forward and inverse kinematics.
A `KinematicsSolver` operates in world coordinates.  The solution to the forward kinematics will be translated and rotated according to the robot base pose to return the position of the end effector relative to the world frame,
and the input to the inverse kinematics will be provided in the world coordinates and transformed so that it is relative to the robot base frame.  If you prefers that the solver inputs are relative to the robot base frame,
they can simply set the robot base pose to the origin.

Collision Awareness
-------------------------

Implementations of the `KinematicsSolver` class do not need to be collision aware with external objects, but they have the option.  A function `KinematicsSolver.supports_collision_avoidance() -> bool` must be implemented
to indicate whether a particular `KinematicsSolver` supports collision avoidance.  If a `KinematicsSolver` supports collision avoidance, it can fulfill the same set of world functions as a `MotionPolicy` (:ref:`isaac_sim_motion_policy_world_state`).
If a solver is collision aware, it is especially important to specify the robot base pose correctly, as the positions of objects can only be queried relative to the world frame, and it is up to the solver to compute the positions of obstacles
relative to the robot.



.. _isaac_sim_articulation_kinematics_solver:

Articulation Kinematics Solver
===============================

The `ArticulationKinematicsSolver` class exists to handle the mapping between the robot `Articulation` and an implementation of a :ref:`isaac_sim_kinematics_solver`.

Forward Kinematics
-------------------------

`ArticulationKinematicsSolver` wraps the forward kinematics function of a `KinematicsSolver` to query the joint positions of the robot `Articulation` and pass the appropriate joint positions to the `KinematicsSolver` in the order
specified by `KinematicsSolver.get_joint_names()`.  This allows the current position of the simulated robot end effector to be queried easily.

Inverse Kinematics
-------------------------

`ArticulationKinematicsSolver` wraps the inverse kinematics to return the resulting joint positions as an `ArticulationAction` that can be directly applied to the robot `Articulation`.
The current robot `Articulation` joint positions at the time this method is called are automatically used as a warm start in the IK calculation.


.. _isaac_sim_lula_kinematics_solver:

Lula Kinematics Solver
=======================

The `LulaKinematicsSolver` implements the :ref:`isaac_sim_kinematics_solver` interface.  The solver does not support collision avoidance with objects in the world.  In addition to the functions in the
`KinematicsSolver` interface, the `LulaKinematicsSolver` includes getters and setters for changing internal settings such as `LulaKinematicsSolver.set_max_iterations()` to set the maximum number
of iterations before the IK computation returns a failure.

.. _isaac_sim_lula_kinematics_solver_configuration:

Lula Kinematics Solver Configuration
-----------------------------------------

Two files are necessary to configure Lula Kinematics for use with a new robot:

   1. A URDF (universal robot description file), used for specifying robot kinematics as well as joint and link names. Position limits for each joint are also required. Other properties in the URDF are ignored and can be omitted; these include masses, moments of inertia, visual and collision meshes.

   2. A supplemental robot description file in YAML format. In addition to enumerating the list of actuated joints that define the configuration space (c-space) for the robot, this file also includes sections for specifying the default c-space configuration. This file can also be used to specify fixed positions for unactuated joints.
