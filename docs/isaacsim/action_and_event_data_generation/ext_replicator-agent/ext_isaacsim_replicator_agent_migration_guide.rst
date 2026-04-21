..
   Copyright (c) 2022-2026, NVIDIA CORPORATION. All rights reserved.
   NVIDIA CORPORATION and its licensors retain all intellectual property
   and proprietary rights in and to this software, related documentation
   and any modifications thereto. Any use, reproduction, disclosure or
   distribution of this software and related documentation without an express
   license agreement from NVIDIA CORPORATION is strictly prohibited.


.. _ira_migration_guide_0x_to_1x:

======================================
IRA Migration Guide: 0.x.x to 1.x.x
======================================

This guide covers breaking changes and migration steps for users upgrading
from IRA 0.x.x (shipped with Isaac Sim 5.1 and before) to IRA 1.x.x
(Isaac Sim 6.0 and after).

IRA 1.0.0 is a **complete architectural overhaul**. The configuration schema,
Python API, dependency graph, and internal module layout have all changed.
Existing 0.x configs and code will **not** work without modification.


What Changed at a Glance
=========================

IRA 1.x retains all core capabilities of 0.x, including:

- environment loading
- character and robot spawning
- sensor placement
- synthetic data generation

While it redesigns how each of those areas is configured and executed. The table below
summarizes every major feature area, including, the version that supports it and what has
changed:

.. list-table::
   :header-rows: 1
   :widths: 30 12 12 46

   * - Feature
     - 0.x
     - 1.x
     - Notes
   * - **Environment / Scene Loading**
     - Yes
     - Yes
     - ``scene.asset_path`` renamed to ``environment.base_stage_asset_path`` (now required). Path can be relative to Isaac Sim assets, a URL, or an absolute path.
   * - **Environment Prop Sublayers**
     - --
     - New
     - ``prop_asset_paths`` lets you layer additional USD assets into the base stage.
   * - **Human Character Spawning**
     - Yes
     - Yes
     - Flat ``character`` section replaced by ``character.groups`` with named groups.
   * - **Robot Spawning (Nova Carter, iw.hub)**
     - Yes
     - Yes
     - ``nova_carter_num`` and ``iw_hub_num`` replaced by named groups with ``config_file_path`` pointing to IAR configs.
   * - **Character Behavior Control**
     - Yes
     - Yes
     - External ``.txt`` command files replaced by inline ``routines`` in YAML.
   * - **Robot Behavior Control**
     - Yes
     - Yes
     - Same change: external command files replaced by inline ``routines``.
   * - **Named Actor Groups**
     - --
     - New
     - Characters, robots, and sensors are organized into independently configured named groups.
   * - **Routine-trigger Behavior Loop**
     - --
     - New
     - Actors continuously pick weighted behaviors; triggers interrupt routines with priority-queued sequences. Replaces the old ``response``, ``event``, and ``incident`` model.
   * - **Behavior Types (wander, patrol, stop/halt)**
     - Yes
     - Yes
     - 0.x supported GoTo, Idle, and Patrol-like commands through text files. 1.x formalizes these as typed behaviors (``wander``, ``patrol``, ``stop``, ``halt``) with rich inline parameters.
   * - **Custom Behavior Trees**
     - --
     - Planned
     - ``custom_behavior`` type executes a Behavior Tree from a JSON file (re-enable planned for a future release).
   * - **Event and Time Triggers**
     - Yes
     - Yes
     - 0.x used ``response``, ``event``, and ``incident`` config sections. 1.x replaces them with first-class ``event_trigger`` and ``time_trigger`` types with priority queuing.
   * - **USD Schema Integration**
     - --
     - New
     - Actor config is persisted in USD API schemas (``IRACharacterAPI``, ``AnimRobotAPI``). Behaviors and triggers become individual USD prims for inspection and editing.
   * - **Per-actor Deterministic Seed**
     - --
     - New
     - Each actor's seed is derived from its name, group, and the global seed, enabling reproducible yet independent randomization.
   * - **Sensor and Camera Placement**
     - Yes
     - Yes
     - ``camera_num`` and ``camera_list`` replaced by named sensor groups with pluggable placement strategies.
   * - **Sensor Placement Strategies**
     - --
     - New
     - ``aim_at_targets`` and ``maximum_coverage`` algorithms; ``num: -1`` auto-calculates camera count for target coverage.
   * - **Camera Randomization Parameters**
     - Yes
     - Yes
     - Height, angle, focal length, and distance ranges moved from extension settings into the per-group YAML config.
   * - **Single Data Writer**
     - Yes
     - Yes
     - ``IRABasicWriter`` is available in both versions.
   * - **Multiple Concurrent Writers**
     - --
     - New
     - ``replicator.writers`` dict supports multiple writers running simultaneously.
   * - **Per-writer Timing Control**
     - --
     - New
     - ``start_frame`` and ``end_frame`` or ``start_time`` and ``end_time`` per writer.
   * - **Per-writer Sensor Selection**
     - --
     - New
     - ``sensor_prim_list`` selects specific cameras for each writer.
   * - **Additional Writers**
     - --
     - New
     - ``CosmosIRAWriter``, ``BasicWriter``, ``SceneGraphWriter``, ``CustomWriter``.
   * - **Semantic Labels on Actors**
     - --
     - New
     - ``semantic_labels`` field per character/robot group.
   * - **Character Colliders**
     - --
     - New
     - Optional cylinder or box collision shapes per character group.
   * - **Robot Onboard Camera Selection**
     - --
     - New
     - ``camera_prim_paths`` specifies which onboard robot cameras to use for data generation.
   * - **Pydantic Config Validation**
     - --
     - New
     - Config files are validated with Pydantic v2 models providing clear, actionable error messages.
   * - **Simulation Duration in Seconds**
     - --
     - New
     - ``simulation_duration`` specified in seconds. 0.x used ``simulation_length`` in frames (assuming 30 FPS).
   * - **UI Workflow**
     - Yes
     - Yes
     - Simplified from 5 steps to 3. The **Generate Random Commands** and **Save Commands** steps are removed.
   * - **Headless and Script-based Generation**
     - Yes
     - Yes
     - ``sdg_scheduler.py`` replaced by ``actor_sdg.py``.
   * - **Animation Backend**
     - Yes
     - Yes
     - ``omni.anim.people`` replaced by ``omni.anim.behavior.core``.
   * - Command Files (``.txt``) and Transition Maps (``.json``)
     - Yes
     - Removed
     - Replaced entirely by inline ``routines`` and ``triggers`` in YAML.
   * - ``response``, ``event``, and ``incident`` config Sections
     - Yes
     - Removed
     - Replaced by ``triggers`` on individual actor groups.
   * - ``filters`` Field on Characters
     - Yes
     - Removed
     - No longer supported.

