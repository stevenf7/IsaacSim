.. _isaac_sim_app_tutorial_configure_rmpflow_denso:

=========================================
Configuring RMPflow for a New Manipulator
=========================================


In this tutorial, you learn how the :ref:`isaac_sim_motion_generation_rmpflow` algorithm can be fully configured following the creation of a `Robot Description File`.

Getting Started
===============

**Prerequisites**

- **Complete** the :ref:`isaac_sim_app_tutorial_motion_generation_robot_description_editor` tutorial to create one of the two required configuration files for using RmpFlow.
- Review the :doc:`../robot_setup_tutorials/tutorial_configure_manipulator` prior to beginning this tutorial to obtain a robot `Articulation` USD asset.

This tutorial provides a URDF file and USD file describing the **Cobotta Pro 900** robot.  The USD file was generated from the URDF using the process discussed in :doc:`../robot_setup_tutorials/tutorial_import_assemble_manipulator`.

Open the tutorial assets from the Content Browser at this path: ``Isaac Sim/Samples/Rigging/Cobotta_Pro_900_Assets``

Using the Lula Test Widget
=============================

This tutorial demonstrates how `RMPflow` can be configured and tested on a new robot using the `Lula Test Widget`.  The `Lula Test Widget` is an extension that can
be enabled in the Extensions menu as shown below, and then accessed under **Tools > Robotics > Lula Test Widget**.

This extension allows you to select their RMPflow config files along with a selected robot `Articulation` on the USD stage and run scenarios to verify that
`RMPflow` is working as intended.  After each type of required config file is created, they can be loaded and used in the `Lula Test Widget`.  


Template RmpFlow Config File
==============================
There are three files to describe the robot and parameterize the
:ref:`isaac_sim_motion_generation_rmpflow` algorithm:

  * A **URDF** (universal robot description file), used for specifying robot kinematics
     as well as joint and link names.  Position limits for each joint are also required.
     Other properties in the URDF are ignored and can be omitted; these include masses,
     moments of inertia, visual and collision meshes.
  * A **supplementary robot description file** in YAML format.  This file can be generated using the `Lula Robot Description Editor` UI tool.
  * A **RMPflow configuration file** in YAML format, containing parameters for all enabled RMPs.

This tutorial assumes that you is starting with a URDF file describing their robot and has created a `Robot Description File` using the 
:ref:`isaac_sim_app_tutorial_motion_generation_robot_description_editor`.
In this tutorial, a template files is provided for the remaining `RMPflow` configuration, which is
modified to match the **Cobotta Pro 900** robot.  The tutorial assets contain a completed `robot_description.yaml` for the **Cobotta Pro 900**.

.. _isaac_sim_tutorial_configure_rmpflow_config_yaml:

Template RmpFlow Config YAML File
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The `RMPflow` algorithm has over 50 settable parameters, but these parameters tend to generalize between robots with similar kinematic structures
and length scales. The values in the template have been tuned specifically for the Franka Emika Panda,
but serve as a good starting point for many 6- and 7-dof robot arms.  The template file can be found in
the tutorial assets as `rmpflow_configs/template_rmpflow_config.yaml`.

.. code-block:: yaml
    :linenos:
    :emphasize-lines: 3,81,92

    # Artificially limit the robot joints.  For example:
    # A joint with range +-pi would be limited to +-(pi-.01)
    joint_limit_buffers: [.01, .01, .01, .01, .01, .01, .01]

    # RMPflow has many modifiable parameters, but these serve as a great start.
    # Most parameters will not need to be modified
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
            max_velocity: 4.
            velocity_damping_region: 1.5
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


    # body_cylinders are used to promote self-collision avoidance between the robot and its base
    # The example below defines the robot base to be a capsule defined by the absolute coordinates pt1 and pt2.
    # The semantic name provided for each body_cylinder does not need to be present in the robot URDF.
    body_cylinders:
         - name: base
           pt1: [0,0,.333]
           pt2: [0,0,0.]
           radius: .05


    # body_collision_controllers defines spheres located at specified frames in the robot URDF
    # These spheres will not be allowed to collide with the capsules enumerated under body_cylinders
    # By design, most frames in industrial robots are kinematically unable to collide with the robot base.
    # It is often only necessary to define body_collision_controllers near the end effector
    body_collision_controllers:
         - name: end_effector
           radius: .05

This tutorial focuses on three fields in this file: 

