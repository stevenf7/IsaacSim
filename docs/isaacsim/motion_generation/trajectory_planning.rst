Trajectory Planning and Execution
=================================

This tutorial demonstrates how to work with trajectories in the Motion Generation API.

By the end of this tutorial, you'll understand:

* How the :class:`Trajectory` interface works
* How to implement your own trajectory class
* How to convert waypoints to trajectories using :class:`Path`
* How to execute trajectories with :class:`TrajectoryFollower`
* The complete cycle for following trajectories

The standalone example ``trajectory_example.py`` demonstrates trajectory planning and execution:

.. code-block:: bash

    # Trajectory planning and execution with TrajectoryFollower
    ./python.sh standalone_examples/api/isaacsim.robot_motion.experimental.motion_generation/trajectory_example.py

.. note::
   You can run this example with the ``--linear`` flag to use a custom LinearTrajectory instead of the built-in minimal-time trajectory. 
   This demonstrates that :class:`TrajectoryFollower` has no opinion about which trajectory type it follows - it works with any object 
   that implements the :class:`Trajectory` interface:

   .. code-block:: bash

       # Run with custom LinearTrajectory
       ./python.sh standalone_examples/api/isaacsim.robot_motion.experimental.motion_generation/trajectory_example.py --linear

The Trajectory Interface
------------------------

A :class:`Trajectory` represents a continuous path through robot state space that can be queried at any time. The interface is basic and you can implement 
any trajectory planning algorithm you want, as long as it returns an object that implements the :class:`Trajectory` interface. The interface requires two members:

* ``duration`` - A read-only property that returns the total duration of the trajectory in seconds
* :meth:`get_target_state` - A method that returns the desired :class:`RobotState` at a given time along the trajectory

Trajectories start at time 0.0 and end after their ``duration``. If you have discrete waypoints, you'll need to implement interpolation in :meth:`get_target_state` 
to return states for times between waypoints.

Implementing a Custom Trajectory: LinearTrajectory
--------------------------------------------------

Implement a basic trajectory class that performs linear interpolation between waypoints in a fixed time per segment, to demonstrate how to use
the :class:`Trajectory` interface.

1. The :meth:`__init__` method sets up the trajectory with waypoints and computes the duration:

   .. literalinclude:: ../snippets/motion_generation/trajectories/trajectory_example.py
      :start-after: <start-linear-trajectory-init-snippet>
      :end-before: <end-linear-trajectory-init-snippet>
      :language: python

2. Implement the required ``duration`` property, which returns the pre-computed duration:

   .. literalinclude:: ../snippets/motion_generation/trajectories/trajectory_example.py
      :start-after: <start-linear-trajectory-duration-snippet>
      :end-before: <end-linear-trajectory-duration-snippet>
      :language: python

3. Implement the required :meth:`get_target_state` method, which:

   1. finds which segment the time ``time`` falls into
   2. computes an interpolation factor ``alpha`` between 0 and 1
   3. linearly interpolates between the start and end waypoints of that segment
   4. returns the interpolated :class:`RobotState`, or if the time is out of bounds, returns ``None``

.. literalinclude:: ../snippets/motion_generation/trajectories/trajectory_example.py
   :start-after: <start-linear-trajectory-get-target-state-snippet>
   :end-before: <end-linear-trajectory-get-target-state-snippet>
   :language: python

This is a basic example, but it shows that any trajectory class that implements ``duration`` and :meth:`get_target_state` can be used 
with the Motion Generation API. 

For a real scenario, interpolate between waypoints using a minimal time, while respecting
velocity and acceleration limits using the built-in :meth:`Path.to_minimal_time_joint_trajectory` method.

Using Path to Create Minimal-Time Trajectories
-----------------------------------------------

The :class:`Path` class provides a convenient way to work with discrete joint-space waypoints. You can convert a :class:`Path` to a minimal-time 
:class:`Trajectory` using :meth:`Path.to_minimal_time_joint_trajectory`, which takes as inputs:

* ``max_velocities`` - Maximum joint velocities (one per active joint)
* ``max_accelerations`` - Maximum joint accelerations (one per active joint)
* ``robot_joint_space`` - The full joint space of the robot
* ``active_joints`` - Which joints are controlled by this trajectory

and creates a :class:`Trajectory` that moves through all waypoints in minimal time while respecting these constraints. The trajectory uses a trapezoidal velocity profile: 
accelerate to maximum velocity, cruise at that velocity, then decelerate to a stop at the next waypoint.