Workflow and UI Changes
=======================

The end-to-end workflow for running IRA has changed significantly.

UI Workflow
-----------

The UI workflow has been simplified. The biggest change is the removal of the
**Generate Random Commands** step.

.. list-table::
   :header-rows: 1
   :widths: 5 40 40

   * - Step
     - 0.x Workflow
     - 1.x Workflow
   * - 1
     - Load config file
     - Load config file (default minimal config loads automatically)
   * - 2
     - Click **Set Up Simulation**
     - Click **Set Up Simulation**
   * - 3
     - Click **Generate Random Commands** for characters
     - *(removed -- behaviors are defined in config)*
   * - 4
     - Click **Save Commands** (disk icon)
     - *(removed -- no command files)*
   * - 5
     - Click **Start Data Generation**
     - Click **Start Data Generation**

In 0.x, command generation and saving were separate manual steps. In 1.x, all
actor behavior is pre-defined in the YAML config using ``routines`` and
``triggers``, so the setup-to-generation flow is two clicks.

Default Config File Location
-----------------------------

.. list-table::
   :header-rows: 1
   :widths: 10 60

   * - Version
     - Location
   * - 0.x
     - ``[ext-path]/config/default_config.yaml`` (auto-loaded on startup)
   * - 1.x
     - ``[ext-path]/data/sample_configs/`` (contains ``minimal.yaml`` and ``warehouse.yaml``)

In 1.x, a minimal config is loaded by default. For a full example with
characters, cameras, and writers, use ``warehouse.yaml``.

Headless or Script-Based Data Generation
-----------------------------------------

