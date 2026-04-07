.. _isaac_sim_pink_tutorial_ik_controller:

============================
IK Controller Tutorial
============================

This tutorial demonstrates how to use the :class:`PinkIKController` to generate smooth, reactive motions that track
end-effector targets. This is the PINK analog to the cuMotion :class:`RmpFlowController`.

By the end of this tutorial, you'll understand:

* How to create and configure the :class:`PinkIKController`
* How to use the :class:`BaseController` interface (``reset`` / ``forward``) for closed-loop IK
* How to provide end-effector targets via :class:`RobotState`

**Prerequisites**

- Review the :ref:`Robot Configuration tutorial <isaac_sim_pink_tutorial_robot_configuration>` to understand how to load robot configurations.
- Review the :doc:`Controllers and the RobotState <../motion_generation/mobile_robot_control_example>` tutorial to understand the :class:`BaseController` interface and :class:`RobotState`.

To follow along with the tutorial, you can search and enable the **PINK Examples** extension within your running
|isaac-sim_short| instance. Within the ``isaacsim.robot_motion.pink.examples`` extension, the **IK Controller**
example provides a fully functional demonstration of end-effector tracking.

Key Concepts
============

The :class:`PinkIKController` implements the :class:`BaseController` interface from the
:doc:`Motion Generation API <../motion_generation/index>`. On each ``forward()`` call it:

1. Updates the Pinocchio configuration from the estimated robot joint state
2. Updates the :class:`FrameTask` target from the setpoint (target end-effector pose)
3. Solves a quadratic program to obtain a joint velocity
4. Integrates the velocity and returns the result as a :class:`RobotState`

This produces reactive, closed-loop control where the robot continuously steers toward the target.

Setting Up the Controller
==========================

First, load a robot configuration, then create the controller:

.. code-block:: python

    from isaacsim.robot_motion.pink import PinkIKController, load_pink_supported_robot

    # Load the robot
    pink_robot = load_pink_supported_robot("franka")

    # Get joint and site names from the Isaac Sim articulation
    robot_joint_space = articulation.dof_names
    robot_site_space = ["panda_hand"]  # Pinocchio frame names for the tool

    # Create the controller
    controller = PinkIKController(
        pink_robot=pink_robot,
        robot_joint_space=robot_joint_space,
        robot_site_space=robot_site_space,
        tool_frame="panda_hand",
        position_cost=1.0,        # [cost] / [m]
        orientation_cost=1.0,     # [cost] / [rad]
        posture_cost=1e-3,        # [cost] / [rad] - regularization
        dt=1.0 / 60.0,           # must match your control rate
    )

All parameters after ``robot_site_space`` are keyword-only.

The controller needs:

* **Robot configuration**: A :class:`PinkRobot` loaded via :func:`load_pink_robot` or :func:`load_pink_supported_robot`
* **Joint and site spaces**: The full ordered joint names from the articulation, and the Pinocchio frame name(s) for the end-effector
* **Tool frame**: The Pinocchio frame name to track. Must exist in both the Pinocchio model and ``robot_site_space``
* **Task costs**: Weights controlling the trade-off between position accuracy, orientation accuracy, and posture regularization
* **dt**: The integration timestep in seconds, which **must** match the rate at which ``forward()`` is called. There is no default; omitting it is a ``TypeError``

.. note::
   The ``tool_frame`` must be a frame name as it appears in the Pinocchio model (parsed from the URDF), which may
   differ from Isaac Sim prim path names. Use ``robot.model.frames[i].name`` to list available frames.

Creating RobotState Objects
===========================

The controller requires :class:`RobotState` objects for the estimated state (current robot state) and setpoint state
(target end-effector pose). For details on :class:`RobotState` creation, see the
:doc:`Motion Generation API documentation <../motion_generation/mobile_robot_control_example>`.

**Estimated State** (current robot configuration):

.. code-block:: python

    import isaacsim.robot_motion.experimental.motion_generation as mg

    estimated_state = mg.RobotState(
        joints=mg.JointState.from_name(
            robot_joint_space=robot_joint_space,
            positions=(robot_joint_space, articulation.get_dof_positions()),
            velocities=(robot_joint_space, articulation.get_dof_velocities()),
        )
    )

**Setpoint State** (target end-effector pose):

