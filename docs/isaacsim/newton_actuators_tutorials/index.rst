..
   Copyright (c) 2022-2026, NVIDIA CORPORATION. All rights reserved.
   NVIDIA CORPORATION and its licensors retain all intellectual property
   and proprietary rights in and to this software, related documentation
   and any modifications thereto. Any use, reproduction, disclosure or
   distribution of this software and related documentation without an express
   license agreement from NVIDIA CORPORATION is strictly prohibited.


.. _isaac_sim_newton_actuators_tutorials:

==================================================
Newton Actuators
==================================================

.. note::

   The ``isaacsim.core.experimental.actuators`` extension is **experimental**.
   Public APIs may contain breaking changes in future releases.

Newton actuators let you define a robot's actuator behavior once, and run it identically in
both |isaac-sim_short| and Isaac Lab.  The model is authored in USD (or built
in Python) and travels with the robot asset, so the same actuator runs across
applications without rewriting application-specific control code.

.. important::

   Although the Newton Actuators are provided by the Newton library, they do **not** require Newton to be the physics backend. 
   The actuators are evaluated on the
   application side and work with either supported physics backend
   (|physx| or :ref:`Newton <newton_physics>`). No backend
   switch is required to use them.

This tutorial series walks through driving a Franka Panda with external
actuators, set up three different ways: from Python, in USD, and through an
OmniGraph node.

Why Newton actuators?
==========================

Newton actuators give you:

* **Cross-application portability.** Author an actuator model once and run
  it unchanged in both |isaac-sim_short| and Isaac Lab — no rewrites or
  application-specific control code.
* **Modular actuator models.** Compose a controller with optional clamping
  stages and an input delay from the ``newton.actuators`` library.
* **USD authoring.** Actuator parameters can be authored directly onto a
  robot asset so the configuration travels with the USD file.

The rest of this series covers the |isaac-sim_short| runtime class,
:class:`~isaacsim.core.experimental.actuators.ArticulationActuators`, which
discovers and applies these actuators on each physics tick.

Anatomy of a Newton actuator
==================================

Each actuator is a pipeline of three optional stages applied to one joint:

.. code-block:: text

   target --> [delay] --> [controller] --> [clamping_1] --> … --> effort

* **Delay** *(optional)* — buffers the input target for *N* physics steps
  before the controller sees it.  Models communication or actuator response
  latency.
* **Controller** *(required)* — the control law that produces a raw effort
  from the joint state and the (possibly delayed) target.  Built-in
  controllers include ``ControllerPD``, ``ControllerPID``, ``ControllerNeuralMLP``,
  and ``ControllerNeuralLSTM``.
* **Clamping** *(optional, ordered list)* — post-controller stages that
  saturate or reshape the effort.  Built-in clampings include
  ``ClampingMaxEffort`` (symmetric saturation), ``ClampingDCMotor`` (linear
  torque-speed envelope), and ``ClampingPositionBased`` (joint-position-dependent
  effort lookup).

Each stage is implemented as a Warp-accelerated subclass of
``newton.actuators.Controller``, ``Clamping``, or ``Delay`` provided by the
``newton.actuators`` library.

The ``ArticulationActuators`` class
==================================================

:class:`~isaacsim.core.experimental.actuators.ArticulationActuators` wraps a
single :class:`~isaacsim.core.experimental.prims.Articulation` and is responsible
for, on each physics tick:

1. Reading joint positions and velocities from the articulation.
2. Stepping every owned actuator (delay --> controller --> clamping).
3. Writing the resulting per-DOF effort back to the articulation.
4. Zeroing the joint's USD ``DriveAPI`` gains so the USD Physics drive
   does not fight the actuator output.

Two construction paths are supported:

.. tab-set::

   .. tab-item:: Discover from USD

      Pass an articulation root path.  The constructor traverses the USD
      subtree, parses every ``NewtonActuator`` prim it finds, validates the
      target relationships, and builds the corresponding ``Actuator`` objects.

      .. literalinclude:: ../../../source/standalone_examples/api/isaacsim.core.experimental.actuators/newton_actuators_usd_example.py
         :start-after: <start-discover-from-usd-snippet>
         :end-before: <end-discover-from-usd-snippet>
         :language: python

      Walked through in detail in :ref:`isaac_sim_newton_actuators_usd`.

   .. tab-item:: Build in Python

      Skip USD discovery and supply a list of
      :class:`~isaacsim.core.experimental.actuators.ActuatorConfig` objects
      paired with DOF names.  Useful when the asset has no authored
      actuators or when iterating on parameters.

      .. literalinclude:: ../../../source/standalone_examples/api/isaacsim.core.experimental.actuators/newton_actuators_python_example.py
         :start-after: <start-construct-from-actuators-snippet>
         :end-before: <end-construct-from-actuators-snippet>
         :language: python

      Walked through in detail in :ref:`isaac_sim_newton_actuators_python`.

By default the wrapper registers a pre-physics callback and steps every
actuator automatically; pass ``auto_step_pre_physics=False`` to drive stepping
manually.

Limitations
==================================================

The current release makes a few simplifying assumptions you should be aware of
before designing around it:

* **Only single-DOF joints can be externally actuated.** An actuator's ``newton:targets``
  relationship must point at a ``PhysicsRevoluteJoint`` or
  ``PhysicsPrismaticJoint`` prim, and exactly one such joint per actuator.
  Other joint types (e.g. ``PhysicsSphericalJoint``, ``PhysicsDistanceJoint``,
  ``PhysicsFixedJoint``, or D6 joints) are not currently accepted.
* **No GUI authoring.** USD authoring is currently done either by hand-editing
  ``.usda`` or by calling
  :func:`~isaacsim.core.experimental.actuators.add_actuator` from Python.

Learning Objectives
===================

By the end of this series, you will be able to:

- **Build** an actuator in Python from stock Newton components, attach it to
  an articulation, and drive a robot to a position target.
- **Author** ``NewtonActuator`` prims onto a robot asset so the actuator
  configuration travels with the USD file across applications.
- **Drive** an actuated robot from OmniGraph using the
  ``Articulation Actuators`` node.

Tutorials in This Series
=========================

.. toctree::
   :maxdepth: 1

   newton_actuators_python
   newton_actuators_usd
   newton_actuators_omnigraph
   newton_actuators_tips

To get started, see :ref:`isaac_sim_newton_actuators_python`.
