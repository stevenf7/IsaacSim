..
   Copyright (c) 2026, NVIDIA CORPORATION. All rights reserved.
   NVIDIA CORPORATION and its licensors retain all intellectual property
   and proprietary rights in and to this software, related documentation
   and any modifications thereto. Any use, reproduction, disclosure or
   distribution of this software and related documentation without an express
   license agreement from NVIDIA CORPORATION is strictly prohibited.

.. _isaac_ros2_omnigraph_migration:

====================================
ROS 2 OmniGraph node migration guide
====================================

This guide covers migrating Action Graphs from Isaac Sim 5.1 and earlier to Isaac Sim 6.0
and later. Two ROS 2 OmniGraph publisher nodes have been updated to accept pre-computed data
from dedicated source nodes rather than resolving USD prims internally. Direct prim
inputs on these nodes are deprecated and will be removed in a future release.

The following nodes require migration:

- :ref:`ROS2 Publish Transform Tree <isaac_ros2_migration_publish_tf>`
- :ref:`ROS2 Publish Joint State <isaac_ros2_migration_publish_joint_state>`


.. _isaac_ros2_migration_publish_tf:

Migrating ROS2 Publish Transform Tree
======================================

1. Add an **Isaac Compute Transform Tree** node (``isaacsim.core.nodes``) to your Action Graph
   and set its **targetPrims** input to the prims you want to publish. For an articulation root,
   the full link tree is expanded automatically. Set **parentPrim** if you need transforms
   relative to a specific frame rather than the world.

2. Connect the outputs of **Isaac Compute Transform Tree** to **ROS2 Publish Transform Tree**
   as follows:

   .. list-table::
      :header-rows: 1
      :widths: 50 50

      * - Isaac Compute Transform Tree output
        - ROS2 Publish Transform Tree input
      * - ``execOut``
        - ``execIn``
      * - ``parentFrames``
        - ``parentFrames``
      * - ``childFrames``
        - ``childFrames``
      * - ``translations``
        - ``translations``
      * - ``orientations``
        - ``orientations``

   Any inputs on **ROS2 Publish Transform Tree** not listed in the table above can remain connected to
   their existing upstream nodes.



.. _isaac_ros2_migration_publish_joint_state:

Migrating ROS2 Publish Joint State
====================================

1. Add an **Isaac Read Joint State** node (``isaacsim.sensors.physics.nodes``) to your Action
   Graph and set its **prim** input to the articulation root prim.

2. Connect the outputs of **Isaac Read Joint State** to **ROS2 Publish Joint State** as follows:

   .. list-table::
      :header-rows: 1
      :widths: 50 50

      * - Isaac Read Joint State output
        - ROS2 Publish Joint State input
      * - ``execOut``
        - ``execIn``
      * - ``jointNames``
        - ``jointNames``
      * - ``jointPositions``
        - ``jointPositions``
      * - ``jointVelocities``
        - ``jointVelocities``
      * - ``jointEfforts``
        - ``jointEfforts``
      * - ``jointDofTypes``
        - ``jointDofTypes``
      * - ``stageMetersPerUnit``
        - ``stageMetersPerUnit``
      * - ``sensorTime``
        - ``sensorTime``

   Any inputs on **ROS2 Publish Joint State** not listed in the table above can remain connected to
   their existing upstream nodes.

