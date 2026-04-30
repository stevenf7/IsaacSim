=============================================
Tutorial 9: Pick and Place Example
=============================================


Learning Objectives
=======================

This is the final manipulator tutorial in a series of four tutorials. It ties everything together by showing how to use the UR10e robot and the 2F-140 gripper to control the gripper, follow a Cartesian target, and perform a pick-and-place sequence.
We will be using the robot imported in :doc:`tutorial_import_assemble_manipulator` and the URDF and XRDF robot configuration files described in :ref:`isaac_sim_cumotion_tutorial_robot_configuration`.

This tutorial builds on top of the :ref:`isaac_sim_robot_motion_experimental` extension and demonstrates two motion controllers:

- **cuMotion RMPflow** — a GPU-accelerated reactive motion planner with collision avoidance.
- **PINK differential IK** — a CPU-based inverse kinematics solver using the `PINK <https://github.com/stephane-caron/pink>`_ library.

*30 Minutes Tutorial*

Prerequisites
==============

- Review :doc:`tutorial_import_assemble_manipulator` and :doc:`tutorial_configure_manipulator` prior to beginning this tutorial to generate robot and the URDF and XRDF files required by the pick-and-place examples.

.. note::
    If you have not completed the previous tutorial(s), you can find the prebuilt asset in the content browser at ``Isaac Sim/Samples/Rigging/Manipulator/configure_manipulator/ur10e/ur/ur_gripper.usd``.

    Additionally, pre-generated URDF, XRDF, and ``rmp_flow.yaml`` files can be found at ``source/extensions/isaacsim.robot_motion.cumotion/robot_configurations/ur10/``. 


Overview
=========

This tutorial is divided into four parts, each corresponding to a standalone example script:

.. list-table::
   :header-rows: 1
   :widths: 10 40 50

   * - Part
     - Script
     - Description
   * - 1
     - ``tutorial_9_gripper_control.py``
     - Gripper control using the Articulation API
   * - 2
     - ``tutorial_9_arm_trajectory.py``
     - Joint-space trajectory planning and execution
   * - 3
     - ``tutorial_9_follow_target.py``
     - Real-time Cartesian target following with cuMotion RMPflow
   * - 4
     - ``tutorial_9_pick_place_cumotion.py`` / ``tutorial_9_pick_place_pink.py``
     - Full pick-and-place sequence with cuMotion RMPflow or PINK differential IK

All scripts are located at ``standalone_examples/tutorials/manipulation/``.

Part 1: Gripper Control
========================

This example introduces the Articulation API by controlling the 2F-140 gripper joints directly with ``set_dof_position_targets``. The gripper closes fully and then opens again. 

.. code-block:: bash

    ./python.sh standalone_examples/tutorials/manipulation/tutorial_9_gripper_control.py

.. image:: /images/isim_6.0_full_tut_gui_ur10e_gripper_control.webp
    :align: center
    :width: 80%

**Key concepts:**

- ``Articulation.dof_names`` returns the list of all degrees of freedom in order. The gripper joint is named ``finger_joint``.
- ``set_dof_position_targets`` sends a position target to one or more DOFs by index. Passing ``dof_indices`` restricts the command to only those joints.

.. dropdown:: tutorial_9_gripper_control.py — gripper control loop

    .. literalinclude:: ../../../source/standalone_examples/tutorials/manipulation/tutorial_9_gripper_control.py
        :language: python
        :start-after: # <start-gripper-control-snippet>
        :end-before: # <end-gripper-control-snippet>


Part 2: Arm Trajectory Following
==================================

This example plans and executes a joint-space trajectory using ``mg.Path`` and ``mg.TrajectoryFollower`` from the motion generation API. The robot follows a sequence of waypoints in minimal time subject to velocity and acceleration limits.

.. code-block:: bash

    ./python.sh standalone_examples/tutorials/manipulation/tutorial_9_arm_trajectory.py

.. image:: /images/isim_6.0_full_tut_gui_ur10e_arm_trajectory.webp
    :align: center
    :width: 80%

**Key concepts:**

