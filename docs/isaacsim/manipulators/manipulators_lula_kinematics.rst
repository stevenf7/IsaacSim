.. _isaac_sim_app_tutorial_motion_generation_lula_kinematics:

=======================
Lula Kinematics Solver
=======================

.. note::
   For new development, consider using the newer :doc:`cuMotion Integration <../../cumotion/index>`, which is built on the new experimental motion generation API and provides improved interfaces and additional features over Lula.

This tutorial shows how the :ref:`isaac_sim_lula_kinematics_solver` class is used to compute forward and inverse kinematics on a robot in |isaac-sim|.

Getting Started
===============

**Prerequisites**

- Complete the :ref:`isaac_sim_app_tutorial_core_adding_manipulator` tutorial prior to beginning this tutorial.
- You can reference the :ref:`isaac_sim_app_tutorial_motion_generation_robot_description_editor` to understand how to generate your own `robot_description.yaml` file to be able to use ``LulaKinematicsSolver`` on unsupported robots.
- Review the :ref:`Loaded Scenario Extension Template <isaac_sim_app_tutorial_extension_templates_loaded_scenario>` to understand how this tutorial is structured and run.

To follow along with the tutorial, run your Isaac Sim 6.0 instance. Then open **Window > Extensions**, search for **Motion Generation Examples** (``isaacsim.robot_motion.motion_generation.examples``), and enable it. If you cannot find it, remove ``@feature`` from the Extensions search bar and search again.
Within the `isaacsim.robot_motion.motion_generation.examples` extension, there is a fully functional example using a ``LulaKinematicsSolver`` to track a task-space target.
The sections of this tutorial build up the file ``scenario.py`` from basic functionality to the completed code.

.. note::
   **Motion Generation Examples** (``isaacsim.robot_motion.motion_generation.examples``) are deprecated **since Isaac Sim 6.0.0**. In the Isaac Sim source repository they live under ``source/deprecated/isaacsim.robot_motion.motion_generation.examples``; the extension id is unchanged.

   **Replacement:** Use the ``isaacsim.robot_motion.cumotion.examples`` extension and the :doc:`cuMotion Integration <../../cumotion/index>` tutorials.

Using the LulaKinematicsSolver to Compute Forward and Inverse Kinematics
========================================================================

The :ref:`isaac_sim_lula_kinematics_solver` is able to calculate forward and inverse kinematics for a robot that is defined
by two configuration files (see :ref:`isaac_sim_lula_kinematics_solver_configuration`).  The ``LulaKinematicsSolver`` can be paired with
an :ref:`isaac_sim_articulation_kinematics_solver` to compute kinematics in a way that can be directly applied to the robot ``Articulation``.

The file ``/Lula_Kinematics_python/scenario.py`` uses the ``LulaKinematicsSolver`` to generate inverse kinematic solutions to move the robot to a target.

.. literalinclude:: ../snippets/manipulators/manipulators_lula_kinematics/using_the_lulakinematicssolver_to_compute_forward_.py
    :language: python

The ``LulaKinematicsSolver`` is instantiated on lines 41-47 using file paths to the appropriate configuration files.  The
``LulaKinematicsSolver`` uses the same robot description files as the Lula-based :ref:`isaac_sim_motion_generation_rmpflow` :ref:`isaac_sim_motion_policy`.
The ``LulaKinematicsSolver`` can solve forward and inverse kinematics at any frame that exists in the robot URDF file.
On line 54, the complete list of recognized frames in the Franka robot is printed:

.. code-block:: console

    Valid frame names at which to compute kinematics:
    ['base_link', 'panda_link0', 'panda_link1', 'panda_link2', 'panda_link3', 'panda_link4', 'panda_forearm_end_pt', 'panda_forearm_mid_pt',
     'panda_forearm_mid_pt_shifted', 'panda_link5', 'panda_forearm_distal', 'panda_link6', 'panda_link7', 'panda_link8', 'panda_hand',
     'camera_bottom_screw_frame', 'camera_link', 'camera_depth_frame', 'camera_color_frame', 'camera_color_optical_frame', 'camera_depth_optical_frame',
     'camera_left_ir_frame', 'camera_left_ir_optical_frame', 'camera_right_ir_frame', 'camera_right_ir_optical_frame', 'panda_face_back_left',
     'panda_face_back_right', 'panda_face_left', 'panda_face_right', 'panda_leftfinger', 'panda_leftfingertip', 'panda_rightfinger', 'panda_rightfingertip', 'right_gripper', 'panda_wrist_end_pt']

Supported robots can be loaded directly by name as on lines 50-52.  This is equivalent to lines 41-47.

On line 57, an :ref:`isaac_sim_articulation_kinematics_solver` is instantiated with the Franka robot ``Articulation``, the ``LulaKinematicsSolver`` instance,
and the end effector name.  The ``ArticulationKinematicsSolver`` class allows you to
compute the end effector position and orientation for the robot ``Articulation`` in a single line (line 75).

The ``ArticulationKinematicsSolver`` also allows you to compute inverse kinematics.
The current position of the robot ``Articulation`` is used as a warm start in the IK calculation,
and the result is returned as an ``ArticulationAction`` that can be consumed by the robot ``Articulation``
to move the specified end effector frame to a target position (lines 67 and 70).

The ``LulaKinematicsSolver`` returns a flag marking the success or failure of the inverse kinematics computation.  On line
67, the script applies the inverse kinematics solution to the robot ``Articulation`` only if the kinematics converged
successfully to a solution, otherwise no new action is sent to the robot,
and a warning is thrown. The ``LulaKinematicsSolver`` exposes
settings that allow you to specify how quickly it terminates its search.  These settings are outside the
scope of this tutorial.

The ``LulaKinematicsSolver`` assumes that the robot base is positioned at the origin unless another location is specified.  On lines 64-65,
the ``LulaKinematicsSolver`` is given the current position of the robot base on every frame.  This allows the forward
and inverse kinematics to operate using world coordinates.  For example, the position of the target is queried in world
coordinates and passed to the ``LulaKinematicsSolver``, which internally performs the necessary transformation to compute
accurate inverse kinematics.

The ``LulaKinematicsSolver`` can be used on its own to compute forward kinematics at any position and to compute
inverse kinematics with any warm start.  A robot ``Articulation`` does not need to be present on the USD stage. See :ref:`isaac_sim_kinematics_solver` for more details.

Additionally, sending an inverse kinematic solution directly to the robot is not likely to be useful beyond demonstrations.
In a realistic scenario, you need to determine not only the end position of the robot, but also the path to get there. An IK solver on its own can make
for only a rudimentary trajectory through space that is not likely to be optimal.

.. figure:: /images/isim_4.5_full_tut_gui_lula_kinematics.webp
   :align: center

Summary
=======

This tutorial reviews how to load the ``LulaKinematicsSolver`` class and use it alongside the ``ArticulationKinematicsSolver``
helper class to compute forward and inverse kinematics at any frame specified in the robot URDF file.

Further Learning
^^^^^^^^^^^^^^^^

To understand the motivation behind the structure and usage of ``LulaKinematicsSolver`` in |isaac-sim|, reference the :ref:`isaac_sim_motion_generation`
page.