The script entry point has changed:

.. code-block:: bash

   # OLD (0.x)
   ./python.sh tools/actor_sdg/sdg_scheduler.py -c [config file path]

   # NEW (1.x)
   ./python.sh tools/actor_sdg/actor_sdg.py -c [config file path]

The ``sdg_scheduler.py`` script is replaced by ``actor_sdg.py``. The
``--save_usd`` flag from the old script is no longer documented as a script
argument.

Simulation Duration
--------------------

In 0.x, ``simulation_length`` was specified in **frames** (assuming 30 FPS).
Users had to mentally convert: 300 frames = 10 seconds.

In 1.x, ``simulation_duration`` is specified in **seconds** directly
(for example, ``60.0``). The simulation still runs at a fixed 30 FPS internally.

Configuration File Changes
==========================

The YAML configuration schema has been redesigned from scratch.

Version Field
-------------

The ``version`` field now tracks the extension version and must have a
``1.x.x`` major version.

.. code-block:: yaml

   # 0.x
   isaacsim.replicator.agent:
     version: 0.7.0

   # 1.x
   isaacsim.replicator.agent:
     version: 1.2.0

Top-Level Structure
--------------------

.. list-table::
   :header-rows: 1
   :widths: 25 25 50

   * - 0.x Field
     - 1.x Replacement
     - Notes
   * - ``global.seed``
     - ``seed``
     - Moved to root level. Now a 32-bit uint (0..4294967295). Auto-generated from system time if omitted.
   * - ``global.simulation_length``
     - ``simulation_duration``
     - Renamed. Was in **frames** (at 30 FPS), now in **seconds**. A value of ``1800`` frames = ``60.0`` seconds.
   * - ``scene.asset_path``
     - ``environment.base_stage_asset_path``
     - Section renamed from ``scene`` to ``environment``.
   * - ``sensor``
     - ``sensor``
     - Completely restructured (see below).
   * - ``character``
     - ``character``
     - Completely restructured (see below).
   * - ``robot``
     - ``robot``
     - Completely restructured (see below).
   * - ``replicator``
     - ``replicator``
     - Completely restructured (see below).
   * - ``response``
     - *(removed)*
     - Response section no longer exists. Use triggers instead.
   * - ``event``
     - *(removed)*
     - Event section no longer exists. Use triggers instead.

**Example of top-level migration:**

.. code-block:: yaml

   # OLD (0.x)
   isaacsim.replicator.agent:
     version: 0.7.0
     global:
       seed: 123456789
       simulation_length: 1800

   # NEW (1.x)
   isaacsim.replicator.agent:
     version: 1.2.0
     seed: 123456789           # optional, auto-generated if omitted
     simulation_duration: 60.0  # 1800 frames / 30 FPS = 60 seconds

Environment (was ``scene``)
-----------------------------

The ``scene`` section has been renamed to ``environment`` and expanded.

.. code-block:: yaml

   # OLD (0.x)
   # scene.asset_path was defined in the config, OR fell back to settings

   # NEW (1.x)
   environment:
     base_stage_asset_path: "Isaac/Environments/Simple_Warehouse/full_warehouse.usd"
     prop_asset_paths: []  # optional: additional USD assets loaded as sublayers

Key differences:

* ``base_stage_asset_path`` is **required** (no more fallback to extension settings).
* Supports relative paths that resolve against the Isaac Sim asset root, full URLs, and absolute filesystem paths.
* New ``prop_asset_paths`` field for layering additional assets into the stage.

Character Section
------------------

The character section now uses a **named groups** system with inline behavior
definitions (routines), replacing the old flat structure with external command
files.

.. code-block:: yaml

   # OLD (0.x)
   character:
     asset_path: ""                       # single path for all characters
     command_file: default_command.txt     # external text file for commands
     num: 8
     filters: []
     spawn_area: []
     navigation_area: []

   # NEW (1.x)
   character:
     root_prim_path: "/World/Characters"   # optional, defaults to /World/Characters
     groups:
       warehouse_workers:                   # named group
         num: 10
         asset_path: "Isaac/People/Characters/"
         spawn_areas: []                    # renamed from spawn_area
         semantic_labels: [["class", "character"]]
         motion_library_path: ""            # optional
         routines:                          # replaces command_file
           - wander:
               weight: 1.0
               repeat: 1
               walk:
                 speed_range: [0.8, 1.5]
                 distance_range: [5.0, 10.0]
                 navigation_areas: []       # renamed from navigation_area
               idle:
                 - animation: idle
                   weight: 1.0
                   time_range: [2.0, 5.0]
         triggers: []                       # new: event-driven behavior interrupts
         colliders: null                    # new: optional collision shapes

