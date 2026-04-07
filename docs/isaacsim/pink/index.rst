.. _isaac_sim_pink:

================
PINK Integration
================

This page provides a high-level overview of the PINK integration to the |isaac-sim_short| :doc:`Motion Generation API <../motion_generation/index>`.
Detailed tutorials for each component are linked at the end of this page.

What is PINK?
-------------

`PINK <https://github.com/stephane-caron/pink>`_ (Python Inverse Kinematics) is an open-source differential inverse kinematics library
built on `Pinocchio <https://github.com/stack-of-tasks/pinocchio>`_ and QP solvers. It formulates IK as a
quadratic program (QP) where weighted tasks form the objective and safety constraints form inequalities.

This integration provides access to PINK's solving capabilities within |isaac-sim_short|:

* **Differential IK Controller**: Reactive, closed-loop end-effector tracking via :class:`PinkIKController`
* **Weighted Multi-Task IK**: Combine frame tracking, posture regularization, velocity damping, and more
* **Safety Constraints**: Joint position limits, velocity limits, and control barrier functions (self-collision, workspace bounds)
* **QP Solver Selection**: Choose from multiple QP backends (``osqp``, ``clarabel``, etc.)

The integration is built around two main classes:

* :class:`PinkRobot` - encapsulates the Pinocchio model, data, and controlled joint names
* :class:`PinkIKController` - implements the :class:`BaseController` interface using PINK's ``solve_ik``

Key Architectural Principles
----------------------------

Reactive Differential IK
#########################

PINK solves differential inverse kinematics: on each control step it computes a joint velocity that steers the robot
toward achieving all tasks at best. The velocity is integrated to produce target joint positions. This makes it a
**reactive controller** (like cuMotion's RMPflow), not a motion planner. For trajectory planning, use the cuMotion
integration or compose PINK-solved waypoints with the Motion Generation API's :class:`Path` and :class:`Trajectory` interfaces.

Extensible Task System
#######################

PINK provides a rich set of task types that can be combined with configurable weights:

* :class:`FrameTask` - End-effector pose tracking (position and orientation)
* :class:`PostureTask` - Joint-space regularization toward a preferred configuration
* :class:`DampingTask` - Velocity minimization for smooth motions
* :class:`RelativeFrameTask` - Regulate the pose of one frame relative to another
* :class:`ComTask` - Center-of-mass position tracking
* :class:`JointCouplingTask` - Coupled revolute joint constraints
* :class:`LinearHolonomicTask` - General linear equality constraints

The :class:`PinkIKController` manages a :class:`FrameTask` and optional :class:`PostureTask` internally, and accepts
arbitrary additional tasks, limits, and barriers through its constructor.

Safety Barriers (Control Barrier Functions)
############################################

PINK supports control barrier functions (CBFs) that enforce safety constraints as QP inequalities:

* :class:`SelfCollisionBarrier` - Minimum distance between collision pairs using the robot's collision model
* :class:`PositionBarrier` - Workspace bounds on frame positions
* :class:`BodySphericalBarrier` - Minimum distance between two robot frames

Barriers are passed to :class:`PinkIKController` via the ``extra_barriers`` parameter.

Coordinate Frame Conversion
############################

The integration provides utility functions to convert between |isaac-sim_short| world-frame
coordinates (position + quaternion ``[w, x, y, z]``) and Pinocchio's ``SE3`` rigid-body transforms.
The general workflow is:

* Read a pose from |isaac-sim_short| as ``(position, quaternion)``
* Convert to a Pinocchio ``SE3`` using :func:`isaac_sim_position_quaternion_to_se3`
* Use the ``SE3`` with PINK tasks (e.g., set a :class:`FrameTask` target)
* If needed, convert results back using :func:`se3_to_isaac_sim_position_quaternion`

Integration with Motion Generation API
---------------------------------------

The PINK integration is built on top of the |isaac-sim_short| Motion Generation API, providing:

* **BaseController Implementation**: :class:`PinkIKController` implements the :class:`BaseController` interface,
  enabling composition with :class:`ControllerContainer`, :class:`ParallelController`, :class:`SequentialController`,
  and :class:`TrajectoryFollower`

.. note::
   PINK does not implement :class:`WorldInterface` for external obstacle tracking. Its collision avoidance is
   limited to self-collision and workspace barriers. For external obstacle-aware motion, use the cuMotion integration
   or combine PINK with cuMotion's :class:`CumotionWorldInterface`.

Known Console Messages
----------------------

When using the ``osqp`` solver backend (the default), the Kit console will display messages like:

.. code-block:: text

   [Error] [omni.kit.app._impl] [py stderr]: ...SparseConversionWarning: Converted matrix 'P' of
   your problem to scipy.sparse.csc_matrix to pass it to solver 'osqp'...

Despite the ``[Error]`` tag, **this is not an error**. It is a Python warning from the ``qpsolvers``
library advising that dense matrices are being converted to sparse format before being passed to OSQP.
The conversion is handled automatically and has negligible performance impact for typical robot IK problem sizes.

Platform Support
----------------

PINK and Pinocchio pip wheels are currently available for **Linux x86_64** only.

Next Steps
----------

For detailed information on each component, see the following tutorials:

Tutorials
#########

.. toctree::
   :maxdepth: 2

   tutorial_robot_configuration
   tutorial_ik_controller
   tutorial_multi_task
