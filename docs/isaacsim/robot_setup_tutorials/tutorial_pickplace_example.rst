=============================================
Tutorial 9: Pick and Place Example
=============================================


Learning Objectives
=======================

This is the final manipulator tutorial in a series of four tutorials. This tutorial tie everything together by showing how to use the UR10e robot and the 2F-140 gripper to follow a target and pick up a block.
We will be using the robot imported in :doc:`tutorial_import_assemble_manipulator`, tuned in :doc:`tutorial_configure_manipulator`, and the robot configuration file generated in :doc:`tutorial_generate_robot_config`.

In this tutorial, we will be using the Lula kinematics solver to follow a target and the RMPFlow to pick up a block.

.. Note:: 
    All the files created in this tutorial are available at ``standalone_examples/deprecated/api/isaacsim.robot.manipulators/ur10e`` for verification.


*30 Minutes Tutorial*

Prerequisites
==============

- Review :doc:`tutorial_generate_robot_config` tutorial prior to beginning this tutorial, continue the following steps from the asset built in the previous tutorial.

.. note::
    If you have not completed the previous tutorial, you can find the prebuilt asset in the content browser at ``Isaac Sim/Samples/Rigging/Manipulator/configure_manipulator/ur10e/ur/ur_gripper.usd``. 

Gripper Control Example
========================

The script below uses the ``Parallel Gripper`` class to control the gripper joints and the ``Manipulator`` class to control the robot joints. 
Steps 0 to 400 close the gripper slowly. Steps 400 to 800, open the gripper slowly, and then reset the gripper position to 0.

.. note::
    The provided script can be run using:
    
    .. code-block:: bash

        ./python.sh standalone_examples/deprecated/api/isaacsim.robot.manipulators/ur10e/gripper_control.py

.. dropdown:: gripper_control.py

    .. literalinclude:: ../snippets/robot_setup_tutorials/tutorial_pickplace_example/gripper_control_example.py
        :language: python

.. image:: /images/isim_5.0_full_tut_gui_ur10e_gripper_control.webp
    :align: center
    :width: 80%



Follow Target Example using Lula Kinematics Solver
====================================================

Create a follow target task using the Lula kinematics solver, where you can specify the target position using a cube and the robot will move its end effector to the target position.
The inverse kinematics solver will use the Lula robot descriptor created in the :doc:`tutorial_generate_robot_config` tutorial. 

The generated robot descriptor file is available at ``source/standalone_examples/deprecated/api/isaacsim.robot.manipulators/ur10e/rmpflow/robot_descriptor.yaml``.

.. note::
    The provided script can be run using:
    
    .. code-block:: bash

        ./python.sh standalone_examples/deprecated/api/isaacsim.robot.manipulators/ur10e/follow_target_example.py

    Move the cube to the target location and run the script to see the robot move its end effector to the target location.



.. image:: /images/isim_5.0_full_tut_gui_ur10e_follow_target.webp
    :align: center
    :width: 80%

The ``ik_solver.py`` script initializes the ``KinematicsSolver`` class and the ``LulaKinematicsSolver`` class.

.. dropdown:: controllers/ik_solver.py

    .. literalinclude:: ../snippets/robot_setup_tutorials/tutorial_pickplace_example/follow_target_example_using_lula_kinematics_solver.py
        :language: python

The ``follow_target.py`` script initializes the ``FollowTarget`` class and sets up the ``manipulator`` and ``parallel_gripper`` objects.

.. dropdown:: tasks/follow_target.py

    .. literalinclude:: ../snippets/robot_setup_tutorials/tutorial_pickplace_example/todo_change_the_config_path.py
        :language: python

The ``follow_target_example.py`` script initializes the ``FollowTarget`` task  and the ``KinematicsSolver`` created in the previous step with a target location for the cube to be followed by the end effector.

.. dropdown:: follow_target_example.py

    .. literalinclude:: ../snippets/robot_setup_tutorials/tutorial_pickplace_example/define_the_manipulator.py
        :language: python

RMP Flow Configuration
======================

Use RMPFlow to control the end effector. See :ref:`isaac_sim_motion_generation_rmpflow` for more details about RMPFlow.

The ``ur10e_rmpflow_common.yaml`` file is available at ``source/standalone_examples/deprecated/api/isaacsim.robot.manipulators/ur10e/rmpflow/ur10e_rmpflow_common.yaml``, 
it specifies various parameters for the RMPFlow controller.