Key differences:

* **Named groups**: Characters are now organized into named groups under ``character.groups``, each with independent settings.
* **No more command files**: The ``command_file`` field and external ``.txt`` command files are gone. Behaviors are defined inline using ``routines``.
* **Routines replace commands**: Each routine entry is a behavior type (``wander``, ``patrol``, ``stop``, ``custom_behavior``) with inline parameters.
* ``filters`` field is removed.
* ``spawn_area`` renamed to ``spawn_areas``.
* ``navigation_area`` is now per-behavior under ``walk.navigation_areas``.
* New ``semantic_labels``, ``motion_library_path``, ``triggers``, and ``colliders`` fields.

Robot Section
--------------

Similar to characters, robots now use named groups with inline routines.

.. code-block:: yaml

   # OLD (0.x)
   robot:
     command_file: default_robot_command.txt
     nova_carter_num: 0
     iw_hub_num: 0
     write_data: false
     spawn_area: []
     navigation_area: []

   # NEW (1.x)
   robot:
     root_prim_path: "/World/Robots"
     groups:
       carters:
         num: 2
         config_file_path: "nova_carter.yaml"   # IAR robot config file
         spawn_areas: []
         agent_radius: null                      # optional NavMesh agent radius
         write_data: false
         camera_prim_paths: []                   # optional: specific cameras for data
         semantic_labels: [["class", "robot"]]
         routines:
           - wander:
               move:
                 distance_range: [10.0, 15.0]
                 navigation_areas: []
               idle:
                 time_range: [2.0, 5.0]
         triggers: []

Key differences:

* ``nova_carter_num`` / ``iw_hub_num`` are gone. Use named groups with ``num`` and ``config_file_path`` pointing to the appropriate IAR config.
* ``command_file`` replaced by inline ``routines`` (same as characters).
* New ``config_file_path`` field references the robot's Isaac Anim Robot (IAR) configuration.
* New ``camera_prim_paths`` for specifying which onboard cameras to use for data generation.
* ``spawn_area`` renamed to ``spawn_areas``.

Sensor Section
---------------

The sensor section has been redesigned to support named groups and pluggable
placement strategies.

.. code-block:: yaml

   # OLD (0.x)
   sensor:
     camera_num: 4
     # OR
     camera_list: ["/World/Camera1", "/World/Camera2"]

   # NEW (1.x)
   sensor:
     root_prim_path: "/World/Cameras"
     groups:
       ceiling_cameras:
         num: 6
         aim_at_targets:           # placement strategy
           height_range: [7.0, 10.0]
           look_down_angle_range: [30.0, 45.0]
           focal_length_range: [10.0, 15.0]
           distance_range: [5.0, 10.0]
       coverage_cameras:
         num: -1                   # auto-calculate for maximum coverage
         maximum_coverage:
           target_coverage_ratio: 0.8
           height_range: [2.0, 5.0]

Key differences:

* ``camera_num`` / ``camera_list`` replaced by named groups under ``sensor.groups``.
* Each group specifies a **placement strategy**: ``aim_at_targets`` or ``maximum_coverage``.
* Camera randomization parameters (height, angle, focal length, distance) that were in extension settings are now in the config YAML per sensor group.
* ``num: -1`` with ``maximum_coverage`` triggers automatic camera count calculation.

Replicator Section
-------------------

The replicator section now supports **multiple concurrent writers** with
per-writer timing control.

