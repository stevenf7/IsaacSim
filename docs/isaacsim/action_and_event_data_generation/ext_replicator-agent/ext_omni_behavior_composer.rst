..
   Copyright (c) 2022-2026, NVIDIA CORPORATION. All rights reserved.
   NVIDIA CORPORATION and its licensors retain all intellectual property
   and proprietary rights in and to this software, related documentation
   and any modifications thereto. Any use, reproduction, disclosure or
   distribution of this software and related documentation without an express
   license agreement from NVIDIA CORPORATION is strictly prohibited.

:orphan:


====================================================================================
Behavior Composer
====================================================================================

The ``omni.behavior.composer`` extension implements the classic `behavior tree system <https://en.wikipedia.org/wiki/Behavior_tree_(artificial_intelligence,_robotics_and_control)>`__ for Omniverse Kit applications. It comes with a suite of tools and APIs to author entity behaviors in Omniverse Kit with OpenUSD alongside a standalone C++ core runtime API to power various simulation engines.

Why use behavior trees to author behaviors?
---------------------------------------------
- Behavior trees allow one to define complex behavior using small, reusable nodes composed into readable control logic.
- High-level behavior logic lives as data: engineers build node implementations, while scenario designers assemble and tune behaviors directly as a part of the scenario description.


Architecture Overview
---------------------

- **Behavior Composer** (``omni.behavior.composer``)

  - Works directly with your USD stage: trees, blackboards, and node libraries are authored as prims.
  - Provides a user-friendly abstraction for creating, editing, and running behavior trees in a scene.
  - Integrates with the visual editor so non-programmers can work with behaviors.
  - This is the layer most Kit application-level code works with.


- **User Interface** (``omni.behavior.composer.ui``)

  - Visual tree editor for authoring and debugging trees.
  - Views into blackboards, node libraries, and runtime state (node status, tick counts, etc.).


- **Low-level Runtime API** (``omni.behavior_tree``)

  - Can be used standalone in pure Python or C++ contexts where USD or Kit runtimes are not needed.
  - Prefer this layer when you need maximum control, or want to build custom runtimes, tools, or tests around behavior trees.
