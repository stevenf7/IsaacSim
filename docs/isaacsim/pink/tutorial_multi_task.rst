.. _isaac_sim_pink_tutorial_multi_task:

============================
Multi-Task Tutorial
============================

This tutorial demonstrates how to combine multiple weighted PINK tasks for more complex IK behaviors. You'll learn how
task weights control the trade-off between competing objectives and how to add safety barriers.

By the end of this tutorial, you'll understand:

* How to combine :class:`FrameTask`, :class:`PostureTask`, and :class:`DampingTask`
* How task cost weights affect the IK solution
* How to add extra tasks and barriers to :class:`PinkIKController`
* How to use :class:`SelfCollisionBarrier` for collision avoidance

**Prerequisites**

- Review the :ref:`Robot Configuration tutorial <isaac_sim_pink_tutorial_robot_configuration>` to understand robot loading.
- Review the :ref:`IK Controller tutorial <isaac_sim_pink_tutorial_ik_controller>` to understand the basic controller workflow.

To follow along with the tutorial, you can search and enable the **PINK Examples** extension within your running
|isaac-sim_short| instance. The **Multi-Task** example provides an interactive demonstration with runtime cost-weight
adjustment.

Task Composition
================

PINK solves a single QP that combines all tasks into a weighted least-squares objective:

.. math::

   \min_{v} \sum_{\text{task } e} \| J_e(q) \, v + \alpha \, e(q) \|^2_{W_e}

where :math:`v` is the joint velocity, :math:`J_e` is the task Jacobian, :math:`e(q)` is the task error,
:math:`\alpha` is the gain, and :math:`W_e = \text{diag}(\text{cost})` is the weight matrix. Higher cost means the
solver tries harder to satisfy that task.

The key insight is that tasks **compete** when they cannot all be satisfied simultaneously. Cost weights determine
which tasks take priority.

Using Multiple Tasks with PinkIKController
============================================

The :class:`PinkIKController` manages a :class:`FrameTask` and optional :class:`PostureTask` internally. To add
more tasks, pass them via the ``extra_tasks`` parameter:

.. code-block:: python

    import pink.tasks
    from isaacsim.robot_motion.pink import PinkIKController, load_pink_supported_robot

    pink_robot = load_pink_supported_robot("franka")

    # Create a DampingTask to minimize joint velocities
    damping_task = pink.tasks.DampingTask(cost=1e-4)

    controller = PinkIKController(
        pink_robot=pink_robot,
        robot_joint_space=articulation.dof_names,
        robot_site_space=["panda_hand"],
        tool_frame="panda_hand",
        position_cost=1.0,
        orientation_cost=1.0,
        posture_cost=1e-3,
        extra_tasks=[damping_task],
        dt=1.0 / 60.0,
    )

Understanding Cost Weights
==========================

The cost values are in **normalized units** that allow comparing position errors (meters) with orientation errors
(radians) and joint errors (radians):

* **Position cost** ``[cost/m]``: How much each meter of position error costs
* **Orientation cost** ``[cost/rad]``: How much each radian of orientation error costs
* **Posture cost** ``[cost/rad]``: How much each radian of joint deviation from the target posture costs
* **Damping cost** ``[cost*s/rad]``: How much each radian/second of joint velocity costs

Example trade-offs:

.. code-block:: python

    # Prioritize position accuracy, ignore orientation
    controller = PinkIKController(
        ...,
        position_cost=10.0,
        orientation_cost=0.0,
        posture_cost=1e-3,
        dt=1.0 / 60.0,
    )

    # Smooth motion with loose tracking
    controller = PinkIKController(
        ...,
        position_cost=0.5,
        orientation_cost=0.5,
        posture_cost=1e-2,
        extra_tasks=[pink.tasks.DampingTask(cost=1e-2)],
        dt=1.0 / 60.0,
    )

Updating Costs at Runtime
=========================

Task costs can be modified at runtime without recreating the controller:

.. code-block:: python

    # Adjust frame task costs
    controller.get_frame_task().set_position_cost(2.0)
    controller.get_frame_task().set_orientation_cost(0.0)

    # Adjust posture cost
    posture = controller.get_posture_task()
    if posture is not None:
        posture.cost = 1e-1

    # Adjust extra tasks directly
    damping_task.cost = 1e-3

The Multi-Task example extension provides UI indicators for adjusting these weights interactively.

Adding Self-Collision Barriers
==============================

PINK supports control barrier functions (CBFs) that enforce safety constraints. The most common is
:class:`SelfCollisionBarrier`, which prevents the robot from colliding with itself.

First, load the robot with collision geometry enabled:

.. code-block:: python

    from isaacsim.robot_motion.pink import load_pink_robot

    pink_robot = load_pink_robot(
        urdf_path="/path/to/robot.urdf",
        srdf_path="/path/to/robot.srdf",  # collision pair exclusions
        build_collision_model=True,
    )

Then pass the barrier to the controller:

