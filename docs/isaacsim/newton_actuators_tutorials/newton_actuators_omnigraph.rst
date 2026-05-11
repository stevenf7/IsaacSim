..
   Copyright (c) 2022-2026, NVIDIA CORPORATION. All rights reserved.
   NVIDIA CORPORATION and its licensors retain all intellectual property
   and proprietary rights in and to this software, related documentation
   and any modifications thereto. Any use, reproduction, disclosure or
   distribution of this software and related documentation without an express
   license agreement from NVIDIA CORPORATION is strictly prohibited.


.. _isaac_sim_newton_actuators_omnigraph:

==================================================
Drive an Actuated Robot from OmniGraph
==================================================

.. note::

   The ``isaacsim.core.experimental.actuators`` extension is **experimental**.
   Node inputs and behavior may change in future releases.

This tutorial walks through driving an actuated robot from OmniGraph
using the **Articulation Actuators** node provided by
``isaacsim.core.experimental.actuators``.

The node is intentionally thin: on each ``execIn`` pulse it lazily
constructs an
:class:`~isaacsim.core.experimental.actuators.ArticulationActuators` for the
configured ``robotPath`` and (optionally) writes a feedforward effort
target.  All actuator pipeline parameters — controllers, clamping, delays —
come from ``NewtonActuator`` prims authored on the asset.

.. important::

   **The Articulation Actuators node only works on robots whose actuators are
   authored in USD.**  It does not expose the Python construction path
   (``ArticulationActuators.from_actuators``).  If your actuator
   configuration is Python-built or relies on a custom
   ``newton.actuators.Controller`` subclass, drive it from a Python script
   or a custom OmniGraph Python node instead — see
   :ref:`isaac_sim_newton_actuators_python`.

By the end of this tutorial you'll know how to:

* Build a minimal OmniGraph that drives a USD-authored actuated robot.
* Send per-DOF feedforward effort commands through the node.

All code examples come from the complete, runnable file ``newton_actuators_omnigraph_example.py``:

.. code-block:: bash

    # Newton Actuators OmniGraph example
    ./python.sh standalone_examples/api/isaacsim.core.experimental.actuators/newton_actuators_omnigraph_example.py

**Prerequisites**

* A robot asset with ``NewtonActuator`` prims already authored — see
  :ref:`isaac_sim_newton_actuators_usd`.
* Familiarity with :ref:`OmniGraph <isaac_sim_app_tutorial_gui_omnigraph>`.

The Articulation Actuators node
==================================================

The node ships under the **Newton Actuators** category in the graph editor's
node search.  Its full name is ``Articulation Actuators``.

Inputs:

.. list-table::
   :header-rows: 1
   :widths: 20 15 65

   * - Name
     - Type
     - Description
   * - ``execIn``
     - execution
     - Trigger pulse.  When ``autoStepPrePhysics`` is true, this is a no-op
       for stepping but still drives feedforward writes.
   * - ``robotPath``
     - string
     - Articulation root prim path.  Changing this after first compute
       destroys and recreates the underlying ``ArticulationActuators``.
   * - ``autoStepPrePhysics``
     - bool
     - When true (default), the underlying wrapper registers a pre-physics
       callback and steps the actuators automatically every tick.  When
       false, the node calls ``step_actuators`` itself on each ``execIn``.
   * - ``stepDt``
     - double
     - Physics timestep (seconds) used when ``autoStepPrePhysics`` is false.
       Default ``0.016667`` (60 Hz).
   * - ``feedforwardCommand``
     - float[]
     - Per-DOF feedforward effort.  Empty array skips the call.
   * - ``indices``
     - int[]
     - Articulation instance indices the feedforward applies to.  Empty
       array applies to all instances.
   * - ``dofIndices``
     - int[]
     - DOF indices the feedforward applies to.  Empty array applies to all
       DOFs.

The node has no output pins; effort is written directly to the articulation.

The example graph
==================================================

The example graph used by this tutorial looks like this:

.. figure:: images/isim_6.0_full_tut_gui_newton_actuators_omnigraph_inspect.png
   :align: center
   :alt: Action Graph editor showing the example graph: On Playback Tick, a Constant String for the robot path, one Constant Double per DOF feeding a Construct Array, an Articulation Actuators node, and an Articulation Controller node.

   The example Action Graph opened in the editor: tick driver, robot-path
   constant, per-DOF pose constants feeding a target-position array, the
   Articulation Actuators node, and the Articulation Controller node.

It contains:

* **On Playback Tick** — emits an execution event every frame while the
  simulation is playing.
* **Robot Path** (a *Constant String* node) — holds the articulation root
  prim path.  Wiring it once and fanning it out keeps a single source of
  truth so the actuator and controller nodes can never drift out of sync.
