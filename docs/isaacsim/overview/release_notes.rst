..
   Copyright (c) 2022-2026, NVIDIA CORPORATION. All rights reserved.
   NVIDIA CORPORATION and its licensors retain all intellectual property
   and proprietary rights in and to this software, related documentation
   and any modifications thereto. Any use, reproduction, disclosure or
   distribution of this software and related documentation without an express
   license agreement from NVIDIA CORPORATION is strictly prohibited.




=============
Release Notes
=============

6.0.0
=====

Release Highlights
------------------

General
^^^^^^^

- Updated to `Kit 110.1.1 <https://docs.omniverse.nvidia.com/dev-guide/latest/release-notes/110_1_1_highlights.html>`__.
- Improved rendering performance and fidelity with multitick rendering. Cameras and RTX Lidars can be scheduled and rendered at rates and offsets driven by physics simulation time.

PhysX and Newton
^^^^^^^^^^^^^^^^

- Added experimental support for the Newton physics engine.

  - C++ and Python tensor APIs for Newton are similar to PhysX. The ``isaacsim.core.experimental`` APIs provide an engine-agnostic interface to physics data.
  - ROS 2 Bridge handles the Newton backend similarly to PhysX. All OmniGraph nodes are compatible with Newton and PhysX.

- URDF and MJCF importers apply Newton schemas to imported assets.

Synthetic Data Generation
^^^^^^^^^^^^^^^^^^^^^^^^^

- **Perception Data Generation (Replicator)**

  - Added end-to-end synthetic data generation (SDG) workflow examples using the Replicator Functional API to author, randomize, simulate, and collect annotated data.

- **Action and Event Data Generation**

  - *Actor Simulation and Synthetic Data Generation* (``isaacsim.replicator.agent.core``, ``isaacsim.replicator.agent.schema``, and ``isaacsim.replicator.agent.ui``): Added a behavior-tree based actor controller, collision triggers for collider-based reactions, Stop and Halt behaviors, custom writer support, and verbose or minimal config serialization in the UI.
  - *Object Simulation and Synthetic Data Generation* (``isaacsim.replicator.object.core`` and ``isaacsim.replicator.object.ui``): Added empty space detection.
  - *Physical Space Event Generation* (``isaacsim.replicator.incident.core`` and ``isaacsim.replicator.incident.ui``): Standardized incident-report metadata.
  - *AI-based behavior tree generation* (``omni.ai.behavior_tree_gen.core`` and ``omni.ai.behavior_tree_gen.bridge``): Added extensions that convert natural-language scenario descriptions into behavior tree JSON files.
  - *Metropolis pipeline* (``omni.metropolis.pipeline``): Added a shared configuration and centralized orchestration pipeline for Action and Event Data Generation extensions.
  - Integrated telemetry in the Action and Event Data Generation toolsets to monitor system efficiency and behavioral trends.

- **Teleoperation Synthetic Data Generation**

  - Added support for teleoperation workflows (``isaacsim.replicator.teleop``) using the open NVIDIA Isaac Teleop framework. You can remotely control robots in simulation and build custom teleoperation applications.
  - Added support for episode recording and replay (``isaacsim.replicator.episode_recorder``). The recorder captures simulation state and teleoperation input to multi-episode HDF5 files for offline replay and SDG pipelines.

Robots
^^^^^^

- Robot policy examples can run Newton policies with the Newton simulator.
- URDF and MJCF importers can import multi-physics based assets and include new selection options for robot type and base type.
- Added robots under ``Samples/Mujoco_Menageries`` for robots imported from MuJoCo Menagerie with the MJCF importer.

Sensors
^^^^^^^

- **Cameras and Depth Sensors**

  - Added clean APIs for sensor authoring and runtime data collection in ``isaacsim.sensors.experimental.rtx``.
  - Added a structured light camera API with pattern projection and timing capability.
  - Expanded the camera asset catalog, including new sensors from Luxonis and SICK.
  - Improved pre- and post-ISP camera pipeline modeling fidelity with USD schemas instead of OmniGraph.
  - Deprecated the ``isaacsim.sensors.camera`` extension.

- **RTX Non-Visual Sensors**

  - Added clean APIs for sensor authoring and runtime data collection in ``isaacsim.sensors.experimental.rtx``.
  - Added RTX Acoustic ultrasonic sensor support.
  - Added support for instantaneous RTX Lidar full-scan point-cloud capture.
  - Expanded the RTX Lidar and RTX Radar asset catalog, including new sensors from Texas Instruments and SICK.
  - Deprecated the ``isaacsim.sensors.rtx`` extension.

ROS
^^^

- **Architecture and Modularization**

  - Isaac Sim ROS 2 workflows are now fully supported on Windows through Pixi with the Isaac Sim ROS Workspaces repository.
  - ROS 2 Publish TF and Odometry now consume pre-computed transforms from ``IsaacComputeTransformTree``. Direct ``targetPrims`` input for these ROS 2 OmniGraph nodes is deprecated.
  - ROS 2 Bridge migrated to the experimental core and sensor APIs: ``isaacsim.core.experimental.*`` and ``isaacsim.sensors.experimental.{rtx,physics}``.
  - The ``URDFImportFromROS2Node`` Kit command is deprecated. Use ``RobotDefinitionReader`` and ``URDFImporter`` instead.

- **New features**

  - Added ``OgnROS2RtxRadarHelper`` to publish RTX Radar as ``PointCloud2``.
  - Tensor-backed ROS 2 nodes run against any registered physics engine, including Newton.
  - Added Simulation Control services for ``GetEntityBounds``, ``SpawnEntities``, and ``GetSpawnables``.
  - Added ``wait_for_publishers_on_topic`` and ``wait_for_subscribers_on_topic`` helpers to ``ROS2TestCase``.

- **Performance improvements**

  - ``OgnROS2PublishJointState`` skips tensor view creation on the sensor-input path.
  - ``OgnROS2PublishTransformTree`` resolves ``toSdfPath`` once per entry and short-circuits invalid prims.
  - Point-cloud metadata fields are gated on matching ``output*`` flags, which prevents accidental message bloat.

- **Isaac Sim ROS Workspaces repository**

  - Now accepts external contributions. See ``CONTRIBUTING.md`` for the updated contribution workflow.
  - Added a Pixi-managed Jazzy workspace with Windows dependency management through Pixi and RoboStack, plus PyPI-based Isaac Sim install support.
  - Added Windows launch-file support for Isaac Sim.
  - Added the ``isaacsim_clearpath_nav2`` package for Nav2 integration with Clearpath robots.
  - Renamed the ``isaacsim`` package to ``isaacsim_bringup`` and migrated key packages from ``ament_cmake`` to ``ament_python``.

Docker
^^^^^^

- Added Docker Compose deployment for Isaac Sim + WebRTC web-viewer as a single stack.
- Support for running multiple Isaac Sim instances in parallel on a single machine.
- Full Docker container support for DGX Spark.
- Added support for the Hub Workstation Cache container.

Live-streaming
^^^^^^^^^^^^^^

