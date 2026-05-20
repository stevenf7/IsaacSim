..
   Copyright (c) 2022-2026, NVIDIA CORPORATION. All rights reserved.
   NVIDIA CORPORATION and its licensors retain all intellectual property
   and proprietary rights in and to this software, related documentation
   and any modifications thereto. Any use, reproduction, disclosure or
   distribution of this software and related documentation without an express
   license agreement from NVIDIA CORPORATION is strictly prohibited.


.. _ira_sample_configs:

==============
Sample Configs
==============

The ``isaacsim.replicator.agent.core`` extension ships with a small set of YAML
configurations under ``[ext-path]/data/sample_configs/``. They demonstrate the
recommended ways to configure the Isaac replicator agent (IRA), from the smallest valid config to a full
data-generation pipeline.

Layout
======

The directory is organized as follows:

.. code-block:: text

   sample_configs/
     minimal.yaml         # smallest valid config (env only)
     full_pipeline.yaml   # end-to-end demo: routines + sensors + writers
     behavior_tree/       # behavior-tree samples (experimental)
       wander.yaml
       patrol_and_wander.yaml
       instance_overrides.yaml

Behavior-tree samples live under ``behavior_tree/`` because behavior-tree character
support is currently experimental (refer to :ref:`Behavior Tree Character
Group (Experimental) <ira_bt_character_group>`). The two top-level samples
use the stable routine-trigger character API and are the recommended
starting point.

Standard Samples
================

Top-level samples. They use the stable routine-trigger character API
(refer to :ref:`Configuration File <ira_configuration_file>`).

.. list-table::
   :header-rows: 1
   :widths: 22 50 28

   * - File
     - Expected behavior
     - Demonstrates
   * - ``minimal.yaml``
     - Opens the warehouse stage. No actors, sensors, or data generation --
       a sanity check that IRA is enabled and the asset server is reachable.
     - Smallest valid IRA config. Loaded by the IRA UI on launch.
   * - ``full_pipeline.yaml``
     - 10 workers wander the warehouse for 60 seconds while six randomly placed
       ceiling cameras capture per-frame RGB, depth, segmentation, bounding
       boxes, and cosmos video annotations to the output folder.
     - End-to-end pipeline: routine-based character behavior, RTX sensor
       placement (``aim_at_targets``), and ``IRABasicWriter``.

Behavior-Tree Samples (Experimental)
====================================

Samples under ``sample_configs/behavior_tree/`` that drive characters with
behavior trees instead of routines. The trees themselves live in the sibling
``sample_behavior_tree/`` folder of the extension.

.. list-table::
   :header-rows: 1
   :widths: 22 32 28 18

   * - File
     - Expected behavior
     - Demonstrates
     - Behavior Tree asset
   * - ``behavior_tree/wander.yaml``
     - Two warehouse workers wander randomly through the warehouse.
     - Single behavior-tree character group.
     - ``sample_behavior_tree/wander.json``
   * - ``behavior_tree/patrol_and_wander.yaml``
     - Two agents follow a fixed patrol route while three others wander around
       them.
     - Two BT character groups (patrol + wander) coexisting in one config.
     - ``sample_behavior_tree/patrol.json`` + ``wander.json``
   * - ``behavior_tree/instance_overrides.yaml``
     - Two warehouse workers each pick up a different cardboard box and carry
       it to a destination marker (``Destination_A``, ``Destination_B``).
     - Per-group ``overrides`` on a shared Behavior Tree. Each group binds
       ``SetBlackboard.slot``, ``PickupObject.target``, and
       ``PlaceObject.xform`` to its own values using ``instanceOverrides``.
     - ``sample_behavior_tree/box_mover_multiple.json``
