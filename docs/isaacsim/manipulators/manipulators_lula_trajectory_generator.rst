.. _isaac_sim_app_tutorial_motion_generation_lula_trajectory_generator:

============================================
Lula Trajectory Generator
============================================

.. note::
   For new development, consider using the newer :doc:`cuMotion Integration <../../cumotion/index>`, which is built on the new experimental motion generation API and provides improved interfaces and additional features over Lula.

This tutorial explores how the :ref:`isaac_sim_lula_trajectory_generator` in the :ref:`isaac_sim_motion_generation` extension can be used to create both task-space and c-space trajectories that can be easily applied to a simulated robot ``Articulation``.

Getting Started
===============

**Prerequisites**

- Complete the :ref:`isaac_sim_app_tutorial_core_adding_manipulator` tutorial prior to beginning this tutorial.
- You can reference the :ref:`isaac_sim_app_tutorial_motion_generation_robot_description_editor` to understand how to generate your own ``robot_description.yaml`` file to be able to use the :ref:`isaac_sim_lula_trajectory_generator` on unsupported robots.
- Review the :ref:`Loaded Scenario Extension Template <isaac_sim_app_tutorial_extension_templates_loaded_scenario>` to understand how this tutorial is structured and run.

To follow along with the tutorial, you can search and enable the **Motion Generation Examples** extension within your running Isaac Sim 6.0 instance.
Within the `isaacsim.robot_motion.motion_generation.examples` extension, there an example of the ``LulaTaskSpaceTrajectorygenerator`` and ``LulaCSpaceTrajectoryGenerator`` being used to generate trajectories
connecting specified c-space and task-space points.
The sections of this tutorial build up the file ``scenario.py`` from basic functionality to the completed code.

.. figure:: /images/isim_4.5_full_tut_gui_lula_trajectory_gen.webp
   :align: center

Generating a C-Space Trajectory
================================

The ``LulaCSpaceTrajectoryGenerator`` class is able to generate a trajectory that connects a provided set of c-space waypoints.
The code snippet below demonstrates how, given appropriate config files,
the ``LulaCSpaceTrajectoryGenerator`` class can be initialized and used to create a sequence
of ``ArticulationAction`` that can be set on each frame to produce the desired trajectory.

The code snippet below shows the relevant contents of ``/Trajectory_Generator_python/scenario.py`` from the provided example.

.. literalinclude:: ../snippets/manipulators/manipulators_lula_trajectory_generator/generating_a_c_space_trajectory.py
    :language: python
    :linenos:
    :emphasize-lines: 53-56, 80-81, 99-103

On lines 53-56, the ``LulaCSpaceTrajectoryGenerator`` class is initialized using a URDF and
:ref:`Lula Robot Description File <isaac_sim_app_tutorial_motion_generation_robot_description_editor>`.
The ``LulaCSpaceTrajectoryGenerator`` takes in a series of waypoints, and it connects them in configuration space using spline-based interpolation.
There are two main objectives that can be fulfilled by the trajectory generator:

* time-optimal
* time-stamped

The provided example shows a trajectory that runs quickly, and then runs slowly.  This is seen in the code on lines (80-81 and 99-103).
On line 80, a time-optimal trajectory is created in the form of a ``LulaTrajectory`` object, which fulfills the :ref:`Trajectory Interface <isaac_sim_trajectory>`.
On line 81, a time-stamped trajectory is created that will hit the same waypoints at the times ``[0,5,10,13]`` seconds (line 78).  Time optimality is
defined as saturating at least one of velocity, acceleration, or jerk limits of the robot throughout a trajectory.

On lines 99-103, These ``LulaTrajectory`` objects are passed to ``ArticulationTrajectory`` to generate a sequence of ``ArticulationAction`` that can be passed directly to the
robot ``Articulation``.  The function ``ArticulationTrajectory.get_action_sequence()`` returns a list of ``ArticulationAction`` that is meant to be consumed at the specified
rate.  In this case, the framerate of physics is assumed to be fixed at ``1/60`` seconds.


If no trajectory can be computed that connects the c-space waypoints, the trajectory returned by ``LulaCSpaceTrajectoryGenerator.compute_c_space_trajectory``
will be ``None``.  This can occur when one of the specified c-space waypoints is not reachable or is very close to a joint limit.
This case is handled on lines 90-92.

On lines 84-88, a visualization of the original ``c_space_points`` is created by converting them to task-space points.
This code is not functional, but it helps to verify that the robot is hitting every target.

