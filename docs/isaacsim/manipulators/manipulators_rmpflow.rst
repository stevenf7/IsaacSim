.. _isaac_sim_app_tutorial_motion_generation_rmpflow:

============================
Lula RMPflow
============================

.. note::
   For new development, consider using the newer :doc:`cuMotion Integration <../../cumotion/index>`, which is built on the new experimental motion generation API and provides improved interfaces and additional features over Lula.

This tutorial shows how the :ref:`isaac_sim_motion_generation_rmpflow` class in the :ref:`isaac_sim_motion_generation` can be used to
generate smooth motions to reach task-space targets while avoiding dynamic obstacles.  This tutorial demonstrates how:

*  ``RmpFlow`` can be directly instantiated and used to generate motions using a custom robot description file
*  ``RmpFlow`` can be loaded and used on supported robots
*  built-in debugging features can improve easy of use and integration

Getting Started
===============

**Prerequisites**

- Complete the :ref:`isaac_sim_app_tutorial_core_adding_manipulator` tutorial prior to beginning this tutorial.
- Review the :ref:`Loaded Scenario Extension Template <isaac_sim_app_tutorial_extension_templates_loaded_scenario>` to understand how this tutorial is structured and run.


To follow along with the tutorial, run your Isaac Sim 6.0 instance. Then open **Window > Extensions**, search for **Motion Generation Examples** (``isaacsim.robot_motion.motion_generation.examples``), and enable it. If you cannot find it, remove ``@feature`` from the Extensions search bar and search again.
Within the `isaacsim.robot_motion.motion_generation.examples` extension, there is a fully functional example of RMPflow including following a target, world awareness,
and a debugging option.  The sections of this tutorial build up the file ``scenario.py`` from basic functionality to the completed code.

.. note::
   **Motion Generation Examples** (``isaacsim.robot_motion.motion_generation.examples``) are deprecated **since Isaac Sim 6.0.0**. In the Isaac Sim source repository they live under ``source/deprecated/isaacsim.robot_motion.motion_generation.examples``; the extension id is unchanged.

   **Replacement:** Use the ``isaacsim.robot_motion.cumotion.examples`` extension and the :doc:`cuMotion Integration <../../cumotion/index>` tutorials.

Generating Motions with an RMPflow Instance
============================================

:ref:`isaac_sim_motion_generation_rmpflow` is used heavily throughout |isaac-sim| for controlling robot manipulators.  As documented
in :ref:`isaac_sim_motion_generation_rmpflow_configuration`, there are three configuration files needed to directly instantiate the ``RmpFlow`` class directly.
After these configuration files are loaded and an end effector target has been specified, actions can be computed to move the robot to the desired target.


.. literalinclude:: ../snippets/manipulators/manipulators_rmpflow/generating_motions_with_an_rmpflow_instance.py
    :language: python

``RMPflow`` is an implementation of the :ref:`isaac_sim_motion_policy` interface.
Any `MotionPolicy` can be passed to an :ref:`isaac_sim_articulation_motion_policy`
to start moving a robot on the USD stage.  On line 43, an instance of ``RmpFlow`` is instantiated
with the required configuration information.  The ``ArticulationMotionPolicy`` created on line 52 acts as a
translational layer between ``RmpFlow`` and the simulated Franka robot ``Articulation``. You can interact with
``RmpFlow`` directly to communicate the world state, set an end effector target, or modify internal settings.
On each frame, an end effector target is passed directly to the ``RmpFlow`` object (line 60).
The ``ArticulationMotionPolicy`` is used on line 64 to compute an action that can be directly consumed by the
Franka ``Articulation``.

.. note:: 
    The RMPflow algorithm takes in consideration the robot structure provided by the configuration URDF file. If working on a robot with assembled components (for example, a UR10 with a gripper attached), the URDF file should be updated to reflect the correct robot structure and contain the offset of the gripper at the end effector frame, or additional control joints. The final assembly URDF can be exported with the :ref:`USD to URDF Exporter <isaac_sim_app_extension_urdf_exporter>`. When modifying the source URDF file, it is recommended to review and update the :ref:`Robot Description file <isaac_sim_app_tutorial_motion_generation_robot_description_editor>` to ensure that the correct supplemental file is being used.

.. figure:: /images/isim_4.5_full_tut_gui_rmpflow.webp
   :align: center

World State
^^^^^^^^^^^^^

As a :ref:`isaac_sim_motion_policy`, ``RmpFlow`` is capable of dynamic collision avoidance
while navigating the end effector to a target.  The world state can be
changing over time while ``RmpFlow`` is navigating to its target.  Objects created with the ``isaacsim.core.api.objects`` package
(see :ref:`isaac_sim_motion_policy_world_state`) can be registered with ``RmpFlow`` and the policy will automatically avoid collisions with these obstacles.
``RmpFlow`` is triggered to query the current state of all tracked objects whenever ``RmpFlow.update_world()`` is called.

``RmpFlow`` can also be informed about a change in the robot base pose on a given frame by calling ``RmpFlow.set_robot_base_pose()``.
As object positions are queried in world coordinates, it is critical to use this function, if the base of the robot is moved
within the USD stage.