.. code-block:: python

    setpoint_state = mg.RobotState(
        sites=mg.SpatialState.from_name(
            spatial_space=robot_site_space,
            positions=(["panda_hand"], target_positions),
            orientations=(["panda_hand"], target_orientations),
        ),
    )

Resetting the Controller
==========================

Before the controller can be used, it must be reset once with the estimated state. The ``reset()`` method:

* Creates the internal PINK :class:`Configuration` from the current joint positions
* Initializes the :class:`FrameTask` target to the current end-effector pose
* Initializes the :class:`PostureTask` target to the current joint configuration

The ``forward()`` method returns ``None`` before ``reset()`` is called successfully.

.. code-block:: python

    success = controller.reset(
        estimated_state=estimated_state,
        setpoint_state=None,
        t=0.0,
    )
    assert success, "Reset failed - check that all controlled joints are in the estimated state"

Running the Controller
======================

In each physics step, follow the same pattern as any :class:`BaseController`:

1. Get the current robot state (estimated state)
2. Create a setpoint state with the target end-effector pose
3. Call ``forward()``
4. Apply the resulting desired state to the robot

.. code-block:: python

    def on_physics_step(step: float):
        # 1. Current state
        estimated_state = mg.RobotState(
            joints=mg.JointState.from_name(
                robot_joint_space=robot_joint_space,
                positions=(robot_joint_space, articulation.get_dof_positions()),
                velocities=(robot_joint_space, articulation.get_dof_velocities()),
            )
        )

        # 2. Target pose
        target_positions, target_orientations = target_cube.get_world_poses()
        setpoint_state = mg.RobotState(
            sites=mg.SpatialState.from_name(
                spatial_space=robot_site_space,
                positions=(["panda_hand"], target_positions),
                orientations=(["panda_hand"], target_orientations),
            ),
        )

        # 3. Solve IK
        desired_state = controller.forward(estimated_state, setpoint_state, sim_time)

        # 4. Apply
        if desired_state is not None:
            articulation.set_dof_position_targets(
                positions=desired_state.joints.positions,
                dof_indices=desired_state.joints.position_indices,
            )

If the setpoint state is ``None``, the controller continues to track the prior target.

Choosing a QP Solver
=====================

PINK supports multiple QP solver backends through the ``qpsolvers`` package. The ``solver`` parameter
selects which one to use:

* ``"osqp"`` (default) - Sparse, fast for small-to-large problems
* ``"clarabel"`` - Interior-point method, robust for ill-conditioned problems

.. code-block:: python

    controller = PinkIKController(
        pink_robot=pink_robot,
        robot_joint_space=robot_joint_space,
        robot_site_space=robot_site_space,
        tool_frame="panda_hand",
        solver="clarabel",
        dt=1.0 / 60.0,
    )

Accessing Task Objects
======================

The controller exposes its managed tasks for direct configuration:

.. code-block:: python

    # Access the FrameTask to modify costs at runtime
    frame_task = controller.get_frame_task()
    frame_task.set_position_cost(2.0)
    frame_task.set_orientation_cost(0.0)  # Ignore orientation

    # Access the PostureTask
    posture_task = controller.get_posture_task()
    if posture_task is not None:
        posture_task.cost = 1e-2  # Increase posture regularization

Example Usage
=============

.. note::
   To experiment with this tutorial interactively, see the ``scenario.py`` file in the
   ``isaacsim.robot_motion.pink.examples`` extension at
   ``isaacsim/robot_motion/pink/examples/ik_controller/scenario.py``.

Summary
=======

This tutorial demonstrated:

1. **PinkIKController Setup**: Creating the controller with task costs and solver selection
2. **RobotState Creation**: Building estimated and setpoint states for the controller interface
3. **Controller Lifecycle**: Using ``reset()`` and ``forward()`` for closed-loop IK
4. **QP Solver Selection**: Choosing between ``osqp``, ``clarabel``, and other backends
5. **Task Access**: Modifying task costs at runtime

The :class:`PinkIKController` provides reactive, task-based inverse kinematics that integrates
with the Motion Generation API.

Next Steps
----------

* :ref:`Multi-Task tutorial <isaac_sim_pink_tutorial_multi_task>` - Combining weighted tasks for complex behaviors
* :ref:`cuMotion RMPflow tutorial <isaac_sim_cumotion_tutorial_rmpflow>` - GPU-accelerated reactive control with obstacle avoidance
* `PINK documentation <https://stephane-caron.github.io/pink/>`_ - Full task, limit, and barrier API reference