- Added web-based livestreaming via WebRTC client accessible through Docker Compose.
- Configurable signal port and stream port via environment variables.
- The ``isaacsim.streaming.rtsp`` extension provides Real-Time Streaming Protocol (RTSP) live-streaming for camera render products in Isaac Sim. It captures rendered frames through a Replicator writer and publishes them over RTSP with ``omni.kit.livestream.rtsp``.
- Full DGX Spark livestreaming support.

Motion Generation
^^^^^^^^^^^^^^^^^

- Added support for task-based differential inverse kinematics with the Python Inverse Kinematics (PINK) implementation in ``isaacsim.robot_motion.pink``.

SimReady Content
^^^^^^^^^^^^^^^^

- The Isaac Sim content browser now depends on ``omni.simready.content.browser`` and includes the ``/Isaac/SimReady`` folder.
- The SimReady Asset Search workflow supports File Index, AI, and WSCache search modes, including filters for names, natural-language phrases, SimReady profiles, features, and tags.
- Added FANUC and Comau robot assets to the asset catalog. Additional FANUC robot assets (84+ models) are available in the Content Browser, and most have multiphysics-ready counterparts.

Breaking changes and deprecations
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. list-table::
   :header-rows: 1

   * - Change
     - Action required
     - Removed in
   * - Removed ``omni.isaac.*`` compatibility shims.
     - Migrate to ``isaacsim.*`` extensions.
     - 6.0.0
   * - Deprecated ``isaacsim.core.api``, ``isaacsim.core.prims``, and ``isaacsim.core.utils``.
     - Migrate to ``isaacsim.core.experimental.*`` and ``isaacsim.core.simulation_manager``.
     - Not specified.
   * - Deprecated ``isaacsim.examples.extension``.
     - Use the repo template system with ``./repo.sh template new``.
     - Not specified.
   * - Deprecated ``isaacsim.replicator.mobility_gen``.
     - Migrate to ``isaacsim.replicator.experimental.mobility_gen``. No action is required for ``isaacsim.replicator.mobility_gen.ui``.
     - Not specified.
   * - Deprecated ``isaacsim.replicator.domain_randomization``.
     - Migrate to ``isaacsim.replicator.experimental.domain_randomization``.
     - Not specified.
   * - Deprecated prim path inputs to ROS 2 OmniGraph nodes.
     - Refer to the migration guide.
     - Not specified.
   * - Deprecated ``isaacsim.cortex.behaviors``, ``isaacsim.cortex.framework``, and ``isaacsim.cortex.examples``.
     - Migration guidance is planned for 6.1.
     - Not specified.
   * - Deprecated ``isaacsim.robot.manipulators``, ``isaacsim.robot.manipulators.examples``, and ``isaacsim.robot.manipulators.ui``.
     - Refer to ``isaacsim.robot.experimental.manipulators.examples`` for recommended alternatives.
     - Not specified.
   * - Deprecated ``isaacsim.robot.wheeled_robots``.
     - Migrate to ``isaacsim.robot.experimental.wheeled_robots`` and ``isaacsim.robot.wheeled_robots.nodes``.
     - Not specified.
   * - Deprecated ``isaacsim.robot_motion.lula``, ``isaacsim.robot_motion.lula_test_widget``, ``isaacsim.robot_motion.motion_generation``, and ``isaacsim.robot_motion.motion_generation.examples``.
     - Migrate to ``isaacsim.robot_motion.experimental.motion_generation``, ``isaacsim.robot_motion.cumotion``, ``isaacsim.robot_motion.pink``, ``isaacsim.robot_motion.cumotion.examples``, and ``isaacsim.robot_motion.pink.examples``.
     - Not specified.
   * - Deprecated ``isaacsim.sensors.camera``.
     - Migrate to ``isaacsim.sensors.experimental.rtx``.
     - Not specified.
   * - Deprecated ``isaacsim.sensors.rtx``.
     - Migrate sensor authoring and runtime APIs to ``isaacsim.sensors.experimental.rtx``. Use ``isaacsim.sensors.rtx.nodes`` for RTX sensor OmniGraph, annotator, and point-cloud debug-draw workflows.
     - Not specified.
   * - Deprecated ``isaacsim.sensors.physics``, ``isaacsim.sensors.physx``, ``isaacsim.sensors.physx.examples``, and ``isaacsim.sensors.physx.ui``.
     - Migrate physics sensor APIs to ``isaacsim.sensors.experimental.physics``. Use ``isaacsim.sensors.physics.examples``, ``isaacsim.sensors.physics.nodes``, and ``isaacsim.sensors.physics.ui`` for examples, OmniGraph nodes, and UI workflows.
     - Not specified.
   * - Deprecated ``isaacsim.util.merge_mesh``.
     - Migrate to ``omni.scene.optimizer.core``.
     - Not specified.
   * - Deprecated ``isaacsim.replicator.agent`` 0.x.x.
     - Migrate to ``isaacsim.replicator.agent`` 1.x.x. Refer to the migration guide.
     - Not specified.
   * - Deprecated ``omni.isaac.ml_archive``.
     - No replacement is available. Install PyTorch directly or manually enable the extension if needed.
     - Not specified.
   * - Removed support for Camera prims as RTX sensors using JSON configs.
     - Migrate to ``isaacsim.sensors.experimental.rtx`` and OmniSensor prims.
     - 6.0.0
   * - Removed ``isaacsim.app.selector``, ``isaacsim.benchmark.examples``, and ``isaacsim.replicator.scene_blox``.
     - No replacement is available.
     - 6.0.0
   * - Removed ``isaacsim.asset.browser``.
     - Migrate to ``omni.simready.content.browser``.
     - 6.0.0

Known issues
^^^^^^^^^^^^

For known issues, see `Known Issues <https://docs.isaacsim.omniverse.nvidia.com/latest/overview/known_issues.html>`__.

Kit SDK Version
---------------

Changed: 109.0.2 -> 110.0.0

Kit SDK Dependency Version Changes
----------------------------------

Added
^^^^^
- isaacsim.anim.robot.core: 1.2.2
- isaacsim.anim.robot.schema: 0.1.0
- omni.behavior.scripting.core: 110.0.4
- omni.behavior.tree.core: 110.0.4
- omni.behavior.tree.schema: 110.0.1
- omni.kit.property.physics: 110.0.7
- omni.metropolis.pipeline: 0.0.5
- omni.metropolis.schema: 0.0.1
- omni.physics.isaacsimready: 110.0.7
- omni.physics.physx.ui: 110.0.7
- omni.physics.ui: 110.0.7
- omni.simready.configuration: 1.0.1
- omni.simready.content.browser: 0.2.4
- omni.simready.content.search: 1.0.5
- omni.simready.paths: 0.1.0

Removed
^^^^^^^
- isaacsim.anim.robot: 1.0.3
- omni.anim.behavior.asset: 109.0.6
- omni.anim.behavior.bundle: 109.0.6
- omni.anim.behavior.ui: 109.0.6
- omni.behavior.composer: 0.5.4
- omni.behavior.composer.schema: 0.4.0
- omni.behavior.composer.ui: 0.5.2
- omni.graph.io: 1.30.1
- omni.kit.profiler.window: 2.3.7
- omni.kit.property.physx: 109.0.10
- omni.kit.scripting: 109.0.5
- omni.kvdb: 109.0.10
- omni.localcache: 109.0.10
- omni.physx.telemetry: 109.0.10
- omni.warp: 1.10.1

