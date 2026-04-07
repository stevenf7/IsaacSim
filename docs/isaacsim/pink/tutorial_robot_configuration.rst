.. _isaac_sim_pink_tutorial_robot_configuration:

==================================
Robot Configuration Tutorial
==================================

This tutorial demonstrates how to configure robots for use with the PINK integration. You'll learn how to load robot
configurations from supported robots or from your own URDF files.

By the end of this tutorial, you'll understand:

* How to load pre-configured robots using :func:`load_pink_supported_robot`
* How to load custom robot configurations using :func:`load_pink_robot`
* The structure of the :class:`PinkRobot` dataclass
* How to enable self-collision checking

**Prerequisites**

- Basic understanding of URDF file format

Key Concepts
============

A :class:`PinkRobot` encapsulates all the data needed for differential IK solving with PINK:

* ``model``: The Pinocchio rigid-body model parsed from the URDF
* ``data``: Pre-allocated Pinocchio workspace for forward kinematics and Jacobian computation
* ``controlled_joint_names``: Ordered list of actuated joint names
* ``q0``: Neutral (home) configuration vector
* ``collision_model`` / ``collision_data``: Optional collision geometry for :class:`SelfCollisionBarrier` support
* ``directory``: Path to the robot configuration directory

The configuration is used by :class:`PinkIKController` to build the underlying :class:`pink.Configuration` and
compute forward kinematics, Jacobians, and frame placements.

Loading Supported Robots
========================

The easiest way to get started is to use a pre-configured robot that comes with the extension. Currently supported
robots include:

* **franka** - Franka Emika Panda robot
* **ur10** - Universal Robots UR10 robot

To load a supported robot configuration:

.. code-block:: python

    from isaacsim.robot_motion.pink import load_pink_supported_robot

    robot = load_pink_supported_robot("franka")
    print(robot.controlled_joint_names)
    # ['panda_joint1', 'panda_joint2', ..., 'panda_joint7']

The function automatically locates the robot's URDF within the extension's ``robot_configurations`` directory.
If the robot name is not supported, a :class:`FileNotFoundError` is raised.

Loading Custom Robots
=====================

If you have your own robot with a URDF file, you can load it using :func:`load_pink_robot`:

.. code-block:: python

    from isaacsim.robot_motion.pink import load_pink_robot

    robot = load_pink_robot(urdf_path="/path/to/my_robot/robot.urdf")

If your URDF references mesh files, provide the package directories so Pinocchio can resolve them:

.. code-block:: python

    robot = load_pink_robot(
        urdf_path="/path/to/my_robot/robot.urdf",
        package_dirs=["/path/to/my_robot"],
    )

Enabling Self-Collision Checking
================================

To use :class:`SelfCollisionBarrier` for self-collision avoidance, the collision model must be loaded
from the URDF. Enable this with the ``build_collision_model`` parameter:

.. code-block:: python

    robot = load_pink_robot(
        urdf_path="/path/to/my_robot/robot.urdf",
        build_collision_model=True,
    )

If you also have an SRDF file defining collision pair exclusions (e.g., adjacent links that are
always in contact), pass it via ``srdf_path``:

.. code-block:: python

    robot = load_pink_robot(
        urdf_path="/path/to/my_robot/robot.urdf",
        srdf_path="/path/to/my_robot/robot.srdf",
        build_collision_model=True,
    )

.. note::
   PINK only requires a URDF file. Unlike the cuMotion integration, no XRDF file is needed.

Accessing the Pinocchio Model
=============================

The :class:`PinkRobot` provides direct access to the underlying Pinocchio objects:

.. code-block:: python

    import pinocchio as pin

    # Model properties
    print(f"DOFs (nq): {robot.model.nq}")
    print(f"Velocity DOFs (nv): {robot.model.nv}")
    print(f"Number of joints: {robot.model.njoints}")

    # List all frames in the model
    for i in range(robot.model.nframes):
        print(f"  Frame: {robot.model.frames[i].name}")

    # Neutral configuration
    q0 = pin.neutral(robot.model)

    # Forward kinematics at a given configuration
    pin.forwardKinematics(robot.model, robot.data, q0)
    pin.updateFramePlacements(robot.model, robot.data)

    # Get a frame's world-space transform
    frame_id = robot.model.getFrameId("panda_hand")
    transform = robot.data.oMf[frame_id]
    print(f"End-effector position: {transform.translation}")

Summary
=======

This tutorial demonstrated:

1. **Loading Supported Robots**: Using :func:`load_pink_supported_robot` to load pre-configured robots
2. **Custom Robots**: Using :func:`load_pink_robot` to load robots from your own URDF files
3. **Collision Model**: Enabling self-collision checking with ``build_collision_model=True``
4. **Pinocchio Access**: Using the Pinocchio model and data for forward kinematics and frame queries

Robot configurations are foundational for all PINK inverse kinematics. Once you have a configuration, you can use it
with :class:`PinkIKController` to generate reactive motions for your robot.

Next Steps
----------

* :ref:`IK Controller tutorial <isaac_sim_pink_tutorial_ik_controller>` - Reactive end-effector tracking
* :ref:`Multi-Task tutorial <isaac_sim_pink_tutorial_multi_task>` - Combining weighted tasks
* `PINK documentation <https://stephane-caron.github.io/pink/>`_ - Full PINK API reference