.. code-block:: python

    from pink.barriers import SelfCollisionBarrier

    barrier = SelfCollisionBarrier(
        n_collision_pairs=10,    # number of closest pairs to monitor
        d_min=0.02,              # minimum allowed distance (meters)
        safe_displacement_gain=1.0,
    )

    controller = PinkIKController(
        pink_robot=pink_robot,
        robot_joint_space=articulation.dof_names,
        robot_site_space=["panda_hand"],
        tool_frame="panda_hand",
        extra_barriers=[barrier],
        dt=1.0 / 60.0,
    )

.. note::
   Self-collision barriers require the robot to be loaded with ``build_collision_model=True`` and an SRDF file
   for best results. Without an SRDF, all collision pairs (including adjacent links) will be checked, which
   may cause the solver to be overly conservative.

Other Available Tasks
=====================

PINK provides additional task types that can be passed via ``extra_tasks``:

* :class:`RelativeFrameTask` - Regulate pose of one frame relative to another (e.g., bimanual coordination)
* :class:`ComTask` - Track center-of-mass position (useful for humanoids)
* :class:`JointCouplingTask` - Enforce linear relationships between joints (e.g., coupled fingers)
* :class:`JointVelocityTask` - Track reference joint velocities
* :class:`LowAccelerationTask` - Minimize joint accelerations for smoother motion
* :class:`LinearHolonomicTask` - General linear equality constraint

Refer to the `PINK documentation <https://stephane-caron.github.io/pink/>`_ for full API details on each task type.

Updating Extra Task Targets with pre_step_callback
===================================================

The controller automatically updates targets for its managed :class:`FrameTask` (from ``setpoint_state.sites``)
and :class:`PostureTask` (from ``setpoint_state.joints``). Extra tasks are **not** auto-updated, tasks like
:class:`DampingTask` or :class:`JointCouplingTask` that have fixed or no targets work as-is, but tasks that need
per-step target updates require the ``pre_step_callback`` parameter.

Some tasks may need per-step updates because their targets change over time:

* :class:`ComTask` -- if the desired center-of-mass follows a trajectory, the target must be set each step
* :class:`RelativeFrameTask` -- to maintain the current relative pose between two frames as the robot moves, the target must be refreshed from the live configuration each step
* :class:`LowAccelerationTask` -- requires ``set_last_integration(v_prev, dt)`` each step to know the previous velocity

The callback is invoked during each ``forward()`` call, after the configuration is updated from the estimated state
but before ``solve_ik`` runs. It receives the current PINK :class:`Configuration` and the ``setpoint_state``:

.. code-block:: python

    from pink.tasks import RelativeFrameTask, ComTask

    relative_task = RelativeFrameTask(
        "left_hand", "right_hand",
        position_cost=1.0, orientation_cost=0.5,
    )
    com_task = ComTask(cost=0.1)

    def update_targets(configuration, setpoint_state):
        relative_task.set_target_from_configuration(configuration)
        com_task.set_target(desired_com_position)

    controller = PinkIKController(
        pink_robot=pink_robot,
        robot_joint_space=articulation.dof_names,
        robot_site_space=["panda_hand"],
        tool_frame="panda_hand",
        extra_tasks=[relative_task, com_task],
        pre_step_callback=update_targets,
        dt=1.0 / 60.0,
    )

The callback has full access to the :class:`Configuration` object, which provides forward kinematics,
Jacobians, and frame placements, required to compute task-specific targets.

Other Available Barriers
========================

Beyond self-collision, PINK provides:

* :class:`PositionBarrier` - Keep a frame's position within axis-aligned bounds
* :class:`BodySphericalBarrier` - Maintain minimum distance between two robot frames

These are passed to :class:`PinkIKController` via the ``extra_barriers`` parameter.

Additional Limits
=================

By default, PINK automatically creates :class:`ConfigurationLimit` and :class:`VelocityLimit` from the Pinocchio
model (which reads them from the URDF joint limits). For additional constraints, use the ``extra_limits`` parameter:

* :class:`AccelerationLimit` - Bound joint accelerations
* :class:`FloatingBaseVelocityLimit` - Clamp base twist for floating-base robots

Summary
=======

This tutorial demonstrated:

1. **Task Composition**: Combining :class:`FrameTask`, :class:`PostureTask`, and :class:`DampingTask`
2. **Cost Weights**: How weights control the trade-off between competing tasks
3. **Runtime Tuning**: Modifying task costs without recreating the controller
4. **Self-Collision Barriers**: Using :class:`SelfCollisionBarrier` for safety
5. **Pre-Step Callback**: Updating extra task targets via ``pre_step_callback`` for tasks that need per-step updates
6. **Additional Tasks**: Overview of all available PINK task, barrier, and limit types

The multi-task architecture provides a flexible, extensible framework for specifying complex IK behaviors through weighted objectives and safety constraints.

Next Steps
----------

* :ref:`cuMotion Integration <isaac_sim_cumotion>` - GPU-accelerated motion planning with obstacle avoidance
* `PINK documentation <https://stephane-caron.github.io/pink/>`_ - Full API reference for tasks, limits, and barriers