Changed
^^^^^^^
- isaacsim.replicator.agent.core: 1.0.12 -> 1.2.6
- isaacsim.replicator.agent.schema: 0.0.1 -> 0.1.0
- isaacsim.replicator.agent.ui: 1.0.8 -> 1.0.20
- isaacsim.replicator.caption.core: 0.6.6 -> 0.7.5
- isaacsim.replicator.incident.core: 0.11.2 -> 0.11.7
- isaacsim.replicator.incident.ui: 0.6.0 -> 0.6.3
- isaacsim.replicator.object.core: 0.11.3 -> 0.11.8
- isaacsim.replicator.object.ui: 0.11.1 -> 0.11.3
- isaacsim.sensors.rtx.calibration: 0.3.2 -> 0.3.9
- isaacsim.sensors.rtx.placement: 0.16.4 -> 0.16.9
- isaacsim.util.debug_draw: 3.2.0 -> 3.2.1
- omni.ai.langchain.agent.chat_iro: 2.2.5 -> 2.2.8
- omni.ai.langchain.core: 2.2.0 -> 2.2.5
- omni.anim.asset: 109.0.6 -> 110.0.0
- omni.anim.behavior.core: 109.0.7 -> 110.0.8
- omni.anim.behavior.schema: 109.0.6 -> 110.0.1
- omni.anim.curve.bundle: 1.3.0 -> 1.4.0
- omni.anim.curve.core: 1.5.3 -> 1.6.0
- omni.anim.curve.ui: 1.6.1 -> 1.7.0
- omni.anim.curve_editor: 109.0.0 -> 110.0.0
- omni.anim.graph.bundle: 109.0.6 -> 110.0.0
- omni.anim.graph.core: 109.0.6 -> 110.0.3
- omni.anim.graph.schema: 109.0.6 -> 110.0.0
- omni.anim.graph.ui: 109.0.6 -> 110.0.1
- omni.anim.navigation.bundle: 109.0.6 -> 110.0.0
- omni.anim.navigation.core: 109.0.6 -> 110.0.3
- omni.anim.navigation.schema: 109.0.6 -> 110.0.0
- omni.anim.navigation.ui: 109.0.6 -> 110.0.2
- omni.anim.retarget.bundle: 109.0.6 -> 110.0.0
- omni.anim.retarget.core: 109.0.6 -> 110.0.3
- omni.anim.retarget.preview: 109.0.6 -> 110.0.5
- omni.anim.retarget.ui: 109.0.6 -> 110.0.1
- omni.anim.shared.core: 109.0.2 -> 110.0.0
- omni.anim.skelJoint: 109.0.6 -> 110.0.3
- omni.anim.timeline: 109.0.1 -> 110.0.0
- omni.anim.widget.timeline: 0.3.0 -> 0.4.0
- omni.anim.window.timeline: 109.0.2 -> 110.0.0
- omni.asset_validator.core: 1.9.2 -> 1.11.2
- omni.asset_validator.ui: 1.9.2 -> 1.11.2
- omni.convexdecomposition: 109.0.10 -> 110.0.7
- omni.cuopt.examples: 1.3.2 -> 1.4.1
- omni.cuopt.service: 1.3.1 -> 1.3.2
- omni.cuopt.visualization: 1.3.2 -> 1.4.0
- omni.curve.creator: 107.0.1 -> 110.0.0
- omni.curve.manipulator: 108.2.0 -> 110.0.0
- omni.flowusd: 109.0.2 -> 110.0.0
- omni.genproc.core: 109.0.0 -> 110.0.0
- omni.graph.action: 2.0.0 -> 2.10.2
- omni.graph.action_nodes: 2.0.3 -> 2.10.2
- omni.graph.action_nodes_core: 2.0.1 -> 2.10.2
- omni.graph.bundle.action: 3.0.1 -> 3.10.2
- omni.graph.examples.cpp: 2.0.1 -> 2.10.2
- omni.graph.nodes: 2.1.6 -> 2.10.2
- omni.graph.nodes_core: 2.0.3 -> 2.10.2
- omni.graph.scriptnode: 2.1.2 -> 2.10.2
- omni.graph.telemetry: 3.1.3 -> 3.10.2
- omni.graph.ui: 2.1.6 -> 2.10.2
- omni.graph.ui_nodes: 2.0.4 -> 2.10.5
- omni.graph.window.action: 2.2.1 -> 2.10.2
- omni.graph.window.core: 3.1.2 -> 3.10.2
- omni.graph.window.generic: 2.2.1 -> 2.10.2
- omni.kit.asset_converter: 5.0.25 -> 5.1.1
- omni.kit.converter.cad: ~207.0 -> ~209.0
- omni.kit.converter.common: 508.0.1 -> 510.0.0
- omni.kit.converter.dgn: 509.3.1 -> 510.0.0
- omni.kit.converter.dgn_core: 511.3.1 -> 512.0.0
- omni.kit.converter.hoops: 509.2.4 -> 510.0.0
- omni.kit.converter.hoops_core: 510.1.3 -> 511.0.0
- omni.kit.converter.jt: 508.2.6 -> 509.0.0
- omni.kit.converter.jt_core: 508.2.8 -> 509.0.0
- omni.kit.environment.core: 1.4.1 -> 1.4.2
- omni.kit.livestream.app: 9.0.0 -> 10.1.0
- omni.kit.livestream.core: 9.0.0 -> 10.0.0
- omni.kit.livestream.webrtc: 9.0.2 -> 10.1.2
- omni.kit.mesh.raycast: 108.0.0 -> 110.0.0
- omni.kit.pointclouds: 1.6.6 -> 1.6.7
- omni.kit.preferences.animation: 1.4.0 -> 1.5.0
- omni.kit.profiler.tracy: 1.2.0 -> 1.2.1
- omni.kit.sequencer.core: 108.1.1 -> 110.0.0
- omni.kit.sequencer.usd: 108.1.1 -> 110.0.0
- omni.kit.stagerecorder.bundle: 109.0.0 -> 110.0.0
- omni.kit.stagerecorder.core: 109.0.0 -> 110.0.2
- omni.kit.stagerecorder.ui: 109.0.0 -> 110.0.0
- omni.kit.timeline.minibar: 1.2.13 -> 1.2.14
- omni.kit.tool.measure: 200.0.4 -> 200.0.7
- omni.kit.variant.editor: 107.5.6 -> 107.5.8
- omni.kit.variant.presenter: 107.1.2 -> 107.1.3
- omni.kit.waypoint.core: 1.6.3 -> 1.6.4
- omni.kit.window.material_graph: 1.9.5 -> 1.9.6
- omni.kit.window.section: 107.1.3 -> 107.1.4
- omni.mesh_tools.libs: 109.0.8 -> 110.0.1
- omni.metropolis.utils: 0.14.7 -> 1.0.5
- omni.physics: 109.0.10 -> 110.0.7
- omni.physics.physx: 109.0.10 -> 110.0.7
- omni.physics.stageupdate: 109.0.10 -> 110.0.7
- omni.physics.tensors: 109.0.10 -> 110.0.7
- omni.physx: 109.0.10 -> 110.0.7
- omni.physx.asset_validator: 109.0.10 -> 110.0.7
- omni.physx.bundle: 109.0.10 -> 110.0.7
- omni.physx.camera: 109.0.10 -> 110.0.7
- omni.physx.cct: 109.0.10 -> 110.0.7
- omni.physx.commands: 109.0.10 -> 110.0.7
- omni.physx.cooking: 109.0.10 -> 110.0.7
- omni.physx.demos: 109.0.10 -> 110.0.7
- omni.physx.fabric: 109.0.10 -> 110.0.7
- omni.physx.foundation: 109.0.10 -> 110.0.7
- omni.physx.graph: 109.0.10 -> 110.0.7
- omni.physx.pvd: 109.0.10 -> 110.0.7
- omni.physx.supportui: 109.0.10 -> 110.0.7
- omni.physx.tensors: 109.0.10 -> 110.0.7
- omni.physx.tests: 109.0.10 -> 110.0.7
- omni.physx.tests.visual: 109.0.10 -> 110.0.7
- omni.physx.ui: 109.0.10 -> 110.0.7
- omni.physx.vehicle: 109.0.10 -> 110.0.7
- omni.ramp: 107.0.2 -> 110.0.0
- omni.replicator.core: 1.12.34 -> 1.13.4
- omni.replicator.nv: 1.0.0 -> 1.1.0
- omni.replicator.replicator_yaml: 2.0.11 -> 2.0.12
- omni.scene.optimizer.analysis: 109.0.2 -> 110.0.4
- omni.scene.optimizer.bundle: 109.0.2 -> 110.0.4
- omni.scene.optimizer.core: 109.0.2 -> 110.0.4
- omni.scene.optimizer.ui: 109.0.2 -> 110.0.4
- omni.scene.optimizer.validators: 109.0.2 -> 110.0.4
- omni.scene.visualization.core: 109.0.1 -> 110.0.0
- omni.services.convert.asset: 509.0.0 -> 510.0.0
- omni.services.convert.cad: 507.1.5 -> 508.0.0
- omni.services.pip_archive: 0.18.3 -> 0.18.6
- omni.usd.metrics.assembler: 109.0.0 -> 110.0.0
- omni.usd.metrics.assembler.physics: 109.0.10 -> 110.0.7
- omni.usd.metrics.assembler.ui: 109.0.0 -> 110.0.0
- omni.usd.schema.flow: 109.0.1 -> 110.0.0
- omni.usd.schema.metrics.assembler: 109.0.0 -> 110.0.0
- omni.usd.schema.physx: 109.0.10 -> 110.0.7
- omni.usd.schema.sequence: 3.1.2 -> 3.2.0
- omni.usdex.libs: 2.1.2 -> 2.2.1
- omni.usdphysics: 109.0.10 -> 110.0.7
- omni.usdphysics.ui: 109.0.10 -> 110.0.7
- omni.warp.core: 1.10.1 -> 1.12.0