.. dropdown:: rmpflow/ur10e_rmpflow_common.yaml

    .. code-block:: yaml
        :linenos:

        joint_limit_buffers: [.01, .01, .01, .01, .01, .01]
        rmp_params:
            cspace_target_rmp:
                metric_scalar: 50.
                position_gain: 100.
                damping_gain: 50.
                robust_position_term_thresh: .5
                inertia: 1.
            cspace_trajectory_rmp:
                p_gain: 100.
                d_gain: 10.
                ff_gain: .25
                weight: 50.
            cspace_affine_rmp:
                final_handover_time_std_dev: .25
                weight: 2000.
            joint_limit_rmp:
                metric_scalar: 1000.
                metric_length_scale: .01
                metric_exploder_eps: 1e-3
                metric_velocity_gate_length_scale: .01
                accel_damper_gain: 200.
                accel_potential_gain: 1.
                accel_potential_exploder_length_scale: .1
                accel_potential_exploder_eps: 1e-2
            joint_velocity_cap_rmp:
                max_velocity: 1.
                velocity_damping_region: .3
                damping_gain: 1000.0
                metric_weight: 100.
            target_rmp:
                accel_p_gain: 30.
                accel_d_gain: 85.
                accel_norm_eps: .075
                metric_alpha_length_scale: .05
                min_metric_alpha: .01
                max_metric_scalar: 10000
                min_metric_scalar: 2500
                proximity_metric_boost_scalar: 20.
                proximity_metric_boost_length_scale: .02
                xi_estimator_gate_std_dev: 20000.
                accept_user_weights: false
            axis_target_rmp:
                accel_p_gain: 210.
                accel_d_gain: 60.
                metric_scalar: 10
                proximity_metric_boost_scalar: 3000.
                proximity_metric_boost_length_scale: .08
                xi_estimator_gate_std_dev: 20000.
                accept_user_weights: false
            collision_rmp:
                damping_gain: 50.
                damping_std_dev: .04
                damping_robustness_eps: 1e-2
                damping_velocity_gate_length_scale: .01
                repulsion_gain: 800.
                repulsion_std_dev: .01
                metric_modulation_radius: .5
                metric_scalar: 10000.
                metric_exploder_std_dev: .02
                metric_exploder_eps: .001
            damping_rmp:
                accel_d_gain: 30.
                metric_scalar: 50.
                inertia: 100.
        canonical_resolve:
            max_acceleration_norm: 50.
            projection_tolerance: .01
            verbose: false
        body_cylinders:
            - name: base
            pt1: [0,0,.10]
            pt2: [0,0,0.]
            radius: .2
        body_collision_controllers:
            - name: ee_link_robotiq_arg2f_base_link
            radius: .05


Follow Target Example using RMP Flow
====================================

Create an RMP flow controller to move the robot end effector to the target location.

.. note::
    The provided script can be run using:
    
    .. code-block:: bash

        ./python.sh standalone_examples/deprecated/api/isaacsim.robot.manipulators/ur10e/follow_target_example_rmpflow.py

.. image:: /images/isim_5.0_full_tut_gui_ur10e_follow_target_rmp.webp
    :align: center
    :width: 80%

The ``rmpflow.py`` initializes Lula motion generation policy using the ``ur10e_rmpflow_common.yaml`` file above, the ``ur10e.urdf`` and the robot descriptor file created in :doc:`tutorial_generate_robot_config`.

.. dropdown:: controllers/rmpflow.py

    .. literalinclude:: ../snippets/robot_setup_tutorials/tutorial_pickplace_example/follow_target_example_using_rmp_flow.py
        :language: python

The ``follow_target_example_rmpflow.py`` script initializes the ``FollowTarget`` task and the ``RMPFlowController`` created in the previous step with a target location for the cube to be followed by the end effector.

.. dropdown:: follow_target_example_rmpflow.py

    .. literalinclude:: ../snippets/robot_setup_tutorials/tutorial_pickplace_example/follow_target_example_using_rmp_flow_1.py
        :language: python

Basic Pick and Place Task using RMP Flow
=========================================

Use the RMPFlow controller to pick up a block and place it in a target location.

.. note::
    The provided script can be run using:
    
    .. code-block:: bash

        ./python.sh standalone_examples/deprecated/api/isaacsim.robot.manipulators/ur10e/pick_up_example.py

.. image:: /images/isim_5.0_full_tut_gui_ur10e_pick_place_rmp.webp
    :align: center
    :width: 80%

The ``controllers/pick_place.py`` script creates a ``PickPlace`` controller that will pick up a block and place it in a target location.

.. dropdown:: controllers/pick_place.py

    .. literalinclude:: ../snippets/robot_setup_tutorials/tutorial_pickplace_example/basic_pick_and_place_task_using_rmp_flow.py
        :language: python

The ``tasks/pick_place.py`` script creates a ``PickPlace`` task that sets up the UR10e manipulator and the gripper to pick up a block and place it in a target location.

.. dropdown:: tasks/pick_place.py

    .. literalinclude:: ../snippets/robot_setup_tutorials/tutorial_pickplace_example/basic_pick_and_place_task_using_rmp_flow_1.py
        :language: python

The ``pick_place_example.py`` script puts everything together and runs the simulation. 

.. important:: Make sure to tune the ``end_effector_offset`` parameter to get the best results, this is the offset between the end effector link on the robot and optimal grasp position for the claw.

.. dropdown:: pick_place_example.py

    .. literalinclude:: ../snippets/robot_setup_tutorials/tutorial_pickplace_example/define_the_manipulator_1.py
        :language: python

Advanced Pick and Place Task using RMPFlow and Foundation Pose
===============================================================

In the pick and place example above, you used the RMPFlow controller to pick up a block and place it in a target location. However there are some limitations to this approach.

- The robot gets the cube pose directly from the simulator observation, which does not translate to the real world.
- The class set up is limited to the cube, and in real life different objects have different shapes and sizes, and different grasping strategies.

To address these limitations, see `Isaac Manipulator <https://nvidia-isaac-ros.github.io/reference_workflows/isaac_manipulator/index.html>`_ tutorials for more advanced pick and place tasks.

Summary
=======

In this tutorial, you learned how to use the Lula kinematics solver to follow a target and the RMPFlow to pick up a block.