- ``mg.Path(waypoints)`` wraps a sequence of joint-space configurations.
- ``.to_minimal_time_joint_trajectory(max_velocities, max_accelerations, ...)`` computes a time-optimal trajectory that respects joint limits.
- ``mg.TrajectoryFollower`` tracks the planned trajectory, calling ``.forward(estimated_state, setpoint, t)`` each physics step to obtain the desired joint state.
- ``get_estimated_state`` packages the current joint positions, velocities, and efforts into an ``mg.RobotState``.
- ``apply_desired_state`` applies the position, velocity, and effort targets from the desired state back to the articulation.

.. dropdown:: tutorial_9_arm_trajectory.py — trajectory setup

    .. literalinclude:: ../../../source/standalone_examples/tutorials/manipulation/tutorial_9_arm_trajectory.py
        :language: python
        :start-after: # <start-arm-trajectory-setup-snippet>
        :end-before: # <end-arm-trajectory-setup-snippet>

.. dropdown:: tutorial_9_arm_trajectory.py — trajectory execution loop

    .. literalinclude:: ../../../source/standalone_examples/tutorials/manipulation/tutorial_9_arm_trajectory.py
        :language: python
        :start-after: # <start-arm-trajectory-loop-snippet>
        :end-before: # <end-arm-trajectory-loop-snippet>


Part 3: Follow Target using cuMotion RMPflow
=============================================

This example shows how to use the cuMotion ``RmpFlowController`` to make the robot track a draggable target cube in real time, with optional obstacle avoidance.

.. code-block:: bash

    ./python.sh standalone_examples/tutorials/manipulation/tutorial_9_follow_target.py

.. image:: /images/isim_6.0_full_tut_gui_ur10e_follow_target.webp
    :align: center
    :width: 80%

To enable obstacle avoidance, pass ``--with-obstacle``:

.. code-block:: bash

    ./python.sh standalone_examples/tutorials/manipulation/tutorial_9_follow_target.py --with-obstacle

.. image:: /images/isim_6.0_full_tut_gui_ur10e_follow_target_with_obstacle.webp
    :align: center
    :width: 80%

**Key concepts:**

- ``load_cumotion_supported_robot("ur10")`` loads the built-in cuMotion robot model for the UR10, which includes the kinematic chain and collision spheres.
- ``mg.WorldBinding`` connects the cuMotion world interface to the Isaac Sim stage. It uses ``mg.SceneQuery`` to find collision objects in the scene and registers them as obstacles.
- ``RmpFlowController`` is initialized with the robot model, world interface, joint space, and tool frame. It accepts an estimated robot state and a Cartesian setpoint each step, and returns desired joint positions.
- ``create_setpoint_state`` packages a target position and orientation into an ``mg.RobotState`` that the controller can track.
- ``world_binding.synchronize_transforms()`` must be called each step to update obstacle transforms before planning.

.. dropdown:: tutorial_9_follow_target.py — scene and controller setup

    .. literalinclude:: ../../../source/standalone_examples/tutorials/manipulation/tutorial_9_follow_target.py
        :language: python
        :start-after: # <start-follow-target-setup-snippet>
        :end-before: # <end-follow-target-setup-snippet>

.. dropdown:: tutorial_9_follow_target.py — per-step control loop

    .. literalinclude:: ../../../source/standalone_examples/tutorials/manipulation/tutorial_9_follow_target.py
        :language: python
        :start-after: # <start-follow-target-loop-snippet>
        :end-before: # <end-follow-target-loop-snippet>


Part 4: Pick and Place 
=======================

This example puts it all together by implementing a pick-and-place sequence. Two example scripts are provided: one using cuMotion RMPflow and one using PINK differential IK.

cuMotion RMPflow
----------------

.. important::
    cuMotion requires a ``tool_frames`` entry in the XRDF. See :ref:`isaac_sim_app_tutorial_generate_robot_config_adding_tool`.

.. code-block:: bash

    ./python.sh standalone_examples/tutorials/manipulation/tutorial_9_pick_place_cumotion.py \
        --xrdf-dir /path/to/robot/config