Extensions Changelog Summary
----------------------------

Please refer to the individual extension changelogs for more detailed information.

- Common updates across many extensions include refreshed `Overview.md`, `python_api.md`, `SETTINGS.md`, and docstrings.
- Several extensions were modernized for `Events 2.0`, deprecated callback/API replacements, and current Warp/core API usage.
- Shared UI/menu cleanup also landed across multiple extensions, including menu action and content browser integration updates.

- **isaacsim.app.setup**

    - Changed

      - Add logging to await_viewport to help debug viewport handle not being available
      - Add missing dependency for Robot Hierarchy window
      - Added dock info for Robot Hierarchy window
      - Refactor enable_ros_extensions to properly wait for viewport to be ready before enabling ROS2 extensions
      - Restructured extension into modular components

    - Fixed

      - Rename "Robot Hierarchy" window to "Robot Inspector" in default and sdg layouts

- **isaacsim.asset.exporter.urdf**

    - Changed

      - Add explicit omni.physics.physx dependency

- **isaacsim.asset.gen.omap.ui**

    - Added

      - Save YAML button in the visualization window to save the ROS occupancy map parameters file directly, alongside the existing Save Image button
      - Image File Name field in the visualization window to set the image filename used in the YAML; defaults to the stage name
      - Update YAML button to rebuild the YAML content with the new filename without regenerating the image
      - Save Image dialog now pre-fills the filename from the Image File Name field

    - Changed

      - Added dock info for Robot Hierarchy window

- **isaacsim.asset.importer.heightmap**

    - Changed

      - Add isaacsim.core.experimental.objects dependency, remove omni.physics.physx dependency for groundplane creation

- **isaacsim.asset.importer.mjcf**

    - Changed

      - Added scene import option for the MJCF importer
      - MJCF converter version bump to 0.1.0a8
      - Added mjc / newton to physx attribute conversion for multi-physics engine asset support
      - Changed dep from pip prebundle to isaacsim.pip.newton
      - Switched to lazy import for mjcf-usd-converter to fix docs build issue
      - USD exchange backend
      - New import format
      - New UI design and interface

- **isaacsim.asset.importer.urdf**

    - Removed

      - Removed UI elements from the URDF importer, moved to isaacsim.asset.importer.urdf.ui extension

    - Changed

      - update urdf-usd-converter to v0.1.0
      - urdf converter version bump to v0.1.0rc2
      - Added mjc / newton to physx attribute conversion for multi-physics engine asset support
      - USD exchange based backend
      - Unified UI
      - Asset structure 3

    - Fixed

      - Updated configuring of mimic joints to be processed after all joints are created to avoid issues with lexicographical order of siblings

- **isaacsim.asset.validation**

    - Changed

      - Updated physics_rules to use new omni.physics.core API (`IPhysicsSimulation.initialize`/`close` replaces removed `attach_stage`/`detach_stage`)

- **isaacsim.benchmark.services**

    - Added

      - Public API properties for frametime recorders: `sample_count` and `samples` for direct recorder access
      - Decorator-based plug-in system for recorders using `@MeasurementDataRecorderRegistry.register()`
      - `DEFAULT_RECORDERS` constant exported for customization in benchmark scripts
      - Process-specific CPU tracking
      - Main thread CPU tracking via single-core usage metrics (Mean/Min/Max)
      - Support for selecting recorders via `recorders` list passed into `BaseIsaacBenchmark` instance
      - Added "Num App Updates" metric to report the number of app update events per phase

    - Removed

      - Legacy collector classes (`IsaacUpdateFrametimeCollector`)
      - Wrapper layer between collectors and recorders
      - Unused profiling, settings, and execution modules
      - Removed support for passing in `gpu_frametime=True` into `BaseIsaacBenchmark` instance

    - Changed

      - Merged `BaseIsaacBenchmark` and `BaseIsaacBenchmarkAsync` into unified core with shared logic
      - Refactored data architecture: eliminated collector layer, one recorder per metric
      - Report formatting: metrics ordered by category (Performance, Custom, Memory, CPU table, Frametime table)
      - Recorder lifecycle: stop/collect from recorders that were started in a given phase

    - Fixed

      - Fixed validation tooling to correctly build the render product map