* ``joint_limit_buffers`` introduces artificial joint limits around the joint limits stated in the robot URDF. The shape of the provided ``joint_limit_buffers`` must match the c-space given in the ``robot_description.yaml`` file. Imagining that the template robot has seven revolute joints, the given buffers of .01 on the seven c-space joints mean that RMPflow will drive the robot up to .01 radians from the joint limits given in the robot URDF. If the robot has prismatic joints, a value of .01 would be expressed implicitly in meters.

* ``body_cylinders`` and ``body_collision_controllers`` help RMPflow to avoid self-collision between the end effector and the robot base. ``body_cylinders`` define an imagined robot base using a set of capsules.  

* ``body_collision_controllers`` define collision spheres placed on different frames of the robot URDF. The template code above defines an unmoving capsule in absolute coordinates and a sphere centered around the "end_effector" frame in the robot URDF. `RMPflow` will not allow a collision between the sphere and capsule.

Apart from preventing the end effector from colliding with the base, `RMPflow` does not directly avoid self-collisions based on collision geometry.

For most applications, however, joint limits are sufficient to prevent links in the middle of the kinematic chain from colliding with each other.

.. _isaac_sim_tutorial_configure_rmpflow_cobotta_900:

Modifying the Template for the Cobotta Pro 900
===============================================

.. _isaac_sim_tutorial_configure_rmpflow_bare_minimum:

Doing the Bare Minimum
^^^^^^^^^^^^^^^^^^^^^^

The minimum changes required to get the  **Cobotta** to be able to use RMPflow to follow a target.

The ``rmpflow_config`` file requires little work to get started (`rmpflow_configs/rmpflow_config_basic.yaml` in the tutorial assets):

.. code-block:: yaml
    :linenos:
    :emphasize-lines: 3,22

    # Artificially limit the robot joints.  For example:
    # A joint with range +-pi would be limited to +-(pi-.01)
    joint_limit_buffers: [.01, .01, .01, .01, .01, .01]

    #Omitting `rmp_params` argument

    # body_cylinders are used to promote self-collision avoidance between the robot and its base
    # The example below defines the robot base to be a capsule defined by the absolute coordinates pt1 and pt2.
    # The semantic name provided for each body_cylinder does not need to be present in the robot URDF.
    body_cylinders:
         - name: base
           pt1: [0,0,.333]
           pt2: [0,0,0.]
           radius: .05


    # body_collision_controllers defines spheres located at specified frames in the robot URDF
    # These spheres will not be allowed to collide with the capsules enumerated under body_cylinders
    # By design, most frames in industrial robots are kinematically unable to collide with the robot base.
    # It is often only necessary to define body_collision_controllers near the end effector
    body_collision_controllers:
         - name: right_inner_finger
           radius: .05

To get the robot moving around, you can ignore the ``rmp_params`` argument for now. Modify the ``joint_limit_buffers``
argument to represent that the robot only has six DOFs rather than the seven listed in the template. You have to provide
``body_cylinders``, you will represent the robot base later.  One change was
required to the default ``body_collision_controllers`` argument, that was to change the frame at which you place a collision
sphere. There is no ``end_effector`` frame in the **Cobotta** URDF, so for now pick a frame that is near the end effector:
``right_inner_finger``.

In the `Lula Test Widget`, observe that the robot is able to follow the target and avoid obstacles.
Notice that the frame that `RMPflow` is moving to the target position is not in the center of the gripper. In the `Lula Test Widget`, the 
``right_inner_finger`` is selected as the end effector frame.  The available end effector frames come from the robot URDF file, and there is not a frame resting
in the center of the gripper.

.. _isaac_sim_tutorial_configure_rmpflow_body_cylinders:

Avoiding Self-Collision: Configuring Body Cylinders and Body Collision Controllers
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

With a completed `Robot Description File`, the robot will avoid collisions with external obstacles, but it will not avoid self-collision.
There is limited tooling available for avoiding self-collision because industrial robot arms typically remove most potential for self-collision
with joint limits. However, some exploration is required with a particular robot to learn what types of self-collision are possible.  
With the preliminary configuration of body cylinders and body collision controllers. You set in the ``Cobotta_Pro_900_Assets/rmpflow_configs/cobotta_rmpflow_config_basic.yaml`` file, 
it is easy to cause collisions between the robot end effector and the robot base.

``body_cylinders`` define an imagined robot base using a set of capsules.  ``body_collision_controllers`` define collision spheres placed
on different frames of the robot URDF.