.. code-block:: yaml

   # OLD (0.x)
   replicator:
     writer: IRABasicWriter          # single writer, selected by name
     parameters:                     # flat parameter dict
       object_info_bounding_box_2d_tight: false
       object_info_bounding_box_2d_loose: false
       semantic_filter_predicate: "class:character|robot;id:*"
       rgb: true
       camera_params: true

   # NEW (1.x)
   replicator:
     hide_debug_visualization: true  # new: hides NavMesh/skeleton debug viz
     writers:
       IRABasicWriter:               # writer name is the dict key
         rgb: true
         camera_params: true
         object_info_bounding_box_2d_tight: true
         object_info_bounding_box_2d_loose: true
         semantic_filter_predicate: "class:character|robot;id:*"
         start_frame: 30             # new: per-writer frame control
         # OR use time-based:
         # start_time: 1.0
         # end_time: 50.0
         # sensor_prim_list: []      # new: optional per-writer sensor selection

Key differences:

* ``writer`` + ``parameters`` replaced by ``writers`` dict. The key is the writer name, and the value contains the parameters directly (no nesting under ``parameters``).
* **Multiple writers**: You can define multiple writers in a single config (for example, ``IRABasicWriter`` + ``CosmosIRAWriter``).
* Per-writer ``start_frame`` and ``end_frame`` or ``start_time`` and ``end_time`` for timing control.
* Per-writer ``sensor_prim_list`` for selecting specific cameras.
* Default ``start_frame`` is ``30`` (skips initial settling frames).
* New writers: ``CosmosIRAWriter``, ``BasicWriter``, ``SceneGraphWriter``, ``CustomWriter``.
* ``IRABasicWriter`` defaults changed: ``object_info_bounding_box_2d_tight``, ``object_info_bounding_box_2d_loose``, and ``object_info_bounding_box_3d`` now default to ``true``.

Behavior System Architecture Changes
======================================

The actor behavior system has been fundamentally redesigned.

Old System (0.x): Command Files + ``omni.anim.people``
--------------------------------------------------------

In 0.x, actor behavior was controlled by **external command files** (``.txt``):

* Characters were driven by ``omni.anim.people`` which read a text-based command file line-by-line.
* Robots were driven by ``isaacsim.anim.robot`` with a similar command file.
* A **Generate Random Commands** button in the UI created these command files based on randomization settings stored in the extension settings.
* Command transition maps (``.json``) controlled probabilistic transitions between commands.

New System (1.x): Routine-Trigger Loop + ``omni.anim.behavior``
-----------------------------------------------------------------

In 1.x, actor behavior uses a **routine-trigger loop** backed by
``omni.anim.behavior.core``:

1. **Routines**: A list of weighted behaviors defined in the YAML config. Actors repeatedly pick a behavior from their routine pool based on probability weights, using the actor's individual seed.
2. **Triggers**: Event-driven or time-driven interrupts. When activated, the actor pauses its routine and executes the trigger's behavior sequence. Higher-priority triggers can preempt running triggers.
3. **USD Schema**: After loading, each actor's configuration is embedded in **USD API schemas** (``IRACharacterAPI`` on SkelRoot for characters, ``AnimRobotAPI`` on robot root prims). Behaviors and triggers become individual USD prims referenced by the actor.

.. list-table::
   :header-rows: 1
   :widths: 25 35 40

   * - Aspect
     - 0.x
     - 1.x
   * - Behavior source
     - External ``.txt`` command file
     - Inline YAML ``routines`` list
   * - Randomization
     - UI button + extension settings
     - Per-behavior ``weight``, ``repeat``, range params in YAML
   * - Transition logic
     - Transition map JSON file
     - Weighted random selection from routine pool
   * - Interrupts
     - ``response`` + ``incident`` sections
     - ``triggers`` (time-based or event-based)
   * - Animation backend
     - ``omni.anim.people`` and ``omni.anim.graph``
     - ``omni.anim.behavior.core`` (v110+)
   * - Determinism seed
     - Global seed
     - Per-actor seed (name + group + global seed hashed)
   * - Stage representation
     - Runtime only
     - Persisted in USD prims and schemas

Available Behavior Types
-------------------------

**Character behaviors:**

* ``wander`` -- random walk and idle cycles with configurable speed, distance, idle animations
* ``patrol`` -- follow a path defined by 3D points or target prims
* ``stop`` -- remain stationary for a configurable time
* ``custom_behavior`` -- execute a Behavior Tree from a JSON file (re-enable planned for future)

**Robot behaviors:**

