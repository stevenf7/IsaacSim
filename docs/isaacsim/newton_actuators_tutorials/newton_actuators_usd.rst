..
   Copyright (c) 2022-2026, NVIDIA CORPORATION. All rights reserved.
   NVIDIA CORPORATION and its licensors retain all intellectual property
   and proprietary rights in and to this software, related documentation
   and any modifications thereto. Any use, reproduction, disclosure or
   distribution of this software and related documentation without an express
   license agreement from NVIDIA CORPORATION is strictly prohibited.


.. _isaac_sim_newton_actuators_usd:

==================================================
Author and Parse Actuators from USD
==================================================

.. note::

   The ``isaacsim.core.experimental.actuators`` extension is **experimental**.
   The Newton USD schema names (``NewtonActuator``, ``NewtonPDControlAPI``,
   …) are part of the shared Newton schema and are also subject to change.

This tutorial shows how to bake an actuator configuration directly into a
robot's USD file, so that the actuator pipeline is reconstructed automatically
every time the asset is loaded — by either |isaac-sim_short| or
Isaac Lab.

Authoring actuators on the asset is the recommended path when:

* You want the same robot file to behave identically across applications (|isaac-sim_short| and Isaac Lab).
* You are bundling a robot package for distribution: hand-tuned gains,
  effort limits, and motor curves all travel with the file.

By the end of this tutorial you'll know how to:

* Author ``NewtonActuator`` prims with the
  :func:`~isaacsim.core.experimental.actuators.add_actuator` helper.
* Inspect the resulting USDA so you can hand-edit it later.
* Save the stage and re-open it so the actuators are discovered automatically.

All code examples come from the complete, runnable file ``newton_actuators_usd_example.py``:

.. code-block:: bash

    # Newton Actuators USD example
    ./python.sh standalone_examples/api/isaacsim.core.experimental.actuators/newton_actuators_usd_example.py

**Prerequisites**

* Read :ref:`isaac_sim_newton_actuators_tutorials` for the actuator pipeline
  overview.
* Familiarity with USD references and API schemas.

The Newton actuator schema
==================================================

A Newton actuator is a USD prim of type ``NewtonActuator``, placed under the
articulation root inside an ``Actuators`` scope.  It carries:

* A ``newton:targets`` relationship pointing at the joint it drives
* One **controller** API schema (e.g. ``NewtonPDControlAPI``,
  ``NewtonPIDControlAPI``, ``NewtonNeuralControlAPI``) and the corresponding
  ``newton:*`` attributes.
* Zero or more **clamping** API schemas (``NewtonMaxEffortClampingAPI``,
  ``NewtonDCMotorClampingAPI``, ``NewtonPositionBasedClampingAPI``).
* An optional **delay** API schema (``NewtonActuatorDelayAPI``).

A minimal authored prim looks like:

.. code-block:: usda

   def NewtonActuator "panda_joint1_actuator" (
       prepend apiSchemas = ["NewtonPDControlAPI", "NewtonMaxEffortClampingAPI"]
   )
   {
       rel newton:targets = </World/Franka/.../panda_joint1>
       float newton:kp = 400.0
       float newton:kd = 40.0
       float newton:maxEffort = 87.0
   }

Any application that understands the Newton USD schema can parse the same
prim and recover the same actuator pipeline.  This is what lets the same
asset move between |isaac-sim_short| and Isaac Lab.

Authoring with ``add_actuator``
==================================================

Hand-writing USDA is fine for one-off tweaks, but for setup-time configuration
the easiest path is the
:func:`~isaacsim.core.experimental.actuators.add_actuator` helper.  It takes
Python config dataclasses, validates them, defines the ``NewtonActuator``
prim under ``{articulation_root}/Actuators/{name}``, applies the appropriate
API schemas, and authors the corresponding ``newton:*`` attributes — all in
one call.

.. literalinclude:: ../snippets/newton_actuators/newton_actuators_usd_example.py
   :start-after: <start-author-actuators-snippet>
   :end-before: <end-author-actuators-snippet>
   :language: python

The ``target_names`` argument matches against the **leaf segment** of joint
USD paths, so passing ``"panda_joint1"`` resolves to whatever full path that
joint has under the articulation root.  The helper validates that each name
matches exactly one joint under the articulation; if a name is ambiguous
or absent, it raises ``ValueError``.

Each clamping type may appear at most once per actuator.  Multiple clamps can
be composed together:

.. code-block:: python

   clamping=[
       MaxEffortClampingConfig(max_effort=87.0),
       DCMotorClampingConfig(saturation_effort=120.0, velocity_limit=10.0, max_motor_effort=87.0),
   ]

Inspecting the authored prims
--------------------------------------------------

The standalone script flattens the ``Actuators`` subtree to USDA and prints
it to the terminal right after authoring, so you can verify exactly what
was written before exporting.  The output should look like:

.. code-block:: text

    === Authored Newton actuator prims (USDA) ===
    #usda 1.0

    over "panda"
    {
        def "Actuators"
        {
            def NewtonActuator "panda_joint1_actuator" (
                prepend apiSchemas = ["NewtonPDControlAPI", "NewtonMaxEffortClampingAPI"]
            )
            {
                float newton:constEffort = 0
                float newton:kd = 8
                float newton:kp = 67
                float newton:maxEffort = 1000
                rel newton:targets = </panda/panda_link0/panda_joint1>
            }

            def NewtonActuator "panda_joint2_actuator" (
                prepend apiSchemas = ["NewtonPDControlAPI", "NewtonMaxEffortClampingAPI"]
            )
            {
                float newton:constEffort = 0
                float newton:kd = 8
                float newton:kp = 66
                float newton:maxEffort = 1000
                rel newton:targets = </panda/panda_link1/panda_joint2>
            }

            def NewtonActuator "panda_joint3_actuator" (
                prepend apiSchemas = ["NewtonPDControlAPI", "NewtonMaxEffortClampingAPI"]
            )
            {
                float newton:constEffort = 0
                float newton:kd = 8
                float newton:kp = 65
                float newton:maxEffort = 1000
                rel newton:targets = </panda/panda_link2/panda_joint3>
            }

            def NewtonActuator "panda_joint4_actuator" (
                prepend apiSchemas = ["NewtonPDControlAPI", "NewtonMaxEffortClampingAPI"]
            )
            {
                float newton:constEffort = 0
                float newton:kd = 8
                float newton:kp = 64
                float newton:maxEffort = 1000
                rel newton:targets = </panda/panda_link3/panda_joint4>
            }

            def NewtonActuator "panda_joint5_actuator" (
                prepend apiSchemas = ["NewtonPDControlAPI", "NewtonMaxEffortClampingAPI"]
            )
            {
                float newton:constEffort = 0
                float newton:kd = 8
                float newton:kp = 63
                float newton:maxEffort = 1000
                rel newton:targets = </panda/panda_link4/panda_joint5>
            }

            def NewtonActuator "panda_joint6_actuator" (
                prepend apiSchemas = ["NewtonPDControlAPI", "NewtonMaxEffortClampingAPI"]
            )
            {
                float newton:constEffort = 0
                float newton:kd = 8
                float newton:kp = 62
                float newton:maxEffort = 1000
                rel newton:targets = </panda/panda_link5/panda_joint6>
            }

            def NewtonActuator "panda_joint7_actuator" (
                prepend apiSchemas = ["NewtonPDControlAPI", "NewtonMaxEffortClampingAPI"]
            )
            {
                float newton:constEffort = 0
                float newton:kd = 8
                float newton:kp = 61
                float newton:maxEffort = 1000
                rel newton:targets = </panda/panda_link6/panda_joint7>
            }
        }
    }

The parent ``"panda"`` prim shows up as an ``over`` because the printed
layer only contains the authored ``Actuators`` subtree — the rest of the
Franka asset lives in the original USD file and is composed in at load
time.  Each ``NewtonActuator`` carries the controller and clamping API
schemas, the corresponding ``newton:*`` attributes, and a
``newton:targets`` relationship pointing at the joint it drives.

Saving the stage
==================================================

Once authored, the actuator prims are part of the stage and persist exactly
like any other USD content.  Flatten the stage to a single file so it can be
distributed:

.. literalinclude:: ../snippets/newton_actuators/newton_actuators_usd_example.py
   :start-after: <start-export-stage-snippet>
   :end-before: <end-export-stage-snippet>
   :language: python

Open the exported file in any USD-aware text editor or USD viewer to confirm
the ``Actuators`` scope, the ``newton:*`` attributes, and the ``newton:targets``
relationships are intact.

Discovering authored actuators
==================================================

When you construct
:class:`~isaacsim.core.experimental.actuators.ArticulationActuators` with
just an articulation root, it walks the USD subtree, finds every
``NewtonActuator`` prim, parses its applied API schemas, and rebuilds the
actuator pipeline:

.. literalinclude:: ../snippets/newton_actuators/newton_actuators_usd_example.py
   :start-after: <start-discover-from-usd-snippet>
   :end-before: <end-discover-from-usd-snippet>
   :language: python

No further wiring is needed — the pre-physics callback is registered
automatically and the actuators take over the moment the timeline starts.

Round-trip: author, save, re-open, discover
==================================================

The most useful pattern is the full round-trip: author once on a base asset,
flatten to disk, then load the saved file in any application that understands
the Newton schema:

.. literalinclude:: ../snippets/newton_actuators/newton_actuators_usd_example.py
   :start-after: <start-reopen-and-discover-snippet>
   :end-before: <end-reopen-and-discover-snippet>
   :language: python

The same exported file can be loaded in Isaac Lab, where its
runtime integration layer parses the same ``NewtonActuator`` prims and
recovers the same effective control law.

Hand-editing authored actuators
==================================================

After authoring, the Franka actuators on the example asset look like this in
the saved USDA:

.. code-block:: usda

   def Scope "Actuators"
   {
       def NewtonActuator "panda_joint1_actuator" (
           prepend apiSchemas = ["NewtonPDControlAPI", "NewtonMaxEffortClampingAPI"]
       )
       {
           rel newton:targets = </World/Franka/panda_link0/panda_joint1>
           float newton:kp = 400.0
           float newton:kd = 40.0
           float newton:maxEffort = 87.0
       }

       # ... one prim per joint ...
   }

Tweaks like adjusting a gain or raising an effort cap can be made by editing
attributes directly.

Limitations
==================================================

* **Custom controller subclasses.** Subclasses of ``newton.actuators.Controller``
  defined in user code (see :ref:`isaac_sim_newton_actuators_python`) do not
  have a corresponding USD schema and cannot be authored or discovered this
  way.  Use the Python construction path for those.
* **Homogeneous instances.** When the articulation prim is referenced
  multiple times (a robot fleet), all instances share the same authored
  actuator parameters.
* **No GUI authoring.** There is not yet an Isaac Sim GUI panel for adding ``NewtonActuator``
  prims; use the Python helper or hand-edit USDA.

What's next
==================================================

* :ref:`isaac_sim_newton_actuators_omnigraph` — drive a USD-authored
  actuated robot from OmniGraph using the
  ``Articulation Actuators`` node.
