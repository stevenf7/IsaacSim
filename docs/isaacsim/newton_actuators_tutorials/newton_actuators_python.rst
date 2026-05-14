..
   Copyright (c) 2022-2026, NVIDIA CORPORATION. All rights reserved.
   NVIDIA CORPORATION and its licensors retain all intellectual property
   and proprietary rights in and to this software, related documentation
   and any modifications thereto. Any use, reproduction, disclosure or
   distribution of this software and related documentation without an express
   license agreement from NVIDIA CORPORATION is strictly prohibited.


.. _isaac_sim_newton_actuators_python:

==================================================
Set Up Actuators from Python
==================================================

.. note::

   The ``isaacsim.core.experimental.actuators`` extension is **experimental**.
   APIs may change between releases.

This tutorial walks through building Newton actuators in Python and attaching
them to a Franka robot, without authoring any USD.

By the end of this tutorial you'll know how to:

* Build an :class:`~isaacsim.core.experimental.actuators.ActuatorConfig`
  from the stock ``newton.actuators`` controllers, clamping stages, and delays.
* Construct an :class:`~isaacsim.core.experimental.actuators.ArticulationActuators`
  from a list of Python configs.
* Drive an articulation to a position target through the actuator pipeline.

All code examples come from the complete, runnable file ``newton_actuators_python_example.py``:

.. code-block:: bash

    # Newton Actuators Python example
    ./python.sh standalone_examples/api/isaacsim.core.experimental.actuators/newton_actuators_python_example.py

**Prerequisites**

* Read :ref:`isaac_sim_newton_actuators_tutorials` for the high-level structure
  of a Newton actuator pipeline.

Building a stock PD actuator config
==================================================

:class:`~isaacsim.core.experimental.actuators.ActuatorConfig` is a thin bundle
of three components: a required Newton ``Controller`` plus an optional list of
``Clamping`` stages and an optional ``Delay``.  The simplest case is a PD
controller with no clamping and no delay:

.. literalinclude:: ../../../source/standalone_examples/api/isaacsim.core.experimental.actuators/newton_actuators_python_example.py
   :start-after: <start-build-pd-config-snippet>
   :end-before: <end-build-pd-config-snippet>
   :language: python

.. note::

   The arrays are sized for ``n_robots``, not for the number of DOFs.  When the
   articulation path matches *N* robot instances, the same actuator is fanned
   out across all *N*; the array entries are the per-instance gains for that
   one actuator.

Adding clamping and delay
==================================================

Most real actuators need at least an effort limit.  Append clamping stages
to ``ActuatorConfig.clamping`` and optionally add a ``Delay`` for
command-input latency:

.. literalinclude:: ../../../source/standalone_examples/api/isaacsim.core.experimental.actuators/newton_actuators_python_example.py
   :start-after: <start-build-pd-with-clamping-snippet>
   :end-before: <end-build-pd-with-clamping-snippet>
   :language: python

Three clamping types ship with Newton:

* ``ClampingMaxEffort`` — symmetric saturation to ``[-max_effort, +max_effort]``.
* ``ClampingDCMotor`` — linear torque-speed envelope for DC motors.
* ``ClampingPositionBased`` — joint-position-dependent effort lookup table.

Constructing ArticulationActuators
==================================================

