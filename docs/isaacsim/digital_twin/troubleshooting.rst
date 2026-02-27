..
   Copyright (c) 2022-2026, NVIDIA CORPORATION. All rights reserved.
   NVIDIA CORPORATION and its licensors retain all intellectual property
   and proprietary rights in and to this software, related documentation
   and any modifications thereto. Any use, reproduction, disclosure or
   distribution of this software and related documentation without an express
   license agreement from NVIDIA CORPORATION is strictly prohibited.

.. _isaac_sim_digital_twin_troubleshooting:


=================================
Digital Twin Troubleshooting
=================================

This page consolidates troubleshooting information for Digital Twin components in Isaac Sim.

Warehouse Logistics Issues
==========================

Warehouse Creator Issues
^^^^^^^^^^^^^^^^^^^^^^^^^

* If warehouse components don't appear after generation, check for errors in the console logs
* For layout issues, ensure the grid dimensions and spacing are properly configured
* If textures appear incorrect, verify your material settings and check GPU compatibility

Conveyor Belt Issues
^^^^^^^^^^^^^^^^^^^^^^^^^

* For non-functioning conveyors, ensure the physics settings are correctly applied
* If objects fall through conveyors, adjust collision settings and physics parameters
* Animation speed issues can be resolved by checking the conveyor speed settings

Cortex Issues
=============

Decider Network Issues
^^^^^^^^^^^^^^^^^^^^^^^^^

* If decision networks fail to initialize, check that all required extensions are enabled
* For unexpected behavior, review your network configurations and connections
* Debug flows by enabling verbose logging and tracing through decisions step by step

Asset Loading Issues
^^^^^^^^^^^^^^^^^^^^^^^^^

* Missing assets can be resolved by checking file paths and ensuring assets are available
* For slow loading of complex assets, consider using simpler versions for testing
* USD file compatibility issues may require updating to the latest USD schema

Mapping Issues
==========================

Occupancy Map Issues
^^^^^^^^^^^^^^^^^^^^^^^^^

* If occupancy maps fail to generate, ensure the scene has proper collision geometry
* For inaccurate maps, adjust the resolution and sensor parameters
* Missing areas in the map may indicate occlusion issues or raycast failures 