The ``update()`` function is programmed to play the sequence of ``ArticulationActions`` in a loop, taking a pause of ``10 frames`` for dramatic effect between trajectories.

Generating a Task-Space Trajectory
===================================

Simple Case: Linearly Connecting Waypoints
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Generating a task-space trajectory is similar to generating a c-space trajectory.
In the simplest use-case, you can pass in a set of task-space position and quaternion orientation targets,
which will be linearly interpolated in task-space to produce the resulting trajectory.
An example is provided in the code snippet below:

.. literalinclude:: ../snippets/manipulators/manipulators_lula_trajectory_generator/simple_case_linearly_connecting_waypoints.py
    :language: python

In moving to the task-space trajectory generator, there are few code changes required.  The initialization is nearly the same on line 36 as for the
c-space trajectory generator.  The main changes are on lines 59-61 where a task-space trajectory is specified.  When using the function
``LulaTaskSpaceTrajectoryGenerator.compute_task_space_trajectory_from_points``, a position and orientation target must be specified for each task-space waypoint.
Additionally, a frame from the robot URDF must be specified as the end effector frame.
If the waypoints cannot be connected to form a trajectory, the ``compute_task_space_trajectory_from_points`` function will return ``None``.
This case is checked on line 69.


Defining Complicated Trajectories
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The ``LulaTaskSpaceTrajectoryGenerator`` can be used to create paths with more complicated specifications than to connect a set of task-space targets linearly.
Using the class ``lula.TaskSpacePathSpec``, you can define paths with arcs and circles with multiple options for orientation targets.
The code snippet below demonstrates creating a ``lula.TaskSpacePathSpec`` and gives an example of each available function for adding to a task-space path.
Additionally, it shows how a ``lula.TaskSpacePathSpec`` can be combined with a ``lula.CSpacePathSpec`` in a ``lula.CompositePathSpec`` to specify trajectories
that contain both c-space and task-space waypoints.

.. literalinclude:: ../snippets/manipulators/manipulators_lula_trajectory_generator/defining_complicated_trajectories.py
    :language: python

The code snippet above creates a ``lula.CompositePathSpec`` on line 55 with an initial c-space position.  It is combined with a
``lula.TaskSpacePathSpec`` on lines 108-109 and it is combined with a ``lula.CSpacePathSpec`` on lines 111-112.  The resulting path
is one that starts at the specified ``initial_c_space_robot_pose``, then follows a series of taskspace targets, then hits two c-space
targets.  When combining path specs, a transition mode must be specified to determine how c-space and task-space points should be connected
to each other.  Reference lines 114-120 to see the possible options.  In this case, no constraint is made on how the ``LulaTrajectoryGenerator``
connects these points.

Each available option for specifying a ``lula.TaskSpacePathSpec`` is demonstrated between lines 63-94.
The code snippet above moves mainly between three translations: ``t0, t1, t2`` with possible rotations ``r0, r1``.
The ``lula.TaskSpacePathSpec`` object is created with an initial position on line 63.
Each following ``add`` function that is called adds a path between the last position in the ``path_spec`` so far and a new position.
The basic possibilities are:

    1. Linearly interpolate translation to a new point while keeping rotation fixed (line 71)
    2. Linearly interpolate rotation to a new point while keeping translation fixed (line 74)
    3. Linearly interpolate both rotation and translation to a new 6 DOF point (line 68)

The ``lula.TaskSpacePathSpec`` also makes it easy to define various arcs and circular paths that connect points in space.
A three-point arc can be defined that moves through a midpoint to a translation target.
There are three options for the orientation of the robot while moving along the path:

    1. Keep rotation constant (line 79)
    2. Always stay oriented tangent to the arc (line 82)
    3. Linearly interpolate rotation to a rotation target (line 85)

Finally, a circular path can be specified without defining a midpoint as on lines 88, 91, and 94.
The same three options for specifying orientation are available.

Summary
=======

This tutorial shows how to use the :ref:`isaac_sim_lula_trajectory_generator` to generate c-space and task-space trajectories for a robot.  Task-space trajectories can be specified using a series of task-space waypoints that will be connected linearly, or they can be defined piecewise with many different options for connecting each pair of points in space.

Further Learning
^^^^^^^^^^^^^^^^

Reference the :ref:`isaac_sim_motion_generation` page for a complete description of trajectories in |isaac-sim|.