`RMPflow` will not allow these spheres and capsules to come into contact with each other. In the basic ``rmpflow`` config, you defined the base as the capsule
connecting two spheres of radius ``.05 m`` at the absolute coordinates ([0,0,0], [0,0,.333]) (refer to :ref:`isaac_sim_tutorial_configure_rmpflow_bare_minimum`),
and you define a single ``body_collision_controller`` at the ``right_inner_finger`` frame.  

In the video above, you observe that the gripper will not pass directly
through the robot base, but it is easy to facilitate a self-collision with the edge of the robot base, or the base of the second link.

The self-collision tooling available in `RMPflow` does not allow you to avoid all self-collisions without sacrificing some acceptable robot configurations as well.

To make self collisions completely impossible for the **Cobotta**, you need a very conservative estimate of the robot base. 
You would not allow the gripper to move close to the base at all.  Choosing the best possible configuration is use-case dependent.
There is no reason to take away maneuverability around the robot base unless you observe that the robot is self-colliding.

One potential configuration in this tutorial covers the other frames in the gripper and exaggerates the size of the robot base to make it
harder for the gripper to intersect with the robot's second link. The sizes and locations for the capsule and spheres are based on the collision spheres that
you've already added.


.. code-block:: yaml
    :linenos:
    :emphasize-lines: 5-12

    # body_cylinders are used to promote self-collision avoidance between the robot and its base
    # The example below defines the robot base to be a capsule defined by the absolute coordinates pt1 and pt2.
    # The semantic name provided for each body_cylinder does not need to be present in the robot URDF.
    body_cylinders:
         - name: base
           pt1: [0,0,.12]
           pt2: [0,0,0.]
           radius: .08
         - name: second_link
           pt1: [0,0,.12]
           pt2: [0,0,.12]
           radius: .16


    # body_collision_controllers defines spheres located at specified frames in the robot URDF
    # These spheres will not be allowed to collide with the capsules enumerated under body_cylinders
    # By design, most frames in industrial robots are kinematically unable to collide with the robot base.
    # It is often only necessary to define body_collision_controllers near the end effector
    body_collision_controllers:
         - name: J5
           radius: .05
         - name: J6
           radius: .05
         - name: right_inner_finger
           radius: .02
         - name: left_inner_finger
           radius: .02
         - name: right_inner_knuckle
           radius: .02
         - name: left_inner_knuckle
           radius: .02

You represent the robot base link "J1" with a capsule of radius .08 m, which matches the size of the collision spheres in near the base of the robot.
You represent the robot's second link with a large sphere of radius .12.  
In the `Lula Test Widget`, you observe the robot does a much better job avoiding collisions with the first and second link.
As expected, it is still possible to cause a self-collision, but the cases are much more limited.

.. _isaac_sim_tutorial_configure_rmpflow_end_effector_frame:

Creating an End Effector Frame
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Observe that the chosen end effector frame ``right_inner_finger`` does not directly
represent the position of the robot's gripper. The frame that `RMPflow` considers to be the end effector must be present in the robot URDF.
In this tutorial, you selected a frame near the end of the robot as the best option. To directly control where the center of the gripper is, you have two options:

* Manually compute transforms between the desired target and the target you send to `RMPflow` at runtime.
* Add a frame to the robot's URDF.

This tutorial covers the second option by adding a frame to the **Cobotta Pro 900** URDF. Typically, the end effector position is in
the center of the gripper, with two principal axes aligned with the gripper fingers.

Investigating the **Cobotta Pro 900** URDF, you observe how the "right_inner_finger" frame is connected to the robot arm.
In the URDF, you observe that the "right_inner_finger" joint is a grandchild of the "onrobot_rg6_base_link" frame, which is at the gripper base.

.. code-block:: xml
    :linenos:
    :emphasize-lines: 1-3,10-12

    <joint name="right_inner_finger_joint" type="revolute">
        <origin rpy="0 0 0" xyz="0 -0.047334999999999995 0.064495"/>
        <parent link="right_outer_knuckle"/>
        <child link="right_inner_finger"/>
        <axis xyz="1 0 0"/>
        <limit effort="1000" lower="-0.872665" upper="0.872665" velocity="2.0"/>
        <mimic joint="finger_joint" multiplier="1" offset="0"/>
      </joint>

    <joint name="right_outer_knuckle_joint" type="revolute">
        <origin rpy="0 0 3.141592653589793" xyz="0 0.024112 0.136813"/>
        <parent link="onrobot_rg6_base_link"/>
        <child link="right_outer_knuckle"/>
        <axis xyz="1 0 0"/>
        <limit effort="1000" lower="-0.628319" upper="0.628319" velocity="2.0"/>
        <mimic joint="finger_joint" multiplier="-1" offset="0"/>
      </joint>