.. note::
    ``--xrdf-dir`` should point to the directory containing the robot URDF and XRDF files made in the previous tutorial. ``--urdf`` and ``--xrdf`` select the filenames within that directory and default to ``robot.urdf`` and ``robot.xrdf``, respectively.

    If no ``--xrdf-dir`` is provided, ``load_cumotion_supported_robot("ur10")`` will be used to load the built-in UR10 robot configuration.

.. image:: /images/isim_6.0_full_tut_gui_ur10e_pick_place_rmp.webp
    :align: center
    :width: 80%

**Key concepts:**

- ``--xrdf-dir`` (optional) points to the directory containing custom robot config files. ``load_cumotion_robot`` loads the URDF and XRDF from that directory using the filenames given by ``--urdf`` and ``--xrdf``. If omitted, the built-in UR10 configuration is used via ``load_cumotion_supported_robot("ur10")``.
- ``RmpFlowController.get_rmp_flow_config().set_param(key, value)`` allows tuning RMPflow parameters at runtime. For this example, ``cspace_target_rmp/metric_scalar`` is reduced to 1.0 to reduce the influence of the initial position error on the motion planning.
- ``controller.reset(estimated_state, setpoint, t)`` must be called at the start of each arm motion segment to re-initialize the planner from the current robot state.

.. dropdown:: tutorial_9_pick_place_cumotion.py — UR10ePickPlace state machine class

    .. literalinclude:: ../../../source/standalone_examples/tutorials/manipulation/tutorial_9_pick_place_cumotion.py
        :language: python
        :start-after: # <start-pick-place-sequence-snippet>
        :end-before: # <end-pick-place-sequence-snippet>


PINK Differential IK
--------------------

This example demonstrates an alternative motion controller: **PINK differential IK**. The same pick-and-place sequence is implemented using the ``PinkIKController``, which solves inverse kinematics using `PINK <https://github.com/stephane-caron/pink>`_ and `Pinocchio <https://github.com/stack-of-tasks/pinocchio>`_.

Run this example with:

.. code-block:: bash

    # Load the built-in PINK robot model for the UR10
    ./python.sh standalone_examples/tutorials/manipulation/tutorial_9_pick_place_pink.py
    # Load a custom URDF
    ./python.sh standalone_examples/tutorials/manipulation/tutorial_9_pick_place_pink.py --urdf <path_to_urdf>

.. image:: /images/isim_6.0_full_tut_gui_ur10e_pick_place_pink.webp
    :align: center
    :width: 80%

**Key concepts:**

- ``load_pink_supported_robot("ur10")`` loads the built-in PINK robot model for the UR10, backed by a Pinocchio model. Alternatively, a custom URDF can be loaded using ``load_pink_robot`` by passing in ``--urdf <path_to_urdf>``.
- ``PinkIKController`` accepts a tool frame name, position and orientation costs, a posture cost, and a QP solver (``"osqp"``). It integrates Cartesian velocity commands into joint positions each step.
- ``_init_pink_q0`` sets ``pink_robot.q0`` to the elbow-up configuration. PINK's PostureTask regularizes the IK solution toward this reference, steering the solver away from elbow-down or degenerate configurations.

.. dropdown:: tutorial_9_pick_place_pink.py — UR10ePickPlace state machine class

    .. literalinclude:: ../../../source/standalone_examples/tutorials/manipulation/tutorial_9_pick_place_pink.py
        :language: python
        :start-after: # <start-pick-place-pink-sequence-snippet>
        :end-before: # <end-pick-place-pink-sequence-snippet>

Summary
=======

In this tutorial, you learned how to:

- Control the 2F-140 gripper using the Articulation API and ``set_dof_position_targets``.
- Plan and execute joint-space trajectories using ``mg.Path`` and ``mg.TrajectoryFollower``.
- Use the cuMotion ``RmpFlowController`` to track a Cartesian target in real time with obstacle avoidance.
- Implement an 8-phase pick-and-place sequence with cuMotion RMPflow.
- Implement the same sequence with PINK differential IK as an alternative CPU-based solver.