1. Define your waypoints:

   .. literalinclude:: ../snippets/motion_generation/trajectories/trajectory_example.py
      :start-after: <start-define-waypoints-snippet>
      :end-before: <end-define-waypoints-snippet>
      :language: python

2. Create a Path and convert it to a minimal-time trajectory:

   .. literalinclude:: ../snippets/motion_generation/trajectories/trajectory_example.py
      :start-after: <start-create-minimal-time-trajectory-snippet>
      :end-before: <end-create-minimal-time-trajectory-snippet>
      :language: python

Following Trajectories with TrajectoryFollower
-----------------------------------------------

The :class:`TrajectoryFollower` is a controller that executes any trajectory. It's a bridge between trajectory planning and real-time control. 
The key insight is that :class:`TrajectoryFollower` has **no opinion** about which trajectory type it follows. It works with any object 
that implements the :class:`Trajectory` interface.

The TrajectoryFollower Cycle
##############################

The :class:`TrajectoryFollower` follows a specific use cycle:

1. **Set the trajectory** - Call :meth:`set_trajectory` to provide the trajectory to follow
2. **Reset the controller** - Call :meth:`reset` immediately before starting to set the start time
3. **Call forward each step** - In your control loop, call :meth:`forward` to get the desired state

Here's how to use it:

.. literalinclude:: ../snippets/motion_generation/trajectories/trajectory_example.py
   :start-after: <start-trajectory-follower-cycle-snippet>
   :end-before: <end-trajectory-follower-cycle-snippet>
   :language: python

The :meth:`set_trajectory` method sets the trajectory and clears the start time. The :meth:`reset` method must be called immediately before starting 
to follow the trajectory, because it sets the start time to the current simulation time. This allows the follower to compute how far along the 
trajectory it should be at any given time.

The Complete Control Loop
---------------------------

Here's the complete control loop that brings everything together:

.. literalinclude:: ../snippets/motion_generation/trajectories/trajectory_example.py
   :start-after: <start-trajectory-control-loop-snippet>
   :end-before: <end-trajectory-control-loop-snippet>
   :language: python

The loop:

1. Gets the current estimated state from the robot
2. Calls :meth:`forward` to get the desired state from the trajectory (at the current time)
3. Applies the desired state to the robot
4. Repeats every simulation step

The :class:`TrajectoryFollower` queries the trajectory at the current time (relative to when :meth:`reset` was called). If the trajectory has ended 
or the time is out of bounds, :meth:`forward` returns ``None``.

Comparing Trajectory Types
---------------------------

The example supports both trajectory types through the ``--linear`` flag. You can compare:

* **LinearTrajectory** - Basic linear interpolation with equal time per segment. Easy to understand and implement, but doesn't respect joint limits or 
  optimize for time.

* **Minimal-Time Trajectory** - Optimized trajectory that respects joint velocity and acceleration limits. More complex, but produces 
  smoother motion that respects the robot's physical constraints.

Both work identically with :class:`TrajectoryFollower` to demonstrate the power of the unopinionated interface design.

Observing Trajectory Performance
--------------------------------

When you run the standalone example, you can observe how different trajectory types affect the robot's motion. The motion should be slightly more jerky when you add the ``--linear`` argument, as the linear interpolation between waypoints doesn't respect acceleration limits.

.. figure:: images/isim_6.0_full_tut_viewport_trajectory.webp
   :align: center
   :width: 100%

   Running the minimal-time joint trajectory (trapezoidal velocity profile).

.. figure:: images/isim_6.0_full_tut_viewport_trajectory_linear.webp
   :align: center
   :width: 100%

   Running the linear joint trajectory (equal time per segment).

Summary
-------

The trajectory system in the Motion Generation API is designed to be flexible and unopinionated:

* **Trajectory Interface** - Simple interface (``duration`` + :meth:`get_target_state`) that any trajectory can implement
* **Path Class** - Convenient way to work with discrete waypoints
* **Minimal-Time Conversion** - Built-in conversion that respects joint limits
* **TrajectoryFollower** - :class:`TrajectoryFollower` controller that executes any trajectory type

This design means you can:

* Implement any trajectory planning algorithm (RRT, PRM, optimization-based)
* Use any representation (joint-space, task-space, hybrid)
* Use trajectories as a part of a larger controller composition

As long as your planner outputs something that meets the :class:`Trajectory` interface, the :class:`TrajectoryFollower` can execute it. 
This separation of planning and execution gives you maximum flexibility.