This tells us that you can create a frame that is offset from the "``onrobot_rg6_base_link``" frame by a pure Z offset of ``.064495+.136813=.2013`` to represent a point in the center of the gripper, aligned with the "``right_inner_finger_joint``" and "``left_inner_finger_joint``". To get closer with the tips of the fingers, increase the Z offset to .24.

Add a link to the URDF called "gripper_center", whose offset from the parent link "``onrobot_rg6_base_link``" is defined by the connection
"``gripper_center_joint``". In the tutorial file, the modified URDF is saved as ``./cobotta_pro_900_gripper_frame.urdf``.

.. code-block:: xml
    :linenos:

    <link name="gripper_center"/>
      <joint name="gripper_center_joint" type="fixed">
        <origin rpy="0 0 0" xyz="0.0 0.0 .24"/>
        <parent link="onrobot_rg6_base_link"/>
        <child link="gripper_center"/>
      </joint>



You observe in the video that the Z axis of the target lies along the center of the gripper and that the Y axis of the target is aligned with the gripper plane.

This video uses three of the provided config files:

.. code-block:: yaml

    ./robot_description.yaml
    ./cobotta_pro_900_gripper_frame.urdf
    ./rmpflow_configs/cobotta_rmpflow_config_basic.yaml

.. figure:: /images/isim_5.0_full_ref_gui_lula_test_widget.webp
    :align: center


Modifying RMPflow Parameters
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

There is one remaining piece of the RMPflow config files left to modify, `the RMPflow` parameters in ``rmpflow_config.yaml``.
Typically not much modification of the parameters from the template is needed.  `RMPflow` terms work well for robots with similar scales.
The template `RMPflow` config was tuned based on the **Franka Emika Panda** robot.

There is one RMPflow parameter that is robot-specific, ``joint_velocity_cap_rmp``. This term sets a limit on the maximum velocity that is allowed by `RMPflow` for any joint in the specified configuration space.
Investigating the URDF, you observe that each joint in the **Cobotta Pro 900** has a velocity limit of ``1 rad/s``.

.. code-block:: xml
    :linenos:
    :emphasize-lines: 6

    <joint name="joint_6" type="revolute">
        <parent link="J5"/>
        <child link="J6"/>
        <origin rpy="0.000000 0.000000 0.000000" xyz="0.000000 0.120000 0.160000"/>
        <axis xyz="-0.000000 -0.000000 1.000000"/>
        <limit effort="1" lower="-6.28318530717959" upper="6.28318530717959" velocity="1"/>
        <dynamics damping="0" friction="0"/>
      </joint>

To make sure that `RMPflow` respects these joint velocity limits, you can modify template parameters so that `RMPflow` will start damping the velocity of a joint when it comes within ``.3 rad/s`` of the ``1 rad/sec`` limit:

.. code-block:: yaml
    :linenos:
    :emphasize-lines: 2-3

    joint_velocity_cap_rmp:
        max_velocity: 1.
        velocity_damping_region: .3
        damping_gain: 1000.0
        metric_weight: 100.

.. Note:: The PD gains from the provided Cobotta Pro 900 USD file are based off the PD gains that you chose for the Franka Emika Panda of P=10000 N*m and D=1000 N*m*s. These values produced oscillations in the Cobotta Pro 900 when you reduced the ``max_velocity joint_velocity_cap_rmp`` term to ``1 rad/sec``. The USD provided for the Cobotta robot in this tutorial has a proportional gain of 10000 N*m damping gain of 10000 N*m*s.

Refer to :ref:`isaac_sim_motion_generation_rmpflow_tuning_guide` for more details about the meaning of each `RMPflow` parameter with and a description of how to improve `RMPflow` parameters for new robots.

Summary
=======

This tutorial builds on the `Lula Robot Description Editor` tutorial to complete the process of configuring RMPflow on a new robot. In it, you:

    1. Modify a template `rmpflow_config.yaml` file to fit a specific robot.
    2. Tune self-collision avoidance behavior.
    3. Create a new end effector frame that can be used by `RMPflow`.

Further Learning
^^^^^^^^^^^^^^^^

To understand the motivation behind the structure and usage of `RmpFlow` in |isaac-sim|, reference the :ref:`isaac_sim_motion_generation` page.