Use :meth:`~isaacsim.core.experimental.actuators.ArticulationActuators.from_actuators`
to skip USD discovery and supply the configs directly.  Each config is paired
with the **DOF name** (the leaf of the joint's USD path) it should drive:

.. literalinclude:: ../../../source/standalone_examples/api/isaacsim.core.experimental.actuators/newton_actuators_python_example.py
   :start-after: <start-construct-from-actuators-snippet>
   :end-before: <end-construct-from-actuators-snippet>
   :language: python

If the same DOF name appears twice, or the name does not exist on the
articulation, ``from_actuators`` raises :class:`ValueError` with a list of the
DOFs available on the articulation.

.. note::

   The construction snippet ends with a call to
   :meth:`~isaacsim.core.experimental.prims.Articulation.set_dof_armatures`.
   An armature is virtual rotor inertia that many physics engines add to joints
   to improve numerical stability. For externally-driven joints
   the Newton-actuator effort can excite high-frequency dynamics that the
   implicit USD drive normally damps for you. Real motors and gearboxes
   also carry significant rotor inertia, so a non-zero armature is closer
   to physical reality regardless of stability concerns. If you observe high-frequency instability,
   increasing the armature value may help.

Trying the non-ideal actuators
--------------------------------------------------

The companion script supports a ``--non-ideal`` flag that swaps the simple
PD configs for the PD + per-joint effort clamp + 2-step input delay variant
from the previous section:

.. code-block:: bash

   ./python.sh standalone_examples/api/isaacsim.core.experimental.actuators/newton_actuators_python_example.py --non-ideal

Running with this flag is a useful sanity check: the same robot still
tracks the position target, but with saturated effort and delayed
commands — closer to real hardware behavior.

Driving the robot
==================================================

By default, ``ArticulationActuators`` registers a callback that runs
immediately before every physics step.  On each call the callback reads
the current joint state and target, evaluates each actuator's
step pipeline, and writes the resulting joint
effort to the articulation.  You don't drive this loop yourself; once the
``ArticulationActuators`` wrapper is constructed, the actuators are live.

To send commands, write to the underlying
:class:`~isaacsim.core.experimental.prims.Articulation` exactly as you would
without actuators; the callback picks the targets up on the next tick:

.. literalinclude:: ../../../source/standalone_examples/api/isaacsim.core.experimental.actuators/newton_actuators_python_example.py
   :start-after: <start-drive-to-target-snippet>
   :end-before: <end-drive-to-target-snippet>
   :language: python

.. figure:: images/isim_6.0_full_tut_viewport_newton_actuators_python_motion.webp
   :align: center
   :alt: Franka Panda driven to its home pose by the Newton PD actuators built in this tutorial.

   The Franka converges to the home pose under the Newton PD actuators,
   then has a feedforward applied at one joint.

You can also send a feedforward effort that is added on top of the controller
output via
:meth:`~isaacsim.core.experimental.actuators.ArticulationActuators.set_dof_feedforward_effort_targets`.
With ``kp`` and ``kd`` set to zero this becomes a pure open-loop torque drive:

.. literalinclude:: ../../../source/standalone_examples/api/isaacsim.core.experimental.actuators/newton_actuators_python_example.py
   :start-after: <start-feedforward-effort-snippet>
   :end-before: <end-feedforward-effort-snippet>
   :language: python

.. note::

   You don't have to attach an explicit actuator to every joint.  In this
   tutorial the seven arm joints get explicit Newton actuators while the two
   finger joints do not; those finger joints keep their authored
   ``UsdPhysics.DriveAPI`` stiffness and damping and behave exactly as they
   would on a stock Franka.

.. note::
   The method
   :meth:`~isaacsim.core.experimental.actuators.ArticulationActuators.set_dof_feedforward_effort_targets`
   only affects joints that have an explicit actuator.  A feedforward value
   written to a DOF without an explicit actuator has no effect.

When you're done, tear the wrapper down.  ``ArticulationActuators`` is a
context manager; ``__exit__`` calls ``actuated.close()``, which deregisters
all ``SimulationManager`` callbacks owned by the instance.  The recommended
idiom is to construct the wrapper directly inside the ``with`` statement so
its lifetime is bounded by the block (``construct`` below is whichever
factory you wrote — for example
:meth:`~isaacsim.core.experimental.actuators.ArticulationActuators.from_actuators`
or the ``construct_articulation_actuators`` helper from earlier in this
tutorial):

.. literalinclude:: ../../../source/standalone_examples/api/isaacsim.core.experimental.actuators/newton_actuators_python_example.py
   :start-after: <start-context-manager-snippet>
   :end-before: <end-context-manager-snippet>
   :language: python

If a ``with`` block isn't convenient — for example, when the construction
and use happen in different scopes — call ``actuated.close()`` explicitly
when finished.  Either path unhooks the pre-physics callback so the wrapper
stops updating actuator efforts each tick; the articulation itself is
unaffected and continues to exist on the stage.

.. note::

   The built-in controllers, clampings, and delays cover almost every case.
   If you do need something custom, ``ActuatorConfig`` accepts any user-written
   subclass of ``newton.actuators.Controller``, ``Clamping``, or ``Delay`` —
   refer to the Newton documentation for the base-class contracts.  Custom
   subclasses cannot be authored in USD; attach them via
   :meth:`~isaacsim.core.experimental.actuators.ArticulationActuators.from_actuators`.

What's next
==================================================

* :ref:`isaac_sim_newton_actuators_usd` — bake an actuator configuration
  into the robot USD so it is rebuilt automatically on load and travels
  with the asset between |isaac-sim_short| and Isaac Lab.
* :ref:`isaac_sim_newton_actuators_omnigraph` — drive an actuated robot
  from OmniGraph.