- **isaacsim.code_editor.vscode**

    - Fixed

      - Hardened subprocess call to avoid shell=True with string concatenation

- **isaacsim.core.api**

    - Removed

      - Remove deprecated PhysX residual reporting APIs (`enable_residual_reporting`, `get_solver_velocity_residual`, `get_solver_position_residual`) from `PhysicsContext`.

    - Fixed

      - Fix issues with incorrect API usage in ArticulationSubset

- **isaacsim.core.deprecation_manager**

    - Changed

      - Remove deprecated asset browser settings

- **isaacsim.core.experimental.objects**

    - Added

      - Add USD `Camera`
      - Add the `colors` parameter to shape classes to set display colors

- **isaacsim.core.experimental.prims**

    - Added

      - `getDofNames()` and `getDofTypes()` on `IArticulationDataView` for articulation DOF metadata (names and types in articulation order)
      - `setArticulationDofMetadata()` on `IPrimDataReader` for Newton backend to supply DOF names and types from Python
      - `XformPrim` now creates `FabricHierarchyLocalMatrix` and `FabricHierarchyWorldMatrix` if they don't exist.
      - Add Newton physics engine support for articulations and rigid bodies
      - Add contact tracking functionality to RigidPrim: `set_enabled_contact_tracking()`, `get_enabled_contact_tracking()`, `get_net_contact_forces()`, `get_contact_force_matrix()`, `get_contact_force_data()`, `get_friction_data()`

    - Removed

      - Remove deprecated PhysX residual reporting APIs (`enable_residual_reports`, `get_solver_residual_reports`) from `Articulation`

    - Changed

      - Add C++ interface to read xform, rigid body and articulation data
      - Slight modification to show how a new physics engine can be added in the future

    - Fixed

      - Fixed Warp 1.12 compatibility for deformable prims (wp.mat33 row-vector constructor replaced with wp.matrix_from_rows)
      - Only return values for DOFs that have applied the `PhysxDrivePerformanceEnvelopeAPI` when querying drive model properties

- **isaacsim.core.experimental.utils**

    - Added

      - Add `get_prim_attribute_names()` to prim utils for listing authored attribute names
      - Add `get_prim_attribute_value()` to prim utils for getting attribute values
      - Add `quaternion_to_euler_angles()` function to transform utils for converting quaternions to euler angles
      - Add `parse_device()` function to ops utils for parsing Warp device specifications
      - Add `ensure_api()` function to prim utils for ensuring API schemas are applied to prims

    - Fixed

      - Fix NaN issue in euler to quaternion conversion utils
      - Fix inconsistency in euler to quaternion conversion utils

- **isaacsim.core.includes**

    - Added

      - Add `Defines.h` header with `ISAACSIM_EXPORT` and `ISAACSIM_IMPORT` macros for DLL visibility

    - Changed

      - Optimize GenericBuffer to re-use memory without allocation if requested size fits within existing capacity.

- **isaacsim.core.nodes**

    - Added

      - IsaacAttachHydraTexture node allows user to add HydraTextures and RenderVars on demand to RenderProduct prims already in the stage

    - Changed

      - Migrate Odometry and joint name resolved nodes to use core experimental prims APIs

- **isaacsim.core.prims**

    - Removed

      - Remove deprecated PhysX residual reporting APIs (`enable_residual_reports`, `get_position_residuals`, `get_velocity_residuals`) from `Articulation` and `SingleArticulation`.

    - Fixed

      - Fixed missing argument `context` in `_reset_fabric_selection` method.
      - Fixed incorrect method call `set_wind` to `set_winds` in `ParticleSystem` constructor.
      - Fixed incorrect attribute name `solverPositionIteration` to `solverPositionIterationCount` in `ParticleSystem.get_solver_position_iteration_counts`.

- **isaacsim.core.rendering_manager**

    - Changed

      - Move import of kit loop runner to a try-except block to handle import exceptions if omni.kit.loop-isaac is not enabled

- **isaacsim.core.simulation_manager**

    - Added

      - Add Newton physics engine support with `switch_physics_engine()` method
      - Add `NewtonMjcScene` and `NewtonXpbdScene` classes for Newton solver-specific scene configuration
      - Add `PhysicsScene` base class for common physics scene operations
      - When `/rtx/hydra/supportMultiTickRate` is enabled, simulation time is propagated to the run loop
      - Add `cleanupInvalidPhysicsScenes()` method to C++ `ISimulationManager` interface to remove tracked physics scenes with invalid prims
      - Add `isValid()` method to C++ `PhysicsScene` class to check if the underlying prim is still valid
      - Add Python binding for `cleanup_invalid_physics_scenes()` method
      - Add supporting APIs for changing physics engines through the omniphysics interfaces
      - Add `PhysicsScene` and `PhysxScene` Python class wrappers for high-level physics scene manipulation
      - Add `PhysicsScene` C++ class and header for USD Physics Scene prim operations
      - Add `get_physics_scene_paths()` function to get all physics scene paths in a stage

    - Changed

      - Replaced omni.physx start_simulation with omni.physics start_simulation
      - Replaced omni.physx simulation event stream with omni.physics simulation event stream
      - Change log level of no adjacent samples found for interpolation warning to INFO

    - Fixed

      - Rebuild with new physics package
      - Fix `RuntimeError: Accessed invalid expired 'PhysicsScene' prim` error when physics scene prims become invalid without triggering USD notices (e.g., layer removal operations, session sublayer changes)
      - Add stage and root layer validation in `_on_play()` to prevent physics initialization on expired/invalid stages
      - Add error handling in `_create_physics_scene()` to gracefully handle physics scene creation failures

- **isaacsim.core.utils**

    - Changed

      - Fix quaternion order issue in torch transformation utils

- **isaacsim.cortex.framework**

    - Deprecated

      - Extension deprecated. Will be replaced in 7.0 with simple examples and open source equivalents.

    - Changed

      - Moved RMPflowCortex policy configs (Franka and UR10) from isaacsim.robot_motion.motion_generation into data/motion_policy_configs for safekeeping.

- **isaacsim.cortex.behaviors**

    - Deprecated

      - Extension deprecated. Will be replaced in 7.0 with simple examples and open source equivalents.

- **isaacsim.cortex.examples**

    - Deprecated

      - Extension deprecated. Will be replaced in 7.0 with simple examples and open source equivalents.

- **isaacsim.examples.base**

    - Changed

      - Replaced timeline API with app utils for simulation control
      - Add functionality to allow setting rendering_dt.

- **isaacsim.examples.extension**

    - Changed

      - Add ticked=True to Extension Generator menu item

- **isaacsim.examples.interactive**

    - Changed

      - Experimental API alignment: app_utils for timeline control, SimulationEvent for physics callbacks.
      - Replaced timeline API with app utils for simulation control.
      - Converted Robo Party to Experimental APIs.
      - The Getting Started, Replay Follow Target, Robo Factory, and Surface Gripper examples now depend on the new Warp-based APIs
      - Simplified bin filling example to improve stability, replaced dropped parts with dropped cubes