* **Target Positions** (a *Construct Array* node, sized to the
  articulation's DOF count) — aggregates one value per DOF into the
  ``double[]`` ``positionCommand`` the controller expects.  For a Franka
  that's 9 entries: 7 arm joints followed by 2 finger joints.
* **Pose0 … Pose8** (one *Constant Double* per DOF) — the actual home-pose
  numbers.  Each is wired into the corresponding ``inputN`` slot of the
  Construct Array.  Splitting the targets across one constant per DOF makes
  it trivial to inspect and tweak any single joint target in the editor.
* **Articulation Actuators** — the experimental Newton actuator node.
  Reads ``robotPath`` from the constant.
* **Articulation Controller** — the standard Isaac Sim node that writes
  position / velocity / effort commands onto the articulation.  Reads
  ``robotPath`` from the same constant and ``positionCommand`` from the
  Construct Array's output.

The wiring is:

* Both the Articulation Actuators and the Articulation Controller have
  their ``execIn`` connected to On Playback Tick's ``tick``.
* The Robot Path constant feeds ``robotPath`` on both actuator-side nodes.
* Each Pose constant feeds the corresponding ``inputN`` slot on the
  Construct Array; the Construct Array's ``array`` output feeds
  ``positionCommand`` on the Articulation Controller.

.. note::

   The Articulation Actuators node only needs to fire **once** to bootstrap
   itself: on its first ``execIn`` pulse it lazily constructs the underlying
   :class:`~isaacsim.core.experimental.actuators.ArticulationActuators`,
   which then registers its own pre-physics callback and runs the actuators
   on every physics step independent of further graph ticks.  We still feed
   it from On Playback Tick in this example because subsequent ticks are
   what re-apply the ``feedforwardCommand`` input (when wired).

   The Articulation Controller, by contrast, does need to tick every frame
   so its ``positionCommand`` is re-asserted onto the articulation.

Authoring the graph
==================================================

In a typical workflow you author this graph by hand in the Action Graph
editor — drop in the nodes shown above, fill in the constant string with
the articulation root path and the per-DOF Constant Doubles with your
target joint positions, and wire them up as described.  See
:ref:`isaac_sim_app_tutorial_gui_omnigraph` for a walkthrough of the
editor.

To reproduce the screenshot above without authoring the graph by hand, a
runnable companion script is provided at
``standalone_examples/api/isaacsim.core.experimental.actuators/newton_actuators_omnigraph_example.py``.
It opens the Franka asset, authors actuator prims onto it, builds the graph
programmatically, plays the simulation, and keeps the kit window open so
you can open the Action Graph editor and inspect or modify the graph live:

.. code-block:: bash

   ./python.sh standalone_examples/api/isaacsim.core.experimental.actuators/newton_actuators_omnigraph_example.py

Once the script is running you can edit the per-DOF Constant Double values
directly in the graph editor and watch the robot follow the new targets in
real time:

.. figure:: images/isim_6.0_full_tut_gui_newton_actuators_omnigraph_drive.webp
   :align: center
   :alt: Editing per-DOF Constant Double values in the Action Graph editor and seeing the Franka follow the new joint-position targets.

   Editing the per-DOF target values in the Action Graph editor drives the
   Franka through the Articulation Controller and the authored Newton
   actuators.

Adding a feedforward source
==================================================

Feedforward effort is added on top of the controller output by every actuator
each tick.  It is the right input for gravity-compensation torques, learned
residual policies, or any open-loop torque component.

Wire a per-DOF ``float[]`` array (typically a **Constant Float Array** node,
or any upstream node that produces a ``float[]``) into the
**feedforwardCommand** input of the Articulation Actuators node.  If the
array is shorter than the full DOF count, also wire a per-DOF ``int[]``
index array into **dofIndices** so the actuator knows which DOFs the
feedforward applies to.

Manual stepping (advanced)
==================================================

Setting ``autoStepPrePhysics`` to **false** disables the pre-physics
callback that the underlying ``ArticulationActuators`` registers, and the
node steps the actuators itself on each ``execIn`` pulse using ``stepDt``.

This is useful when you need:

* Deterministic ordering between feedforward writes and the actuator step
  inside the same graph evaluation tick, or
* Stepping at a rate other than the physics rate (e.g. for analysis).

Be aware that the timeline still drives physics independently — manually stepping the 
actuators faster than physics is usually not useful. In nearly all cases the default 
(auto-stepping) is what you want.

Limitations
==================================================

* **USD discovery only.** The node has no Python equivalent of
  :meth:`~isaacsim.core.experimental.actuators.ArticulationActuators.from_actuators`.
  If your actuator pipeline is built in Python, drive it with a Python
  script (see :ref:`isaac_sim_newton_actuators_python`) or wrap it in a
  custom OmniGraph Python node.