* ``wander`` -- random movement and idle with configurable distance and wait time
* ``patrol`` -- follow a path defined by 3D points or target prims
* ``halt`` -- stop for a configurable duration

**Trigger types (shared by characters and robots):**

* ``event_trigger`` -- fires on a named event
* ``time_trigger`` -- fires after a specified time (in seconds)

Step-by-Step Migration Checklist
=================================

Config File Migration
----------------------

1. Change ``version`` to ``1.x.x`` (for example, ``1.2.0``).
2. Move ``global.seed`` to root-level ``seed``.
3. Convert ``global.simulation_length`` (frames) to ``simulation_duration`` (seconds) at root level.

   * Formula: ``simulation_duration = simulation_length / 30.0``

4. Rename ``scene.asset_path`` to ``environment.base_stage_asset_path`` (this field is now **required**).
5. Restructure ``character`` into ``character.groups.<group_name>`` with ``num``, ``asset_path``, and inline ``routines``.
6. Convert external command files (``.txt``) to inline ``routines`` entries. Map old commands to new behavior types:

   * GoTo commands -> ``wander`` behavior with ``distance_range``
   * Idle commands -> ``wander`` behavior with ``idle`` list
   * Patrol-like sequences -> ``patrol`` behavior with ``path_points`` or ``target_prims``
   * See the :ref:`Configuration File Guide <ira_configuration_file>` for full behavior type documentation.

7. Restructure ``robot`` into ``robot.groups.<group_name>`` with ``num``, ``config_file_path``, and inline ``routines``.

   * Replace ``nova_carter_num: N`` with a group entry using ``config_file_path: "nova_carter.yaml"``.
   * Replace ``iw_hub_num: N`` similarly with the appropriate IAR config.

8. Replace ``sensor.camera_num`` and ``camera_list`` with ``sensor.groups.<group_name>`` using a placement strategy (``aim_at_targets`` or ``maximum_coverage``).
9. Move camera randomization settings (height, angle, focal length, distance ranges) from extension settings into the sensor group config.
10. Replace ``replicator.writer`` + ``replicator.parameters`` with ``replicator.writers.<WriterName>: { ... }``.
11. Remove ``response``, ``event``, and ``incident`` sections. Replace with ``triggers`` on individual character/robot groups.

Quick Config Conversion Example
--------------------------------

**Old (0.x):**

.. code-block:: yaml

   isaacsim.replicator.agent:
     version: 0.7.0
     global:
       seed: 123456789
       simulation_length: 1800
     sensor:
       camera_num: 4
     character:
       asset_path: ""
       command_file: default_command.txt
       num: 8
     robot:
       command_file: default_robot_command.txt
       nova_carter_num: 2
       iw_hub_num: 0
       write_data: false
     replicator:
       writer: IRABasicWriter
       parameters:
         semantic_filter_predicate: "class:character|robot;id:*"
         rgb: true
         camera_params: true

**New (1.x):**

.. code-block:: yaml

   isaacsim.replicator.agent:
     version: 1.2.0
     seed: 123456789
     simulation_duration: 60.0
     environment:
       base_stage_asset_path: "Isaac/Environments/Simple_Warehouse/full_warehouse.usd"
     sensor:
       groups:
         default_cameras:
           num: 4
           aim_at_targets:
             height_range: [2.0, 3.0]
             look_down_angle_range: [0.0, 60.0]
             focal_length_range: [13.0, 23.0]
             distance_range: [6.5, 14.0]
     character:
       groups:
         default_characters:
           num: 8
           asset_path: "Isaac/People/Characters/"
           routines:
             - wander:
                 walk:
                   speed_range: [1.0, 1.0]
                   distance_range: [5.0, 15.0]
                 idle:
                   - animation: idle
                     time_range: [2.0, 5.0]
     robot:
       groups:
         nova_carters:
           num: 2
           config_file_path: "nova_carter.yaml"
           routines:
             - wander:
                 move:
                   distance_range: [10.0, 15.0]
                 idle:
                   time_range: [2.0, 5.0]
     replicator:
       writers:
         IRABasicWriter:
           semantic_filter_predicate: "class:character|robot;id:*"
           rgb: true
           camera_params: true
           start_frame: 30