- **isaacsim.gui.components**

    - Added

      - Add menu.create_submenu to recursively build MenuItemDescription lists from dicts describing submenus

    - Changed

      - Remove unused dependencies
      - Add menu.open_content_browser_to_path to open the Content Browser to a specific path

    - Fixed

      - Hardened subprocess calls to avoid shell=True with string concatenation
      - Fixed incorrect type annotation for SearchWidget

- **isaacsim.gui.content_browser**

    - Added

      - New `omni.simready.content.browser` extension for Simready asset search

    - Changed

      - Update omni.simready.content.browser settings
      - Add SimReady folder
      - Update assets path to 6.0 staging
      - Update assets path to development

- **isaacsim.gui.menu**

    - Added

      - Robot Self-Collision Detector to Tools > Asset Editors menu

    - Removed

      - Removed Warp Sample Scenes menu item from Help menu (omni.warp dependency removed)

    - Changed

      - Add ticked=True to Asset Check menu item
      - Remove Asset Browser from menu and context menu
      - Use menu.open_content_browser_to_path to open the Content Browser to a specific path as a replacement
      - Add Utility menu item to check Isaac Sim assets root path
      - Fix broken Isaac Sim documentation links

- **isaacsim.gui.property**

    - Added

      - Introduced widget for applying IsaacSiteAPI to Xformable prims
      - Introduced new widget for setting the IsaacMotionPlanningAPI collisionEnabled attribute

    - Fixed

      - Fixed incorrect type annotation (List to list)

- **isaacsim.replicator.behavior**

    - Changed

      - Migrated behavior scripting dependency from omni.kit.scripting to omni.behavior.scripting.core
      - Updated SDG physics based volume filling behavior script to use the omni.physx api

- **isaacsim.replicator.examples**

    - Changed

      - Synched snippets with docs, typos and print statements fixes
      - Augmentation examples use basic empty stage (dome light + ground plane) by default, with optional env_url for custom stages

- **isaacsim.replicator.mobility_gen**

    - Added

      - Support loading usdz asset

- **isaacsim.replicator.mobility_gen.examples**

    - Changed

      - Change occupancy map radius for Carter Robot

- **isaacsim.replicator.mobility_gen.ui**

    - Added

      - Support loading usdz asset

- **isaacsim.replicator.synthetic_recorder**

    - Changed

      - Updated UI to use width and height for checkboxes to fix click issues

- **isaacsim.replicator.writers**

    - Changed

      - Added pinholeOpenCV and fisheyePolynomial projection support to pose writer
      - Moved DOPE utils to DOPEWriter class

- **isaacsim.robot.manipulators.examples**

    - Added

      - UR (Universal Robots) stacking example
      - A simplified stacking class based on core_experimental (NVIDIA Warp APIs)

    - Changed

      - Experimental API alignment: app_utils for timeline control and SimulationEvent for physics callbacks in follow-target and pick-place examples.
      - Supported multiple Franka robots for pick and place task
      - Updated the folder structure of the extension
      - Simplify bin filling example and improve stability, example cubes instead of various parts

- **isaacsim.robot.schema**

    - Added

      - `KinematicChain` class for building and caching joint chains between arbitrary start/end prims on a robot
      - Forward Kinematics computation (`compute_fk`) with per-joint intermediate transforms
      - Fused FK + spatial Jacobian computation (`compute_fk_and_jacobian`) in a single pass
      - `IKSolver` abstract interface and `IKSolverRegistry` for pluggable IK solver implementations
      - Levenberg-Marquardt IK solver (`IKSolverLM`) registered as the default solver, with adaptive damping, null-space bias toward joint centers, step clamping, and joint-limit clipping
      - `pose_error` function computing 6-DOF orientation + position error between two transforms
      - Math module (`math.py`): `Transform` (SE(3) composition and inversion), `Joint` (screw-axis exponential map for revolute and prismatic joints), quaternion operations (`quat_mul`, `quat_conj`, `quat_rotate`, `axis_angle_to_quat`, `quat_to_matrix`), `skew`, and `adjoint`
      - Teleport functionality on `KinematicChain`: `teleport` propagates FK through the kinematic tree and writes USD body transforms; `teleport_anchored` applies joints while keeping a specified link fixed via rigid correction
      - Zero-configuration pose computation (`_compute_zero_config_poses`) using static joint local frames
      - Joint chain path finding via LCA algorithm (`_collect_chain_joints`) returning ordered joints with forward/backward traversal direction
      - Named pose query utilities: `GetAllNamedPoses`, `GetNamedPoseStartLink`, `GetNamedPoseEndLink`, `GetNamedPoseJoints`, `GetNamedPoseJointValues`, `GetNamedPoseJointFixed`, `GetNamedPoseValid`
      - `CreateNamedPose` for creating `IsaacNamedPose` prims with relationships and attributes
      - Loop detection in articulation traversal (`_discover_articulation_prims`, `PopulateRobotSchemaFromArticulation`, `RecalculateRobotSchema`) using visited-set guards to prevent infinite loops in cyclic joint graphs
      - `DetectAndApplySites` and `AddSitesToRobotLinks` for automatic site detection on link child Xforms and registration in the robot schema
      - `ApplySiteAPI` function; `ApplyReferencePointAPI` deprecated and redirected to `ApplySiteAPI`
      - `ValidateRobotSchemaRelationships` returning valid/invalid link and joint lists
      - `RecalculateRobotSchema` that preserves existing relationship order while appending newly discovered items and removing invalid ones
      - `RebuildRelationshipAsPrepend` and `EnsurePrependListForRobotRelationships` for proper USD layering of robot relationships
      - Schema diagram generation script
      - Loop detector on parsing of joints
      - Missing SiteAPI functions
      - Verify if all found links and joints are added to the schema
      - Detect and Create SiteAPIs when applying robot schema
      - Update Robot Schema relationships with missing links and joints

    - Changed

      - `UpdateDeprecatedSchemas` migrates `ReferencePointAPI` to `SiteAPI` and deprecated DOF offset attributes to `DofOffsetOpOrder` token array
      - `UpdateDeprecatedJointDofOrder` collects deprecated per-axis attributes, builds token array, and removes old attributes
      - Updated deprecated schema checker and fixer

- **isaacsim.robot.wheeled_robots**

    - Changed

      - Update to new osqp version and fix OSQP.setup() positional argument issue

- **isaacsim.robot_motion.lula**

    - Changed

      - Updated Overview.md with note about newer cumotion extension.

- **isaacsim.robot_motion.motion_generation**

    - Changed

      - Updated Overview.md with note about newer experimental motion generation API.
      - Updated path_planner_visualizer.py docstring to clarify it only does interpolation.

- **isaacsim.robot_motion.motion_generation.examples**
    - Removed

      - Removed RMPflowCortex policy configs for Franka and UR10 (moved to deprecated isaacsim.cortex.framework extension).


- **isaacsim.robot_motion.motion_generation.tutorials**

    - Changed

      - Update license headers

