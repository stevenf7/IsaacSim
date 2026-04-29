..
   Copyright (c) 2022-2026, NVIDIA CORPORATION. All rights reserved.
   NVIDIA CORPORATION and its licensors retain all intellectual property
   and proprietary rights in and to this software, related documentation
   and any modifications thereto. Any use, reproduction, disclosure or
   distribution of this software and related documentation without an express
   license agreement from NVIDIA CORPORATION is strictly prohibited.


.. _isaac_sim_app_example_event_reactive_actors:

==================================================
Example: Reacting to Events with Actor Triggers
==================================================

This example shows how Event Generation (``isaacsim.replicator.incident``) and Actor Synthetic Data Generation (SDG) (``isaacsim.replicator.agent``) can be wired together end-to-end **without writing a single line of Python**. You edit two YAML config files and drive the two extensions from their Omniverse windows.

At runtime, Event Generation fires a fire event in the warehouse, which dispatches a `carb event <https://docs.omniverse.nvidia.com/dev-guide/latest/programmer_ref/events.html>`_; Actor SDG characters subscribe to that carb event through ``event_trigger`` and swap their behavior: pause briefly, walk to a safe point, stand still, and finally resume their wander routine.

.. image:: /images/isim_6.0_full_ex_external_event_reactive_actors.webp
   :width: 900
   :align: center
   :alt: Two warehouse workers reacting to a fire event in the Simple Warehouse stage.

|

Prerequisites
=============

- Both extensions are enabled. Refer to :ref:`actor_sim_enable_extensions` for the Actor SDG side; the Event Generation extension is enabled automatically by the same Action and Event Data Generation app launch.
- Familiarity with the standalone tutorials is helpful, but not required: 

  - :ref:`isaac_sim_app_tutorial_replicator_character`
  - :ref:`isaac_sim_app_tutorial_replicator_incident`

How the Two Extensions Connect
==============================

The two extensions have no direct API coupling. They connect through the **carb event bus** that every extension in a Kit app instance shares. Event Generation dispatches a named carb event when an incident fires, and Actor SDG's ``event_trigger`` listens for that same name. A matching string is the only contract between them.

The dispatched event name is always:

.. code-block:: text

    isaacsim.replicator.incident.core.events/<event_name>

Replace ``<event_name>`` with whatever you put under ``FireEvent.name`` (or ``SpillEvent.name``) in the Event Generation YAML. The extension interpolates the event name into the dispatched string exactly as written. Use underscores instead of spaces; a space in ``name`` causes the actor's ``event_trigger`` lookup to silently fail.

Only ``FireEvent`` and ``SpillEvent`` dispatch carb events. ``ToppleEvent`` currently signals only within Event Generation and cannot drive an actor trigger. For the complete list of trigger types incidents support (including chaining one incident from another), refer to :ref:`iri_trigger_section`.

Step 1 - Author the Event Generation YAML
==========================================

Save the following as ``incident_config.yaml`` anywhere on disk:

.. code-block:: yaml

    isaacsim.replicator.incident:
      version: 0.1.0
      global:
        report_dir: ~/EventsResult
        seed: 42
      event:
        event_list:
          - FireEvent:
              name: warehouse_fire
              flammable_item:
                item: $random_flammable_item$
                flammable_nearby_radius: 1.5
              trigger:
                type: time
                time: 4

The ``time: 4`` is seconds counted from when the timeline starts playing. The extension resolves ``$random_flammable_item$`` at setup time by scanning the stage for prims tagged ``IsaacSim_Replicator_Incident_Attr:FlammableItem``.

Step 2 - Author the Actor SDG YAML
===================================

Save as ``agent_config.yaml``. The trigger's ``event:`` string must match what Step 1 dispatches exactly.

.. code-block:: yaml

    isaacsim.replicator.agent:
      version: 1.5.0
      seed: 42
      simulation_duration: 25.0
      environment:
        base_stage_asset_path: Isaac/Environments/Simple_Warehouse/full_warehouse.usd
      sensor:
        groups:
          sensor_group_00:
            num: 1
            aim_at_targets: {}
      character:
        groups:
          warehouse_workers:
            num: 2
            routines:
              - wander:
                  weight: 1.0
                  repeat: 1
                  walk:
                    speed_range: [1.0, 1.0]
                    distance_range: [5.0, 10.0]
                    navigation_areas: []
                  idle:
                    - animation: idle
                      weight: 1.0
                      time_range: [3.0, 5.0]
            triggers:
              - event_trigger:
                  event: isaacsim.replicator.incident.core.events/warehouse_fire
                  priority: 10
                  behavior:
                    - stop:
                        weight: 1.0
                        repeat: 1
                        time_range: [1.0, 2.0]
                    - patrol:
                        weight: 1.0
                        repeat: 1
                        speed_range: [3.0, 4.0]
                        path_points:
                          - [0.0, 0.0, 0.0]
                    - stop:
                        weight: 1.0
                        repeat: 1
                        time_range: [10.0, 15.0]