.. literalinclude:: ../snippets/manipulators/manipulators_rmpflow/world_state.py
    :language: python

On lines 22, an obstacle is added to the stage, and on line 40, it is registered as an obstacle with ``RmpFlow``.
On each frame, ``RmpFlow.update_world()`` is called (line 56).  This triggers ``RmpFlow`` to query the current position of the cube to account for any movement.

On lines 59-60, the current position of the robot base is queried and passed to ``RmpFlow``.
This step is separated from other world state because
it is often unnecessary (when the robot base never moves from the origin), or this step might require extra consideration
(for example, ``RmpFlow`` is controlling an arm that is mounted on a moving base).

Loading RMPflow for Supported Robots
========================================

In the previous sections, observe that ``RmpFlow`` requires five arguments to be initialized.  Three of these arguments are file paths to required configuration files.
The ``end_effector_frame_name`` argument specifies what frame on the robot (from the frames found in the referenced URDF file) should be considered the end effector.
The ``maximum_substep_size`` argument specifies a maximum step-size when internally performing the Euler Integration.

For manipulators in the |isaac-sim| library, appropriate config information for loading `RmpFlow` can be found in the ``isaacsim.robot_motion.motion_generation`` extension.
This information is indexed by robot name and can be accessed simply.
The following change shows how loading configs for supported robots can be simplified.

.. literalinclude:: ../snippets/manipulators/manipulators_rmpflow/loading_rmpflow_for_supported_robots.py
    :language: python

A supported set of robots can have their RMPflow configs loaded by name.
Line 34 prints the names of every supported robot with a provided RMPflow config (at the time of writing this tutorial):

    ['Franka', 'UR3', 'UR3e', 'UR5', 'UR5e', 'UR10', 'UR10e', 'UR16e', 'Rizon4', 'Cobotta_Pro_900', 'Cobotta_Pro_1300', 'RS007L', 'RS007N', 'RS013N', 'RS025N', 'RS080N', 'Techman_TM12', 'Kuka_KR210', 'Fanuc_CRX10IAL']

On lines 35,38, the RmpFlow class initializer is simplified to unpacking a dictionary of loaded keyword arguments.  
The ``load_supported_motion_policy_config()`` function is  the simplest way to load supported robots.
 

Debugging Features
==================

The ``RmpFlow`` class has contains debugging features that are not generally available in the :ref:`isaac_sim_motion_policy` interface. 
These debugging features allow decoupling of the simulator from the RmpFlow algorithm to help diagnose any undesirable behaviors
that are encountered (:ref:`isaac_sim_motion_generation_rmpflow_debugging_features`).

``RmpFlow`` uses collision spheres internally to avoid collisions with external objects.  These spheres can be visualized with
the ``RmpFlow.visualize_collision_spheres()`` function.  This helps to determine whether ``RmpFlow`` has a reasonable representation
of the simulated robot.

The visualization can be used alongside a flag ``RmpFlow.set_ignore_state_updates(True)`` to ignore state updates from the robot
``Articulation`` and instead assume that robot joint targets returned by ``RmpFlow`` are always perfectly achieved.  This causes ``RmpFlow``
to compute a robot path over time that is independent of the simulated robot ``Articulation``.  At each timestep, ``RmpFlow`` returns joint
targets that are passed to the robot ``Articulation``.


.. literalinclude:: ../snippets/manipulators/manipulators_rmpflow/debugging_features.py
    :language: python

The collision sphere visualization can be very helpful to distinguish between behaviors that are coming from the simulator, and behaviors that are coming from ``RmpFlow``.
In the image below, the Franka robot is given weak proportional gains (lines 43-44).  Using the debugging visualization, it is easy to
determine that RmpFlow is producing reasonable motions, but the simulated robot is simply not able to follow the motions.  When RMPflow moves the robot quickly,
the Franka robot ``Articulation`` lags significantly behind the commanded position.

.. figure:: /images/isim_6.0_full_tut_gui_rmpflow_debug.png
   :align: center

Summary
=======

This tutorial reviews using the ``RmpFlow`` class to generate reactive motions in response to a dynamic environment.  The ``RmpFlow``
class can be used to generate motions directly alongside an :ref:`isaac_sim_articulation_motion_policy`.

This tutorial reviewed four of the main features of ``RmpFlow``:

    1. Navigating the robot through an environment to a target position and orientation.
    2. Adapting to a dynamic world on every frame.
    3. Adapting to a change in the robot's position on the USD stage.
    4. Using visualization to decouple the simulated robot ``Articulation`` from the RMPflow algorithm for quick and easy debugging.

Further Learning
^^^^^^^^^^^^^^^^

To learn how to configure RMPflow for a new robot, review the
:ref:`basic formalism <isaac_sim_motion_generation_rmpflow>`, and then read the
:ref:`RMPflow tuning guide <isaac_sim_motion_generation_rmpflow_tuning_guide>` for practical advice.

To understand the motivation behind the structure and usage of ``RmpFlow`` in |isaac-sim|, reference
the :ref:`isaac_sim_motion_generation` page.