- **isaacsim.robot_setup.gain_tuner**

    - Changed

      - Migrate mass property queries from PhysX property query interface to Articulation tensor API (`isaacsim.core.experimental.prims.Articulation`).
      - Remove `omni.physics.physx` dependency; mass, COM, and inertia are now queried via `get_link_masses()`, `get_link_coms()`, and `get_link_inertias()`.

    - Fixed

      - Fixed incorrect type annotations
      - Fix Vec3f/Vec3d type mismatch in inertia accumulation caused by robot schema double-precision change

- **isaacsim.robot_setup.xrdf_editor**

    - Added

      - Can load and export XRDF version 2.0

    - Fixed

      - Removed incorrect type annotation for SimulationContext

- **isaacsim.ros2.core**

    - Added

      - CompressedImage message backend
      - Added ros2 image buffer utils

    - Changed

      - Removed hardcoded ROS 2 distribution checks. Added experimental support for any ROS 2 distribution beyond Jazzy to be sourced and used with Isaac Sim.
      - Fixed ROS 2 service request polling so `takeRequest()` can receive a pending request on its first poll call.
      - Removed isaacsim.sensors.experimental.physics dependency
      - Set publish_with_queue_thread extension setting to true
      - Added a `simulate_until_condition` method

    - Fixed

      - Hardened subprocess call to avoid shell=True with string concatenation

- **isaacsim.ros2.examples**

    - Changed

      - Update waypoint follower action graph to use ReadPrimLocalTransform node

- **isaacsim.ros2.nodes**

    - Added

      - ROS 2 H.264 Compressed Image support with H.264 RGB handling
      - omni.replicator.nv extension automatically enabled by omni.replicator.core and implictily used for HW H.264 encoding

    - Removed

      - Moved test_menu_graphs to isaacsim.ros2.ui
      - Replaced fields_to_dtype with sensors_msgs_py.point_cloud2.read_points where applicable

    - Changed

      - ROS2PublishJointState node now publishes from sensor inputs (e.g. IsaacReadJointState) for joint state data
      - Shifted RTX sensor scan accumulation and post-processing back to host by default to reduce GPU resource contention and improve frametime & frametime consistency. Post-processing-on-device still available as option by setting app.sensors.nv.[modality].outputBufferOnGPU=true.
      - Converted OgnROS2QoSProfile node from Python to C++ for improved performance and consistency with other C++ OG nodes
      - Add missing dependency for isaacsim.sensors.physics.nodes
      - Update isaacsim.sensors.physics dependency to isaacsim.sensors.experimental.physics
      - Update waypoint follower action graph to use ReadPrimLocalTransform node

    - Fixed

      - Fix `eFloat` and `eUnknown` cases in `writeNodeAttributeFromMessage` incorrectly hardcoding `"outputs:"` prefix instead of using `inputOutput(isOutput)` and `prependStr`

- **isaacsim.ros2.ui**

    - Added

      - Added PointCloud2 metadata options to RTX Lidar OG tool
      - Added test_menu_graphs

    - Changed

      - Migrated test_menu_graphs imports to use experimental prims and stage utilities (XformPrim, define_prim, add_reference_to_stage)
      - Fixed articulation root path in test_joint_states_data_flow and test_odometry_data_flow to use chassis_link
      - Fixed SimpleCheckBox widget path for "Publish Robot's TF?" in test_odometry_data_flow
      - Remove Asset Browser from menu
      - Use menu.open_content_browser_to_path to open the Content Browser to a specific path as a replacement

- **isaacsim.ros2.urdf**

    - Changed

      - Updated isaacssim.ros2.urdf to use URDF importer 3.x
      - Make isaacsim.asset.importer.urdf.ui a dependency since this extension heavily depends on and modifies the default urdf importer ui

- **isaacsim.sensors.camera**

    - Changed

      - omni:rtx:post:depthSensor:outlierRemovalEnabled is now a bool
      - Camera sensor: switched to use "_fast" version of the annotators where available ("bounding_box_2d_tight_fast", "bounding_box_2d_loose_fast", "instance_segmentation_fast", "instance_id_segmentation_fast")

    - Fixed

      - TestSingleViewDepthSensor.test_getter_setter_methods uses correct initial value for confidenceThreshold.
      - Cleanup annotators and state properly when the camera is destroyed
      - Fixed camera_view.get_data() resolution order issue (height, width) -> (width, height)

- **isaacsim.sensors.camera.ui**

    - Fixed

      - Registered proper actions for all camera and depth sensor creation menu items

- **isaacsim.sensors.experimental.physics**

    - Added

      - Add joint state sensor that reads all DOF positions, velocities, and efforts per articulation

    - Changed

      - Rewrite sensor implementations to use C++ core experimental prims APIs
      - IMU and Contact sensor creation commands renamed to include Experimental in their name to avoid name collision with deprecated sensor commands
      - Rebuilt physics sensors on core experimental APIs with Python-first implementations
      - Added Python backends for contact and IMU sensors plus legacy interface shims for compatibility
      - Added new command-based prim creation for sensors and OmniGraph nodes
      - Removed sensor period and frequency parameters, all sensors use the physics frequency by default

- **isaacsim.sensors.physics**

    - Changed

      - Deprecated this extension in favor of isaacsim.sensors.experimental.physics extension
      - Moved omnigraph nodes from this extension to isaacsim.sensors.nodes extension. The nodes use the new api from isaacsim.sensors.experimental.physics extension.

    - Fixed

      - Fix crash issue when IPhysxSimulation interface is not available

- **isaacsim.sensors.physics.examples**

    - Added

      - Updated to use interfaces from isaacsim.sensors.experimental.physics extension
      - Updated contact and IMU examples to use the new sensor command APIs and legacy Python interfaces
      - Improved example UI lifecycle handling with typed callbacks, stage-close cleanup, and richer docstrings

    - Changed

      - IMU and Contact sensor creation commands renamed to include Experimental in their name to avoid name collision with deprecated sensor commands

- **isaacsim.sensors.physics.ui**

    - Added

      - Updated to use interfaces from isaacsim.sensors.experimental.physics extension
      - Updated menu actions to use new sensor creation commands and experimental prim helpers
      - Improved context menu handling and visibility control for created sensor prims

    - Changed

      - IMU and Contact sensor creation commands renamed to include Experimental in their name to avoid name collision with deprecated sensor commands

    - Fixed

      - Registered proper actions for Contact Sensor and IMU Sensor creation menu items

- **isaacsim.sensors.physx.ui**

    - Fixed

      - Registered proper actions for PhysX Lidar and LightBeam sensor creation menu items