A few notes on this config:

- The ``sensor`` block creates a single placeholder camera. The trigger does not require it, but the Configuration Editor populates it by default; leaving it in place keeps the YAML round-trippable through the editor UI.
- ``weight``, ``repeat``, and ``navigation_areas: []`` are shown explicitly even though each is a default. This example surfaces them so that you can see what the Configuration Editor writes out and modify the values in place.
- The trigger's ``behavior`` list runs **in order**: a brief 1-2 second stop, then a patrol to ``(0, 0, 0)``, then a 10-15 second stop. After the list completes, the actor resumes its routine.

.. important::

   Both extensions operate on whichever stage Actor SDG loads, because they share a single Kit stage. If you point Actor SDG at an untagged warehouse, Event Generation logs ``'$random_flammable_item$' is not a tagged prim`` and no event fires. Either tag a prim manually (Step 5) or load a pre-tagged stage such as ``Isaac/Samples/Replicator/Incidents/full_warehouse_with_incident_tags.usd``.

Step 3 - Launch the App
=======================

From the Isaac Sim install directory:

.. code-block:: bash

    ./isaac-sim.action_and_event_data_generation.sh

This opens ``isaacsim.exp.action_and_event_data_generation.full.kit``, which enables both Actor SDG and Event Generation UIs. Two menu entries appear under **Tools > Action and Event Data Generation**:

- **Actor SDG** -- Actor SDG's config window.
- **Event Config File** -- Event Generation's config window.

Open both from the **Tools** menu and they dock side by side.

Step 4 - Set Up Actor SDG
=========================

In the **Actor SDG** window:

1. Click the **Select A Configuration File** field (or paste the path to ``agent_config.yaml``).
2. Once the path is set, click **Set Up Simulation**.

Internally this opens the warehouse stage, instantiates two ``warehouse_workers`` characters with their wander routine, and attaches a carb-event listener to each character already subscribed to ``isaacsim.replicator.incident.core.events/warehouse_fire``. The subscription is live before you touch anything else.

Do **not** start the timeline yet. Avoid both **Start Data Generation** and the play button, because Event Generation's time countdown begins as soon as the timeline plays. Complete Step 5 first.

Step 5 - Set Up Event Generation
================================

In the **Event Config File** window:

1. Use the **Config File Path** picker to select ``incident_config.yaml``.
2. In the **Stage** window, select any box prim on a shelf (for example, ``/Root/Box_21069`` from the Simple Warehouse stage).
3. Right-click in the viewport. Expand the **Incident Scene Tags** submenu.
4. Choose **Apply Flammable Item Tag** > **Box**.
5. Click **Set Up Incident**.

If you adapt this example to use ``SpillEvent`` or ``ToppleEvent``, apply the corresponding **Leakable Item Tag** or **Loose Item Tag** in this same step before clicking **Set Up Incident**. The selected prim's property panel exposes checkboxes for the same actions.

Internally, Event Generation reads the YAML, waits for navmesh baking, picks the tagged prim as the flammable target, and arms a time trigger that will fire at ``t = 4 s`` after the timeline plays. Nothing has fired yet.

The Global section's Seed field should populate to ``42``, and the event list should show ``warehouse_fire``.

Step 6 - Play and Watch
=======================

You have two ways to start the simulation:

- **Timeline play button** -- the standard Omniverse play button at the top of the viewport. It plays the timeline only and writes no data.
- **Start Data Generation** (**Actor SDG** window) -- plays the timeline *and* runs Replicator writers on top to capture synthetic data. With no ``replicator`` section in this example's YAML, the writers produce no output, but ``simulation_duration: 25.0`` still stops playback automatically.

Either way, verify that you receive:

.. list-table::
   :widths: 25 75
   :header-rows: 1

   * - Time (s)
     - What happens
   * - 0
     - Two workers begin wandering.
   * - ~4
     - Event Generation fires ``FireEvent(warehouse_fire)``. Flow flame and smoke appear on the tagged prim. A carb event is dispatched.
   * - ~4 (next tick)
     - Both workers cancel their wander routines and pause for 1-2 seconds (the first ``stop`` in the trigger).
   * - After the pause
     - Workers walk briskly (3-4 m/s) toward ``(0, 0, 0)``. Travel time depends on each worker's starting position.
   * - On arrival
     - Each worker stands still at the safe point for 10-15 seconds.
   * - Trigger complete
     - Each worker samples a fresh wander routine and resumes.
   * - 25
     - Simulation ends.