- **isaacsim.sensors.rtx**

    - Added

      - Use Hydra time (omni.timeline) in RTX Sensor models

    - Removed

      - Tools for manipulating deprecated JSONs

    - Changed

      - Shifted RTX sensor scan accumulation and post-processing back to host by default to reduce GPU resource contention and improve frametime & frametime consistency. Post-processing-on-device still available as option by setting app.sensors.nv.[modality].outputBufferOnGPU=true.
      - IsaacSensorCreateRtxSensor commands accept usd_path argument to enable adding arbitrary RTX Sensor USDs to the stage
      - IsaacSensorCreateRtxRadar command validates if user has enabled Motion BVH before creating prim

    - Fixed

      - Fixed occasional segfault when running with many lidars doing full-scan processing at the same time by copying GenericModelOutput buffers into local copies rather than manipulating AOV
      - IsaacCreateRTXLidarScanBuffer.transform output no longer resets frame-to-frame
      - Only reset outputs in IsaacCreateRTXLidarScanBuffer if enablePerFrameOutput == True, preventing output "flickering"
      - Prevent USD path warnings when using IsaacSensorCreateRtxSensor commands

- **isaacsim.sensors.rtx.ui**

    - Fixed

      - Registered proper actions for all RTX Lidar and RTX Radar sensor creation menu items

- **isaacsim.simulation_app**

    - Added

      - Added separate default render settings for PathTracing and RealTimePathTracing modes

    - Changed

      - Automatically close the application during interpreter shutdown if close() was not called
      - Close stage in simulation app close() method to avoid errors
      - Update error message when application fails to start and exit before proceeding to make debugging easier.
      - Fix issue where simulation app close() method would hang if the app was already stopped
      - Skip explicit stage close in simulation app close() method to avoid crashes
      - is_running method does not require an active USD stage
      - Use close_stage_async method when closing stage to avoid blocking the main thread if available
      - Simulation app close() method now waits for replicator workflows to complete even when using replicator step()

- **isaacsim.storage.native**

    - Changed

      - Update assets path to 6.0 staging
      - Add retry attempts and retry base delay settings for asset root connectivity checks
      - Update assets path to development

- **isaacsim.test.collection**

    - Changed

      - Exclude NumPy module reload errors
      - Update dependencies to use new experimental extensions

- **isaacsim.test.utils**

    - Added

      - Move `find_widget_with_retry` from `MenuUITestCase` to `menu_utils` as a standalone function
      - Add `find_enabled_widget_with_retry` to poll for a widget that is both found and enabled
      - Add `wait_for_widget_enabled` to poll until an already-found widget becomes enabled
      - Add new utility functions (`get_all_menu_paths`, `count_menu_items`) and `MenuUITestCase` base class for menu UI tests.

    - Changed

      - Add `omni.kit.material.library.get_mdl_list_async` and `omni.kit.menu.utils.rebuild_menus` to `MenuUITestCase.wait_for_stage_loading` to fix menu rebuild issues
      - Add `find_widget_with_retry` to `MenuUITestCase` to find a widget with retry
      - Replace `omni.kit.ui_test.menu_click` with custom step-by-step menu navigation that polls for each submenu to become findable and visible before proceeding, avoiding the `carb.log_error` and `AttributeError` that `menu_click` produces when submenus are slow to appear
      - Add `carb.log_info` diagnostics throughout `menu_click_with_retry` for log debugging
      - Suppress transient error logs from `omni.kit.ui_test.query` during intermediate retries in `menu_click_with_retry`; errors are only surfaced on the final retry attempt
      - Add pycoverage patch for numpy `_CopyMode.__bool__` to prevent `ValueError` when scipy imports trigger `_CopyMode.IF_NEEDED` evaluation under coverage
      - Fix pycoverage compatibility issue with numpy sum and prod functions
      - Add a pycoverage compatible amin and amax implementation that is monkeypatched into numpy on extension startup. Removed from image_comparison.py as it is no longer needed.
      - This is only used if --/exts/omni.kit.test/pyCoverageEnabled=1 is set
      - Refactor menu_click_with_retry into a separate function
      - Add new_stage to MenuUITestCase

    - Fixed

      - Add `omni.kit.material.library` as a dependency

- **omni.isaac.core_archive**

    - Changed

      - Update to llvmlite==0.46.0, nest_asyncio==1.6.0, matplotlib==3.10.8, contourpy==1.3.3, fonttools==4.61.1, pyparsing==3.3.2, cycler==0.12.1, kiwisolver==1.4.9, packaging==26.0, osqp==1.0.5, pyperclip==1.8.0, pyperclip==1.11.0

- **omni.isaac.ml_archive**

    - Changed

      - Update to pytorch 2.10.0+cu128, torchaudio 2.10.0+cu128, torchvision 0.25.0+cu128 and update dependencies

- **omni.kit.loop-isaac**

    - Added

      - Added `set_next_simulation_time` function and Python binding to support multi-tick rendering mode
      - When `/rtx/hydra/supportMultiTickRate` is enabled, `SWHExternalSimulationTime` is passed to the run loop

- **omni.pip.cloud**

    - Changed

      - Update cryptography to 46.0.5
      - Update azure-core to 1.38.0
      - Update msal to 1.35.1
      - Downgrage boto3 to 1.40.61
      - Downgrage botocore to 1.40.61
      - Downgrage s3transfer to 0.14.0
      - Update aioboto3 to 15.5.0

- **omni.pip.compute**

    - Added

      - Added "pynvvideocodec==2.1.0"

    - Changed

      - Update imageio==2.37.2, scipy==1.17.0, pyyaml==6.0.3, opencv-python-headless==4.13.0.90, trimesh==4.11.1, rtree==1.4.1

Isaac Sim ROS Workspaces Changelog Summary
-------------------------------------------

The `Isaac Sim ROS Workspaces <https://github.com/isaac-sim/IsaacSim-ros_workspaces>`_ companion repository for Isaac Sim ROS Bridge has the following changes for Isaac Sim 6.0.0:

Added
^^^^^
- ``isaac_compressed_image_decoder`` package for decoding ROS 2 compressed images [Humble, Jazzy]
- ``ros2_object_id_subscriber`` tutorial example in ``isaac_tutorials`` [Humble, Jazzy]
- ``topic_based_ros2_control`` ROS 2 package added as a submodule [Jazzy]
- Multi-humanoid namespace support in ``h1_fullbody_controller`` launch [Humble, Jazzy]
- Ubuntu 24.04 / ROS 2 Jazzy Python 3.12 Docker build support and dockerfile [Jazzy]
- ``rmw_zenoh`` support for Jazzy 22.04 Docker build [Jazzy]
- ``--no-cache`` (``-n``) flag for ``build_ros.sh`` to allow cache-free Docker rebuilds [Humble, Jazzy]

Changed
^^^^^^^
- Bumped all package versions to Isaac Sim 6.0.0
- Improved Humble MoveIt integration with custom ``panda_isaac.urdf.xacro`` and ``gripper_to_isaac.py`` bridge [Humble]
- Updated MoveIt configs to mitigate timeout issues [Jazzy]
- Cleaned up occupancy map parameters in Navigation packages [Humble, Jazzy]
- Updated internal libraries path to ``isaacsim.ros2.core`` in ``isaacsim`` ROS package [Humble, Jazzy]
- Switched ``h1_fullbody_controller`` topics to relative names for namespaced multi-humanoid setups [Humble, Jazzy]

Removed
^^^^^^^
- Legacy references to older Ubuntu / Python / ROS mentions from launch files, parameters, and build scripts


.. toctree::
	:maxdepth: 2

	./known_issues
	../migration_guides/index



