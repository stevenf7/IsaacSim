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


6.0.1 GA
========

Release Highlights
------------------

General
^^^^^^^

- Updated to Kit SDK 110.1.1 -> 110.1.2
- Upgraded the asset toolchain with major releases of the asset converter, importer, and exporter, along with DGN, HOOPS, JT, and CAD converter updates.
- Completed a repo-wide linting and docstring pass with regenerated ``python_api.md`` files and extensive documentation updates from validation and design review feedback.

NuRec and MobilityGen
^^^^^^^^^^^^^^^^^^^^^^

- Added the ``isaacsim.replicator.nurec_utils`` extension, which consolidates NuRec rendering, metrics, and detection utilities.
- Added teleoperation support for NuRec scenes that render through Sparse Pixel Gaussian (SPG) graphs, plus volume NuRec detection in addition to particle scenes.


Kit SDK Version
---------------

Changed: 110.1.1 -> 110.1.2

Kit SDK Dependency Version Changes
----------------------------------

Added
^^^^^
- omni.usd.metrics.assembler.usdgeom: 0.1.0

Changed
^^^^^^^
- isaacsim.app.compatibility_check: 1.1.3 -> 1.1.4
- isaacsim.exp.full: 6.0.0 -> 6.0.1
- isaacsim.replicator.agent.core: 1.6.7 -> 1.6.8
- isaacsim.sensors.rtx.calibration: 0.3.9 -> 0.3.10
- isaacsim.sensors.rtx.placement: 0.16.9 -> 0.16.10
- isaacsim.util.debug_draw: 3.2.2 -> 3.2.3
- omni.anim.behavior.ui: 110.1.3 -> 110.1.4
- omni.cip.core: 2.0.17 -> 2.0.23
- omni.cip.mega: 2.0.14 -> 2.0.18
- omni.cip.mega.scenario_payload_ui: 2.0.5 -> 2.0.6
- omni.cip.mega.ui: 2.0.14 -> 2.0.18
- omni.cip.mega.waypoints_ui: 2.0.4 -> 2.0.5
- omni.cip.pip: 2.0.1 -> 2.0.5
- omni.cip.ui: 2.0.3 -> 2.0.5
- omni.cip.workspace: 2.0.1 -> 2.0.3
- omni.cip.wrapp_ui: 2.0.1 -> 2.0.2
- omni.convexdecomposition: 110.1.11 -> 110.1.13
- omni.cuopt.examples: 1.4.1 -> 1.4.2
- omni.cuopt.service: 1.3.2 -> 1.3.3
- omni.cuopt.visualization: 1.4.1 -> 1.4.2
- omni.graph.action_nodes: 2.10.3 -> 2.11.0
- omni.graph.action_nodes_core: 2.10.2 -> 2.11.0
- omni.graph.examples.cpp: 2.10.3 -> 2.11.0
- omni.graph.nodes: 2.11.1 -> 2.12.0
- omni.graph.nodes_core: 2.10.3 -> 2.11.0
- omni.graph.telemetry: 3.10.3 -> 3.11.1
- omni.graph.ui_nodes: 2.10.5 -> 2.11.1
- omni.kit.asset_converter: 5.1.4 -> 6.0.1
- omni.kit.converter.dgn: 510.1.4 -> 510.1.5
- omni.kit.converter.dgn_core: 512.3.0 -> 512.3.3
- omni.kit.converter.hoops_core: 511.3.0 -> 511.3.2
- omni.kit.converter.jt_core: 510.1.0 -> 510.1.1
- omni.kit.property.physics: 110.1.11 -> 110.1.13
- omni.kit.stagerecorder.bundle: 110.0.0 -> 110.0.2
- omni.kit.stagerecorder.core: 110.0.9 -> 110.0.14
- omni.kit.stagerecorder.ui: 110.0.0 -> 110.0.2
- omni.kit.tool.asset_exporter: 4.0.7 -> 5.0.1
- omni.kit.tool.asset_importer: 5.2.0 -> 6.0.1
- omni.kit.variant.presenter: 107.1.3 -> 107.1.6
- omni.physics: 110.1.11 -> 110.1.13
- omni.physics.isaacsimready: 110.1.11 -> 110.1.13
- omni.physics.physx: 110.1.11 -> 110.1.13
- omni.physics.physx.ui: 110.1.11 -> 110.1.13
- omni.physics.stageupdate: 110.1.11 -> 110.1.13
- omni.physics.tensors: 110.1.11 -> 110.1.13
- omni.physics.ui: 110.1.11 -> 110.1.13
- omni.physx: 110.1.11 -> 110.1.13
- omni.physx.asset_validator: 110.1.11 -> 110.1.13
- omni.physx.bundle: 110.1.11 -> 110.1.13
- omni.physx.camera: 110.1.11 -> 110.1.13
- omni.physx.cct: 110.1.11 -> 110.1.13
- omni.physx.commands: 110.1.11 -> 110.1.13
- omni.physx.cooking: 110.1.11 -> 110.1.13
- omni.physx.demos: 110.1.11 -> 110.1.13
- omni.physx.fabric: 110.1.11 -> 110.1.13
- omni.physx.foundation: 110.1.11 -> 110.1.13
- omni.physx.gpu: 110.1.11 -> 110.1.13
- omni.physx.graph: 110.1.11 -> 110.1.13
- omni.physx.pvd: 110.1.11 -> 110.1.13
- omni.physx.supportui: 110.1.11 -> 110.1.13
- omni.physx.tensors: 110.1.11 -> 110.1.13
- omni.physx.tests: 110.1.11 -> 110.1.13
- omni.physx.tests.visual: 110.1.11 -> 110.1.13
- omni.physx.ui: 110.1.11 -> 110.1.13
- omni.physx.vehicle: 110.1.11 -> 110.1.13
- omni.replicator.core: 1.13.25 -> 1.13.27
- omni.services.convert.cad: 508.0.3 -> 508.0.4
- omni.services.core: 1.10.0 -> 1.11.0
- omni.usd.metrics.assembler.physics: 110.1.11 -> 110.1.13
- omni.usd.schema.physx: 110.1.11 -> 110.1.13
- omni.usdphysics: 110.1.11 -> 110.1.13
- omni.usdphysics.ui: 110.1.11 -> 110.1.13
- semantics.schema.property: 2.0.1 -> 2.0.2

Extensions
==========

This section lists notable functional changes — new APIs, behavior changes, and
bug fixes that affect users. Releases that only contained internal maintenance
(linter, docstring, and test-only updates) are omitted.

- **isaacsim.asset.transformer** (1.2.3 -> 1.2.5)

    - Added

      - `RuleInterface.request_deletion` / `RuleInterface.get_pending_deletions` for rules to register manager-owned working files for deletion after the manager releases its stage handle.

    - Fixed

      - `AssetTransformerManager.run` performs deferred file deletions after releasing the working stage, fixing Windows `PermissionError` when rules convert `payloads/<base>.usd` to `.usda`. The manager now drops its `base_layer` handle after asset collection and drains pending deletions after each rule.
      - `_run_deferred_deletions` is best-effort and non-fatal: it skips `Sdf.Layer.Clear()` and logs files that cannot be removed instead of failing the rule.

- **isaacsim.asset.transformer.rules** (1.7.8 -> 1.7.10)

    - Fixed

      - `GeometriesRoutingRule.process_rule` releases the rule-owned `.tmp.usda` layer handle before deleting it on the `save_base_as_usda = False` path.
      - `GeometriesRoutingRule` no longer fails with `PermissionError: [WinError 5] Access is denied` when converting `base.usd` to `.usda` on Windows. Manager-owned working files are now deleted via `RuleInterface.request_deletion` after the manager releases its stage handle, instead of in-rule `os.remove`.
      - `_create_visual_materials_scope` anchors source-layer references on `realPath` instead of `identifier`, so the `.usd` -> `.usda` rewrite on Windows updates `instances.usda` material references correctly.

- **isaacsim.benchmark.services** (4.2.1 -> 4.2.3)

    - Fixed

      - Fixed malformed `syncUsdLoads` setting path in `set_sync_mode` (was `/omni.kit.plugin/syncUsdLoads`, now `/omni/kit/plugin/syncUsdLoads`) so synchronous USD loads are correctly forced.

- **isaacsim.core.simulation_manager** (1.15.4 -> 1.15.6)

    - Changed

      - Reduce warning to an info level message when USD context or stage is not available.

- **isaacsim.core.throttling** (2.3.3 -> 2.3.5)

    - Changed

      - Replaced the `_is_replicator_capturing` run-status check with an attached-annotator ownership check so throttling defers to Replicator whenever a capture pipeline is configured.

    - Fixed

      - Async rendering no longer re-enables on timeline stop/pause while a Replicator capture pipeline is attached, even when the orchestrator is briefly stopped between steps. Toggling async rendering in that window could emit a one-sided `ASSETS_LOADING` event (NVBug-6169678) that stalled the next Replicator step for the full asset-loading timeout.

- **isaacsim.physics.newton** (0.7.14 -> 0.8.1)

    - Changed

      - Upgraded Newton pip package from 1.2.0 to 1.2.1.

- **isaacsim.physics.newton.tensors** (0.1.7 -> 0.1.9)

    - Changed

      - Updated Newton pip package to 1.2.1.

- **isaacsim.replicator.experimental.mobility_gen** (0.2.5 -> 0.2.10)

    - Added

      - Teleop support for NuRec scenes with SPG (PPISP): the chase viewport renders through the scene's authored PPISP graph.
      - Volume NuRec detection (`OmniNuRecFieldAsset` / `omni:nurec:isNuRecVolume`), in addition to particle scenes.
      - Warn on NuRec replay when `render_rt_subframes` is below the recommended value.
      - `OccupancyMap.from_ros_yaml` loads occupancy maps from Omniverse/URL paths via `omni.client`.
      - `RecordingSession`: headless build-and-record control extracted from the UI, so recordings can be driven from a script.
      - `collect_input()` (exported): caches a scene into a recording — `.usdz` byte-copied whole; `.usd`/`.usda`/`.usdc` collected via `omni.kit.usd.collect`.
      - `replay_directory.py` options: `--warmup_frames`, `--max_frames`, `--skip_completed`, `--self_contained`.

    - Changed

      - Depend on `isaacsim.replicator.nurec_utils`, deduplicating the local NuRec utilities.
      - Replay runs with multi-GPU rendering disabled.
      - Scene caching copies the input scene and its dependencies instead of flattening the stage (much faster for large scenes).

    - Fixed

      - `MobilityGenCamera.update_state`: guard depth/segmentation/normals/instance-id against empty annotator buffers (as RGB already is), avoiding a "tile cannot extend outside image" crash on replay.
      - `occupancy_map`: defer the `cv2` import to first use.

- **isaacsim.replicator.mobility_gen.ui** (0.4.4 -> 0.4.8)

    - Changed

      - Added a dependency on `isaacsim.replicator.nurec_utils`.
      - For SPG scenes the chase viewport renders through the export's authored PPISP graph via `route_chase_through_ppisp`; non-SPG scenes point the viewport at the chase camera as before.
      - Teleop build validates NuRec render prerequisites (`setup_for_rendering`) on the loaded stage and aborts with a warning notification if one is unmet (e.g. `omni.rtx.spg` not enabled), instead of recording a black scene.
      - The recording panel now drives recordings through the shared `RecordingSession`, so the UI and headless scripts build and record scenes through the same path.
      - `_cache_stage` now copies the input scene (and the files it needs) into a temporary folder before loading, then opens the stage from that copy. This removes the flatten + strip-kit-prims path and the USDZ re-export; USDZ inputs are copied as-is so every package member (including SPG `.cu.lua` launchers) is preserved, and recording start is much faster for large NuRec scenes.

- **isaacsim.replicator.nurec_utils** (0.1.2)

    - New extension

- **isaacsim.robot.experimental.wheeled_robots** (0.2.9 -> 0.2.11)

    - Changed

      - Clarify that `invert_steering` is for rear-wheel-steered robots such as forklifts.

- **isaacsim.robot.wheeled_robots.nodes** (0.1.2 -> 0.1.5)

    - Changed

      - Clarify Ackermann Controller `invertSteering` input description for rear-wheel-steered robots.

    - Fixed

      - Clarified DifferentialController velocityCommand output order and units.

- **isaacsim.robot.wheeled_robots.ui** (2.3.1 -> 2.3.3)

    - Fixed

      - Corrected Differential Controller graph shortcut joint names and indices to use left/right wheel order.
      - Supported joint index 0 by using -1 as the unset index sentinel.

- **isaacsim.ros2.core** (1.9.1 -> 1.9.4)

    - Fixed

      - Dynamic ROS 2 message publishing leaked the previous sequence buffer every tick: `Ros2DynamicMessageImpl::_setArray` re-initialized variable-length array fields without finalizing the prior allocation. Finalize before re-initializing.
      - `IPCBufferManager` destructor leaked one CUDA virtual address reservation (missing `cuMemAddressFree`) and one exported POSIX file descriptor per buffer on every teardown, and released allocation handles before unmapping them. Tear down in the documented VMM order (unmap, release, address-free) and close the exported file descriptors.
      - `camera_info_utils.compute_relative_pose`: defer the `cv2` import to first use.

- **isaacsim.ros2.nodes** (1.18.11 -> 1.18.13)

    - Fixed

      - `OgnROS2CameraInfoHelper`: defer the `cv2` import to first use.

- **isaacsim.sensors.experimental.rtx** (1.4.4 -> 1.4.6)

    - Fixed

      - `camera_utils.draw_annotator_data_to_image`: defer the `cv2` import to first use.

- **isaacsim.sensors.rtx.nodes** (0.1.0 -> 0.1.2)

    - Fixed

      - `IsaacExtractRTXSensorPointCloud` properly passes-through Cartesian point clouds.

- **isaacsim.simulation_app** (2.18.3 -> 2.18.4)

    - Added

      - Added `shutdown_watchdog_timeout` launch config option (default 120s). When fast shutdown is enabled, `close()` arms a `faulthandler`-based watchdog before `app.shutdown()` so a deadlocked Kit teardown (e.g. the carb.tasking GIL deadlock) dumps all thread stacks and force-exits instead of hanging until an external timeout. The watchdog runs on a C thread so it fires even when the main thread is wedged holding the GIL.

    - Fixed

      - Fixed malformed `syncUsdLoads` setting path in `_start_app` and `_set_render_settings` (was `omni.kit.plugin/syncUsdLoads`, now `omni/kit/plugin/syncUsdLoads`) so the `sync_loads` launch config option correctly forces synchronous USD loads as documented.

- **isaacsim.ucx.core** (1.4.2 -> 1.4.4)

    - Fixed

      - `waitForRequestWithTimeout` now treats `timeoutMs = 0` as "wait indefinitely", matching the documented OGN-node default (`"If 0, waits indefinitely"`). Previously only `g_kUcxInfiniteTimeout` (`UINT32_MAX`) was treated as the infinite sentinel; `timeoutMs = 0` fell through the polling loop on the first iteration and returned "Request timed out", causing intermittent send-side timeouts in any UCX OGN node using the default value.

- **isaacsim.ucx.nodes** (1.6.4 -> 1.6.7)

    - Changed

      - `OgnUCXPublishImage`: the image FlatBuffer's `Tensor.shape` is now `[height, width, bytes_per_pixel]` with `ndim = 3` and row-major strides, replacing the previous 1D `[dataSize]` shape. Receivers can now consume the image as a properly-shaped tensor without an external reshape step. `bytes_per_pixel` is derived as `dataSize / (height * width)` so future encodings do not require a code change here. Both the CPU path (`sendCudaBuffer = false`) and the GPU-direct metadata header (`sendCudaBuffer = true`) emit the same shape. Total byte count is still recoverable as `prod(shape)`.

    - Fixed

      - `OgnUCXCameraHelper.ogn`: the `tag` input default is now the FNV-1a 32-bit hash of `"isaac.Image"` (`270059627`), matching the convention used by the other UCX OGN publishers (`OgnUCXPublishClock`, `OgnUCXPublishJointState`, `OgnUCXSubscribeJointCommand`). Previously the default was the literal `10`, which made `UCXCameraHelper` the only UCX publisher whose default tag did not derive from its FlatBuffer schema name and required consumers to override the input to receive frames.

- **omni.pip.compute** (1.9.0 -> 1.9.2)

    - Removed

      - Removed "pynvvideocodec==2.1.0".

6.0.0 GA
========

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

- **Physics Sensors**

  - Added clean APIs for sensor authoring and runtime data collection in ``isaacsim.sensors.experimental.physics``.
  - Added a new Raycast sensor type with configurable ray origins, directions, and time offsets.
  - Deprecated the ``isaacsim.sensors.physics`` and ``isaacsim.sensors.physx`` extensions.

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

  - Reduced overhead of automatic namespace generation and ``isaac:nameOverride`` resolution on the publish path. Automatic namespace generation creates uniquely identifiable topics in multi-robot simulations, while name overrides let users customize published link names.
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

Changed: 110.0.0 -> 110.1.1

Kit SDK Dependency Version Changes
----------------------------------

Added
^^^^^
- isaacsim.anim.robot.bt_nodes: 0.1.1
- isaacsim.kit.xr.teleop.bridge: 1.1.2
- omni.ai.behavior_tree_gen.bridge: 1.0.4
- omni.ai.behavior_tree_gen.core: 1.0.2
- omni.anim.behavior.bundle: 110.1.0
- omni.anim.behavior.tree: 110.1.3
- omni.anim.behavior.ui: 110.1.3
- omni.behavior.scripting.bundle: 110.1.0
- omni.behavior.scripting.ui: 110.1.0
- omni.behavior.tree.bundle: 110.1.0
- omni.behavior.tree.ui: 110.1.12
- omni.cip.core: 2.0.17
- omni.cip.mega: 2.0.14
- omni.cip.mega.occupancy_map_ui: 2.0.7
- omni.cip.mega.scenario_payload_ui: 2.0.5
- omni.cip.mega.ui: 2.0.14
- omni.cip.mega.waypoints_ui: 2.0.4
- omni.cip.pip: 2.0.1
- omni.cip.ui: 2.0.3
- omni.cip.workspace: 2.0.1
- omni.cip.wrapp_ui: 2.0.1
- omni.kit.converter.gsplat: 0.1.14
- omni.kit.livestream.rtsp: 10.2.3
- omni.kit.thumbnails.usd: 1.0.12
- omni.mega.schema: 2.0.5
- omni.metropolis.agent_registry: 0.1.2
- omni.physx.gpu: 110.1.11
- omni.replicator.srtx: 1.1.11
- omni.warehouse.creator.api: 1.1.2
- omni.warehouse.creator.ui: 1.3.0
- omni.wrapp.package_explorer: 2.4.3

Removed
^^^^^^^
- omni.kit.widget.schema_api: 1.0.4
- omni.mesh_tools.libs: 110.0.1
- omni.simready.configuration: 1.0.1
- omni.simready.content.search: 1.0.5
- omni.simready.paths: 0.1.0
- omni.tools.array: 108.0.0

Changed
^^^^^^^
- isaacsim.anim.robot.core: 1.2.2 -> 1.4.2
- isaacsim.anim.robot.schema: 0.1.0 -> 0.1.1
- isaacsim.app.compatibility_check: 1.1.1 -> 1.1.3
- isaacsim.replicator.agent.core: 1.2.6 -> 1.6.7
- isaacsim.replicator.agent.schema: 0.1.0 -> 0.1.1
- isaacsim.replicator.agent.ui: 1.0.20 -> 1.0.36
- isaacsim.replicator.caption.core: 0.7.5 -> 0.7.10
- isaacsim.replicator.incident.core: 0.11.7 -> 0.11.8
- isaacsim.replicator.incident.ui: 0.6.3 -> 0.6.4
- isaacsim.replicator.object.core: 0.11.8 -> 0.11.12
- isaacsim.replicator.object.ui: 0.11.3 -> 0.11.5
- isaacsim.util.debug_draw: 3.2.1 -> 3.2.2
- omni.ai.langchain.agent.chat_iro: 2.2.8 -> 2.2.11
- omni.ai.langchain.core: 2.2.5 -> 2.3.1
- omni.anim.asset: 110.0.0 -> 110.1.0
- omni.anim.behavior.core: 110.0.8 -> 110.1.4
- omni.anim.behavior.schema: 110.0.1 -> 110.1.0
- omni.anim.graph.bundle: 110.0.0 -> 110.1.1
- omni.anim.graph.core: 110.0.3 -> 110.1.2
- omni.anim.graph.schema: 110.0.0 -> 110.1.1
- omni.anim.graph.ui: 110.0.1 -> 110.1.2
- omni.anim.navigation.bundle: 110.0.0 -> 110.1.0
- omni.anim.navigation.core: 110.0.3 -> 110.1.4
- omni.anim.navigation.schema: 110.0.0 -> 110.1.0
- omni.anim.navigation.ui: 110.0.2 -> 110.1.1
- omni.anim.retarget.bundle: 110.0.0 -> 110.1.0
- omni.anim.retarget.core: 110.0.3 -> 110.1.0
- omni.anim.retarget.preview: 110.0.5 -> 110.1.0
- omni.anim.retarget.ui: 110.0.1 -> 110.1.0
- omni.anim.skelJoint: 110.0.3 -> 110.1.0
- omni.anim.window.timeline: 110.0.0 -> 110.0.1
- omni.asset_validator.core: 1.11.2 -> 1.19.3
- omni.asset_validator.ui: 1.11.2 -> 1.19.3
- omni.behavior.scripting.core: 110.0.4 -> 110.1.0
- omni.behavior.tree.core: 110.0.4 -> 110.1.9
- omni.behavior.tree.schema: 110.0.1 -> 110.1.0
- omni.convexdecomposition: 110.0.7 -> 110.1.11
- omni.cuopt.visualization: 1.4.0 -> 1.4.1
- omni.flowusd: 110.0.0 -> 110.0.3
- omni.graph.action_nodes: 2.10.2 -> 2.10.3
- omni.graph.examples.cpp: 2.10.2 -> 2.10.3
- omni.graph.nodes: 2.10.2 -> 2.11.1
- omni.graph.nodes_core: 2.10.2 -> 2.10.3
- omni.graph.telemetry: 3.10.2 -> 3.10.3
- omni.graph.ui: 2.10.2 -> 2.10.3
- omni.graph.window.core: 3.10.2 -> 3.10.4
- omni.importer.onshape: 2.0.1 -> 2.0.3
- omni.kit.asset_converter: 5.1.1 -> 5.1.4
- omni.kit.browser.asset: 1.3.15 -> 1.3.16
- omni.kit.browser.core: 2.3.17 -> 2.3.18
- omni.kit.browser.folder.core: 1.12.1 -> 2.0.2
- omni.kit.converter.cad: 209.0.0 -> 209.4.0
- omni.kit.converter.common: 510.0.0 -> 510.1.3
- omni.kit.converter.dgn: 510.0.0 -> 510.1.4
- omni.kit.converter.dgn_core: 512.0.0 -> 512.3.0
- omni.kit.converter.hoops: 510.0.0 -> 510.3.0
- omni.kit.converter.hoops_core: 511.0.0 -> 511.3.0
- omni.kit.converter.jt: 509.0.0 -> 509.1.2
- omni.kit.converter.jt_core: 509.0.0 -> 510.1.0
- omni.kit.graph.delegate.modern: 1.10.11 -> 1.10.15
- omni.kit.graph.editor.core: 1.5.4 -> 1.5.8
- omni.kit.graph.usd.commands: 1.3.2 -> 1.3.6
- omni.kit.livestream.app: 10.1.0 -> 10.1.1
- omni.kit.livestream.core: 10.0.0 -> 10.2.1
- omni.kit.livestream.messaging: 1.2.1 -> 1.3.0
- omni.kit.livestream.webrtc: 10.1.2 -> 10.3.2
- omni.kit.pointclouds: 1.6.7 -> 1.6.14
- omni.kit.prim.icon: 1.1.0 -> 1.1.1
- omni.kit.profiler.tracy: 1.2.1 -> 1.2.0
- omni.kit.property.physics: 110.0.7 -> 110.1.11
- omni.kit.stagerecorder.core: 110.0.2 -> 110.0.9
- omni.kit.timeline.minibar: 1.2.14 -> 1.2.13
- omni.kit.tool.asset_exporter: 4.0.5 -> 4.0.7
- omni.kit.tool.asset_importer: 5.1.3 -> 5.2.0
- omni.kit.tool.measure: 200.0.7 -> 200.0.12
- omni.kit.waypoint.core: 1.6.4 -> 1.6.9
- omni.kit.widget.material_preview: 1.1.2 -> 1.1.3
- omni.kit.window.collection: 0.3.4 -> 0.3.5
- omni.kit.window.material_graph: 1.9.6 -> 2.2.0
- omni.kit.window.movie_capture: 2.7.4 -> 3.0.1
- omni.metropolis.pipeline: 0.0.5 -> 0.0.9
- omni.metropolis.schema: 0.0.1 -> 0.0.3
- omni.metropolis.utils: 1.0.5 -> 1.1.2
- omni.physics: 110.0.7 -> 110.1.11
- omni.physics.isaacsimready: 110.0.7 -> 110.1.11
- omni.physics.physx: 110.0.7 -> 110.1.11
- omni.physics.physx.ui: 110.0.7 -> 110.1.11
- omni.physics.stageupdate: 110.0.7 -> 110.1.11
- omni.physics.tensors: 110.0.7 -> 110.1.11
- omni.physics.ui: 110.0.7 -> 110.1.11
- omni.physx: 110.0.7 -> 110.1.11
- omni.physx.asset_validator: 110.0.7 -> 110.1.11
- omni.physx.bundle: 110.0.7 -> 110.1.11
- omni.physx.camera: 110.0.7 -> 110.1.11
- omni.physx.cct: 110.0.7 -> 110.1.11
- omni.physx.commands: 110.0.7 -> 110.1.11
- omni.physx.cooking: 110.0.7 -> 110.1.11
- omni.physx.demos: 110.0.7 -> 110.1.11
- omni.physx.fabric: 110.0.7 -> 110.1.11
- omni.physx.foundation: 110.0.7 -> 110.1.11
- omni.physx.graph: 110.0.7 -> 110.1.11
- omni.physx.pvd: 110.0.7 -> 110.1.11
- omni.physx.supportui: 110.0.7 -> 110.1.11
- omni.physx.tensors: 110.0.7 -> 110.1.11
- omni.physx.tests: 110.0.7 -> 110.1.11
- omni.physx.tests.visual: 110.0.7 -> 110.1.11
- omni.physx.ui: 110.0.7 -> 110.1.11
- omni.physx.vehicle: 110.0.7 -> 110.1.11
- omni.replicator.core: 1.13.4 -> 1.13.25
- omni.replicator.nv: 1.1.0 -> 1.1.1
- omni.scene.optimizer.analysis: 110.0.4 -> 110.1.0
- omni.scene.optimizer.bundle: 110.0.4 -> 110.1.0
- omni.scene.optimizer.core: 110.0.4 -> 110.1.0
- omni.scene.optimizer.ui: 110.0.4 -> 110.1.0
- omni.scene.optimizer.validators: 110.0.4 -> 110.1.0
- omni.services.client: 0.5.4 -> 0.5.6
- omni.services.convert.asset: 510.0.0 -> 510.0.2
- omni.services.convert.cad: 508.0.0 -> 508.0.3
- omni.services.core: 1.9.3 -> 1.10.0
- omni.services.pip_archive: 0.18.6 -> 0.18.7
- omni.simready.content.browser: 0.2.4 -> 0.3.7
- omni.usd.fileformat.e57: 1.7.0 -> 1.7.4
- omni.usd.fileformat.pts: 108.0.0 -> 110.0.2
- omni.usd.metrics.assembler: 110.0.0 -> 110.1.2
- omni.usd.metrics.assembler.physics: 110.0.7 -> 110.1.11
- omni.usd.metrics.assembler.ui: 110.0.0 -> 110.1.1
- omni.usd.schema.metrics.assembler: 110.0.0 -> 110.1.0
- omni.usd.schema.physx: 110.0.7 -> 110.1.11
- omni.usdex.libs: 2.2.1 -> 2.2.2
- omni.usdphysics: 110.0.7 -> 110.1.11
- omni.usdphysics.ui: 110.0.7 -> 110.1.11
- omni.warehouse_creator: 0.4.4 -> 1.0.0
- omni.warp.core: 1.12.0 -> 1.13.0

Extensions Changelog Summary
----------------------------

Please refer to the individual extension changelogs for more detailed
information. A handful of cross-cutting changes landed in many extensions this
release; rather than repeat them per extension, they are called out once here:

- Many extensions were migrated onto the Core Experimental API
  (``isaacsim.core.experimental.*``), ``isaacsim.core.simulation_manager``, and
  ``isaacsim.core.rendering_manager``, replacing the deprecated
  ``isaacsim.core.api`` and ``isaacsim.core.utils`` dependencies.
- The Newton physics backend is supported more broadly: importers, prims, and
  robot policies now author Newton schemas (``NewtonArticulationRootAPI``,
  ``NewtonMimicAPI``) and select the Newton-compatible USD physics variant when
  Newton is the active engine. The matching ``PhysxArticulationAPI`` /
  ``PhysxMimicJointAPI`` authoring is dropped from importer and rule output;
  the runtime consumes the Newton schemas directly.
- Multitick rendering is enabled across the RTX sensor, ROS 2, UCX, and
  ``SimulationApp`` pipelines, with the corresponding non-multitick code paths
  removed. Multitick simulation time is now communicated via the
  ``/ExternalSimulationTime`` Fabric prim instead of the previous
  ``set_next_simulation_time`` / ``SWHExternalSimulationTime`` event API.
- The deprecated ``omni.isaac.ml_archive`` dependency was removed from many
  extensions; the extension itself is now marked deprecated and its bundled
  PyTorch was updated to 2.11.0+cu128 (torchvision 0.26.0+cu128, torchaudio
  2.11.0+cu128).
- Python binding modules across many extensions were moved into ``bindings/``
  subdirectories. The public Python import paths (for example
  ``isaacsim.core.experimental.prims.bindings._<name>``) shift accordingly;
  downstream code importing from the old top-level binding location needs to
  be updated.
- Menu registrations across many extensions migrated from the deprecated
  ``onclick_fn`` to ``onclick_action``, and many extensions moved to the shared
  UI library (``isaacsim.gui.components``).
- Common documentation refreshes (``Overview.md``, ``python_api.md``,
  ``SETTINGS.md``, docstrings) landed across many extensions; individual
  extensions do not re-list these.

- **isaacsim.app.about**

    - Changed

      - Redesigned the About dialog: removed the OK button (dismiss via the titlebar), aligned header rows, simplified the plugin list, restyled the hover tooltip, and fixed the clipped OK button and the clipboard "Kit SDK Version" separator.

- **isaacsim.app.setup**

    - Added

      - Emit a telemetry event for app startup duration via ``isaacsim.core.telemetry``.

    - Removed

      - Removed the ``isaacsim.core.telemetry`` dependency and direct telemetry calls from app startup (the event is now emitted indirectly).

- **isaacsim.asset.exporter.urdf**

    - Added

      - Round-trip drive breadcrumbs: ``isaac:source_drive`` XML comments preserve DriveAPI gains (stiffness, damping, max force, target position), MjcActuator parameters, and ``PhysxJointAPI`` armature across URDF export and import.

    - Changed

      - Rewritten as a physics-graph-driven converter (``UsdToUrdfConverter``).
      - Switched to codeless PhysX schema usage; uses direct ``prim.ApplyAPI()`` / ``prim.CreateAttribute()`` calls instead of ``pxr.PhysxSchema`` typed-API classes.
      - ``matrix4_to_origin`` now decomposes the matrix via ``Gf.Transform`` so roll-pitch-yaw is computed from the unscaled rotation; ``ExtractRotation`` on a scaled matrix produced incorrect angles.
      - Split into an API extension (this) and a UI extension (``isaacsim.asset.exporter.urdf.ui``); removed the ``nvidia-srl-usd-to-urdf`` dependency.

    - Fixed

      - DriveAPI values no longer incorrectly populate URDF ``<dynamics>``, ``<limit effort>``, or ``<calibration reference_position>``; these elements now only contain passive joint properties per the URDF-to-USD concept mapping.
      - Preserve mesh scale when exporting instanceable geometry containers; the scale is emitted on the URDF ``<mesh scale=...>`` attribute instead of being dropped.
      - Replaced ``Usd.Prim.GetAncestorsRange`` (C++-only API) with a ``GetParent`` walk in mesh prototype path resolution; the previous code raised ``AttributeError`` whenever a non-instanced mesh was exported.

- **isaacsim.asset.exporter.urdf.ui**

    - New extension

- **isaacsim.asset.gen.conveyor**

    - Added

      - ``create_conveyor_belt`` public Python API as a direct replacement for the ``CreateConveyorBelt`` Kit command.

    - Deprecated

      - ``CreateConveyorBelt`` Kit command, in favor of ``create_conveyor_belt()``.

    - Fixed

      - Conveyor texture animation is now restored on stop. The StopPlay handler in ``OgnIsaacConveyor::initInstance`` performs the restore synchronously from the event callback (subscribing to ``omni::timeline::kGlobalEventStop``); the previous deferred ``requestCompute`` flow silently dropped the restore. Regression introduced in the Kit 107.3 event-dispatcher migration.
      - Eliminated an off-by-one frame drift on stop by gating the texture-animation block in ``OgnIsaacConveyor::compute()`` on a new ``m_isPlaying`` flag set from the StartPlay / StopPlay callbacks.
      - ``create_conveyor_belt`` now applies ``UsdPhysics.MeshCollisionAPI`` with the ``convexHull`` approximation on ``UsdGeomMesh`` prims, so PhysX accepts the resulting dynamic body instead of rejecting the default ``meshSimplification`` approximation.
      - Emit a one-shot ``CARB_LOG_WARN`` when ``IStageReaderWriter`` is unavailable so the FSD-mirror fallback to USD-only authoring is observable in logs.

- **isaacsim.asset.gen.conveyor.ui**

    - Changed

      - Replaced ``omni.kit.commands.execute("CreateConveyorBelt")`` call sites with direct ``create_conveyor_belt()`` API.
      - Replaced the MDL "Ghost" / "GhostVolumetric" preview material with a viewport selection group tinted green via ``omni.usd.UsdContext.register_selection_group``.

    - Removed

      - ``data/Ghost.mdl`` and ``data/GhostVolumetric.mdl`` (no longer referenced).
      - ``mdl_file`` argument to ``ConveyorBuilderWidget.__init__`` and the matching ``Extension.mdl_file`` plumbing.

- **isaacsim.asset.gen.omap**

    - Fixed

      - Fixed the ``compute_coordinates()`` return type annotation from ``np.matrix`` to ``np.ndarray`` and replaced the deprecated ``np.matrix`` with ``np.array`` and the ``@`` operator.

- **isaacsim.asset.gen.omap.ui**

    - Changed

      - UI improvements: unified filename field, auto-updating YAML, and the window docks to the Property panel.

- **isaacsim.asset.importer.heightmap**

    - Changed

      - The heightmap ground plane is now sized from the generated occupancy map's world-space bounds (via ``UsdGeom.BBoxCache``) and created after the heightmap instances, so it always covers the geometry.

    - Fixed

      - ``SetDefaultPrim`` no longer fails when ``/World`` does not exist; it is created automatically.
      - The heightmap importer no longer crashes on grayscale images (PIL modes ``L``, ``I``, ``F``) that produce 2D NumPy arrays.
      - Raise ``ValueError`` for non-PIL heightmap inputs before modifying the stage, and propagate image-processing failures instead of silently returning an empty heightmap (6132964).
      - Show the file picker after the Load Image button creates it, unblocking PNG selection from the UI (6083539).

- **isaacsim.asset.importer.mjcf**

    - Added

      - Over-constrained joints (multiple single-axis joints sharing a body pair) are combined into a single PhysX D6 joint in the PhysX variant; the MuJoCo/Newton variants keep per-DOF authoring. The redundant single-axis joints are removed from the PhysX variant; all edits stay in the PhysX overlay layer.
      - ``MJCFImporterConfig.fix_base`` is now a tri-state ``bool | None``: ``True`` adds a world-to-root fixed joint, ``False`` makes the robot floating-base, and the new default ``None`` leaves the source asset's base authoring untouched.

    - Changed

      - Added ``omni.usd.schema.mujoco`` and ``omni.hydra.usdrt_delegate`` dependencies.
      - Updated ``mujoco-usd-converter`` to 0.2.0.
      - Imported MJCF articulation roots no longer carry ``PhysxArticulationAPI``; self-collision is authored via ``NewtonArticulationRootAPI`` (``newton:selfCollisionEnabled``) on top of the standard ``UsdPhysics.ArticulationRootAPI``.
      - Imported MJCF mimic joints are now expressed exclusively through ``NewtonMimicAPI`` (``newton:mimicJoint``, ``newton:mimicCoef0``, ``newton:mimicCoef1``); ``PhysxMimicJointAPI`` is no longer authored.
      - Replaced the Kit extension-manager lookup for the default profile path with the new ``isaacsim.asset.transformer.rules.DEFAULT_PROFILE_PATH`` constant.
      - Intermediate artifacts (usdex layers, temp stage) are written to a system temp directory via ``tempfile.mkdtemp()`` in non-debug mode, avoiding ``PermissionError`` when importing from read-only locations.
      - ``MassAPI`` is only added when a non-default density is set on a link; links with no mass no longer have a ``MassAPI`` applied.
      - Only ``MeshCollisionAPI`` (not ``PhysxArticulationAPI``) is now authored on articulation roots; gates ``extension.py`` so the package can be imported outside Kit.
      - Added a deprecation notice to ``commands_api.md`` for ``MJCFCreateImportConfig`` and ``MJCFCreateAsset`` Kit commands.

    - Fixed

      - Fixed a ``SIGSEGV`` crash in ``UsdStage::~UsdStage`` between tests by stopping the timeline and flushing run-loop frames in teardown.
      - With ``run_asset_transformer=False``, ``import_mjcf()`` no longer crashes writing to a non-existent output directory. The intermediate stage is only materialized when the transformer needs it.

- **isaacsim.asset.importer.mjcf.ui**

    - Added

      - "Base Type" dropdown in the Options frame with three choices (Source / Fixed / Mobile) that drives the new tri-state ``MJCFImporterConfig.fix_base`` field.

    - Changed

      - Multi-file selection and import in the UI.
      - Robot Type dropdown.
      - Updated treeview identifier to ``filebrowser_grid_view``.

    - Fixed

      - Multi-select import now builds an independent ``OptionWidget`` / config / models per selected MJCF file, so edits to one file's panel no longer bleed into another's settings.

- **isaacsim.asset.importer.urdf**

    - Added

      - Round-trip drive, geometry, and joint reconstruction from ``isaac:source_*`` breadcrumb comments restores DriveAPI gains, capsule/cone primitives, and multi-DOF joints (SphericalJoint, D6Joint) on import.
      - ``URDFImporterConfig.fix_base`` is now a tri-state ``bool | None`` (fixed / floating-base / source as-is).

    - Changed

      - Imported URDF articulation roots no longer carry ``PhysxArticulationAPI``; self-collision is authored via ``NewtonArticulationRootAPI`` (``newton:selfCollisionEnabled``).
      - Imported URDF mimic joints are now expressed exclusively through ``NewtonMimicAPI``.
      - Updated ``urdf-usd-converter`` to v0.1.2.
      - Replaced ``pxr.PhysxSchema`` typed-API usage in the drive reconstruction module with direct ``prim.ApplyAPI()`` / ``prim.CreateAttribute()`` calls.
      - Replaced the Kit extension-manager lookup for the default profile path with ``isaacsim.asset.transformer.rules.DEFAULT_PROFILE_PATH``.
      - When the merged URDF is relocated to a temp directory, relative ``<mesh filename="..."/>`` entries are rewritten to absolute paths so downstream mesh resolution is preserved (``package://`` URIs are left untouched).
      - Intermediate artifacts are written to a system temp directory in non-debug mode, avoiding ``PermissionError`` from read-only locations.
      - Mass API authoring follows the MJCF importer behavior (only applied when a non-default density is set).

    - Fixed

      - Fixed a ``SIGSEGV`` crash in ``UsdStage`` teardown between tests.
      - With ``run_asset_transformer=False``, ``import_urdf()`` no longer crashes writing to a non-existent output directory.

- **isaacsim.asset.importer.urdf.ui**

    - Added

      - "Base Type" dropdown (Source / Fixed / Mobile) driving the tri-state ``URDFImporterConfig.fix_base`` field.
      - Auto-populate the ROS package table from ``package://`` references found in the selected URDF.
      - ``package_scanner`` module that resolves ``package://`` URIs to filesystem paths by walking parent directories.

    - Changed

      - Multi-file selection and import in the UI.
      - Moved ``checkbox_builder`` / ``dropdown_builder`` / ``string_filed_builder`` imports to ``isaacsim.gui.components.ui_utils``.
      - Replaced local style definitions with the shared base style from ``isaacsim.gui.components.style``.

    - Fixed

      - Multi-select import now builds an independent config per selected URDF, so edits no longer bleed across files or ROS package tables.

- **isaacsim.asset.importer.utils**

    - Added

      - ``apply_floating_base`` helper in ``asset_utils`` (the inverse of ``apply_fix_base``) that removes any ``FixedJoint`` anchoring the articulation root to the world.
      - ``parse_robot_name`` helper in ``importer_utils`` for validating the input file extension and parsing the name.
      - Collapse multiple single-axis joints sharing a body pair into a single PhysX D6 joint; remove the redundant joints from the PhysX variant.
      - File conflict / collision checks during import.

    - Changed

      - Added ``__all__`` to ``asset_utils`` and added ``create_robot_schema`` / ``ROBOT_TYPE_TOKENS`` to ``importer_utils.__all__`` so the package re-exports match ``config/python_api.md``.
      - ``apply_link_density()`` now applies ``MassAPI`` to rigid-body links that lack it before authoring density, so callers no longer need a separate ``add_rigid_body_schemas()`` pass; links with an authored positive ``physics:mass`` are still skipped.
      - ``enable_self_collision`` marks articulation roots with ``UsdPhysics.ArticulationRootAPI`` plus ``NewtonArticulationRootAPI`` (``newton:selfCollisionEnabled``) instead of writing ``physxArticulation:enabledSelfCollisions`` / ``PhysxArticulationAPI``. The PhysX schema enums remain available for code that reads existing data.
      - Replaced ``pxr.PhysxSchema`` typed-API usage with direct ``prim.ApplyAPI()`` / ``prim.CreateAttribute()`` calls across the importer utility modules.
      - Deferred ``isaacsim.asset.transformer`` import to ``run_asset_transformer_profile()`` to remove a module-level cross-extension dependency.
      - ``importer_utils.add_rigid_body_schemas()`` is retained for backward compatibility but will be removed in the future.

    - Removed

      - ``create_physx_mimic_joint`` helper from ``importer_utils``; URDF and MJCF importers now leave joints as ``NewtonMimicAPI``. The ``PhysxMimicAttr`` / ``PhysxMimicRel`` / ``PhysxSchema.MIMIC_JOINT_API`` enums remain available for code that reads existing PhysX mimic data (for example the URDF exporter).

- **isaacsim.asset.transformer**

    - Changed

      - Documented the input-stage mutation contract on ``RuleInterface``: ``args["input_stage"]`` is informational only and must be treated as fully read-only, including its session layer. Rules that need to author overrides while reading from the original input must open a private ``Usd.Stage`` from ``args["input_stage_path"]`` and author into that stage's session layer. The contract avoids mid-frame Hydra invalidations when the transformer runs against the editor's active stage.
      - Removed direct Omni / carb dependencies.

    - Fixed

      - ``AssetTransformerManager._collect_assets`` now anchors dependency discovery and asset-path remapping to the source layer's directory instead of the freshly-exported output layer, so relative asset paths (for example ``../textures/foo.png``) are rewritten correctly regardless of where the output ``payloads/`` directory sits.
      - ``_collect_assets`` resolves relative asset paths against a priority-ordered list of candidate anchor directories (source root layer first, then every used sublayer's directory), fixing the multi-sublayer case where an asset path authored in a sublayer was anchored at the wrong directory.
      - ``_collect_assets`` skips URI-style asset paths (``omni://``, ``http://``, ``file://``, ...) in its remap step rather than attempting filesystem-relative resolution.
      - ``make_explicit_relative`` normalizes backslash separators to forward slashes so USD asset paths, sublayer identifiers, and references are portable across platforms.

- **isaacsim.asset.transformer.rules**

    - Added

      - New rules: ``MergeMeshRule`` (merge visual mesh prims grouped under rigid bodies via Scene Optimizer), ``MjcToPhysxConversionRule`` (convert MJCF actuator/joint attributes to PhysX drive and joint schemas), ``UrdfToMjcPhysxConversionRule`` (convert URDF joint attributes to MJCF actuators and PhysX schemas), ``JointStateAPIRule`` (apply ``PhysxSchema.JointStateAPI`` to non-fixed joints missing it; wired into the Isaac Sim profile between Fix Physics Joint Poses and Route Materials).
      - ``DEFAULT_PROFILE_PATH`` module-level constant exposing the path to the bundled ``isaacsim_structure.json`` profile.
      - ``register_all_rules()`` standalone function for registering all built-in rules without Kit's extension lifecycle.
      - ``discover_rule_classes()`` helper that walks the extension package and returns every concrete ``RuleInterface`` subclass.
      - ``GeometriesRoutingRule`` quantizes hashed geometry values to a physical 1 mm grid derived from the stage's ``metersPerUnit`` and the mesh's extent magnitude, so meshes authored in m, cm, or mm deduplicate at the same resolution instead of relying on raw float-string comparison. Large arrays (points, normals, UVs) are quantized via NumPy in C.
      - ``GeometriesRoutingRule`` tracks a global ``used_geometry_names`` set so newly emitted geometry names cannot collide with pre-existing entries when deduplication is enabled.
      - ``MakeListsNonExplicitRule`` now normalizes ``isaac:physics:robotLinks`` and ``isaac:physics:robotJoints`` relationships to ``prepend`` list ops, walking each prim's ``GetPrimStack()`` so sublayered PrimSpecs are also rewritten.
      - ``canonical_builtin_mdl_path`` helper that returns the Kit-resolvable bare/suffix form of a built-in MDL path.
      - ``refresh_builtin_mdl_cache_async`` helper for best-effort upgrade of the built-in MDL cache from ``omni.kit.material.library.get_mdl_list_async``; the Kit extension awaits this on startup, standalone callers can ignore it.
      - ``omni.kit.material.library`` declared as an ``optional = true`` dependency so the rules extension is usable without the material library.
      - ``visibility`` added to ``_INSTANCE_SPECIFIC_PROPERTIES`` so it is no longer baked into the geometry hash.

    - Changed

      - ``MjcToPhysxConversionRule`` and ``UrdfToMjcPhysxConversionRule`` no longer author ``PhysxMimicJointAPI`` from joints with ``NewtonMimicAPI``; the runtime consumes ``NewtonMimicAPI`` directly.
      - ``PrimRoutingRule.process_rule()`` now raises ``ValueError`` when ``prim_types`` is unconfigured (missing, ``None``, or empty) instead of silently logging and returning ``None``. Disable a rule with ``enabled = false`` instead.
      - ``is_builtin_mdl`` and ``canonical_builtin_mdl_path`` consult an in-memory cache initialized from a hardcoded fallback at import time and upgraded by ``refresh_builtin_mdl_cache_async`` when available. The previously public ``BUILTIN_MDL_FILES`` / ``BUILTIN_MDL_PATH_SUFFIXES`` constants are replaced by private fallbacks.
      - ``register_all_rules()`` now discovers rule implementations dynamically via ``discover_rule_classes()`` instead of a hard-coded list.
      - ``GeometriesRoutingRule._compute_geometry_hash`` ignores xform properties and replaces ``str(value)`` hashing with a unit-aware quantization via ``_quantize_value``.
      - No longer deletes ``PhysxMimicJointAPI`` and articulation roots by default in the Isaac Sim profile JSON.

    - Fixed

      - ``FlattenRule.process_rule`` no longer mutates any caller-owned USD state. It now opens a fresh private ``Usd.Stage`` from ``args["input_stage_path"]`` and authors variant blocks/selections through ``Usd.EditContext``, fixing a ``librtx.hydra`` crash (``Unable to find RP Prim from previous update pass!``) when the Asset Transformer was run against the editor's active stage.
      - ``GeometriesRoutingRule._compute_instance_delta_hash`` now incorporates the effective inherited purpose so a prototype mesh referenced by both a visual Xform (``purpose=default``) and a collision Xform (``purpose=guide``) is split into separate ``/Instances`` entries.
      - ``GeometriesRoutingRule`` propagates the effective purpose computed via ``UsdGeom.Imageable.ComputePurpose()`` instead of only the immediate parent's authored value, so collision meshes whose ``purpose=guide`` is authored on an ancestor stay hidden through the routed instance.
      - ``GeometriesRoutingRule._make_references_non_instanceable`` no longer writes the flattened stage back to the source layer's ``realPath`` on disk; idempotency of the full Isaac Sim profile is preserved.
      - ``MaterialsRoutingRule`` rewrites absolute or explicit-relative paths to project-local copies of Kit built-in MDLs into their canonical bare form (for example ``OmniPBR.mdl``), so Kit's MDL search paths resolve them.
      - ``MaterialsRoutingRule`` no longer duplicates local texture files when the target path already exists with identical content (``files_are_identical`` short-circuits the rename loop).
      - ``MaterialsRoutingRule`` writes asset paths with forward-slash separators on Windows via ``make_explicit_relative``.
      - ``MergeMeshRule``, ``MjcToPhysxConversionRule``, and ``UrdfToMjcPhysxConversionRule`` are now registered with the global ``RuleRegistry``.
      - ``is_builtin_mdl`` now recognizes ``omnisurfacepresets.mdl``, ``core_definitions.mdl``, and path-suffix forms like ``nvidia/core_definitions.mdl``.
      - ``JointStateAPIRule`` no longer imports ``pxr.PhysxSchema``; it uses shared PhysX schema tokens from ``isaacsim.asset.importer.utils`` so standalone wheel imports do not require Kit-only schema bindings.
      - Added the standalone ``isaacsim.asset.importer.utils`` wheel dependency required by the rule token helper.

- **isaacsim.asset.transformer.ui**

    - Added

      - New extension dependency: ``omni.kit.window.file`` (the Save / Save As implementation already shipped in the standard Isaac Sim app; the dependency is now declared explicitly).
      - Shared modal-slot helpers (``_dismiss_active_modal`` / ``_build_modal_window``) so modals are reliably destroyed (not just hidden) when replaced.
      - ``_save_active_stage_and_run`` thin wrapper around ``omni.kit.window.file.save`` that re-invokes ``_run_actions`` from its completion callback (and surfaces an error dialog on save failure).

    - Changed

      - ``_is_active_stage_unsaved()`` returns ``True`` for both never-saved stages and previously-saved stages with pending in-memory edits (``omni.usd.get_dirty_layers(stage, recursive=True)`` non-empty), because the transformer reads from disk.
      - ``_resolve_input_stage_path()`` returns ``(path, error_message)`` so the caller can render the specific failure reason in the UI.
      - ``_show_confirmation_dialog()`` accepts optional ``confirm_label`` / ``cancel_label`` and uses a fixed button width (``ui.Pixel(120)``) instead of a character-count heuristic that broke under custom fonts, high DPI, and non-Latin glyphs.

    - Fixed

      - A cancelled or failed save now surfaces an error dialog instead of silently aborting.
      - ``_run_actions()`` no longer returns silently when the active stage is unsaved, when no actions are configured, when the output directory is unset, or when ``AssetTransformerManager.run()`` raises; each failure opens a modal dialog.
      - Per-rule failures returned by ``ExecutionReport.results`` are now surfaced via the same error dialog (capped at 10 entries with an "...and N more" suffix).
      - Unsaved-stage precheck shows a terse "Save Stage?" Yes / No / Cancel dialog before doing anything else.

- **isaacsim.asset.validation**

    - Changed

      - Added ``DedupBaseRuleChecker`` to filter duplicate errors and warnings caused by multiple variants.
      - Removed a redundant ``fetch_results()`` after ``simulate()`` when collecting initial collider pairs in physics validation rules.

    - Fixed

      - ``RigidBodyHasMassAPI`` no longer crashes on rigid bodies missing ``MassAPI`` or the required mass attributes; missing-attribute errors are collected up front. It also no longer flags unauthored ``principalAxes`` on assets that fall back to the schema default.
      - ``HasArticulationRoot``, ``JointsExist``, and ``LinksExist`` only fire on stages that actually contain joints.
      - ``NonAdjacentCollisionMeshesDoNotClash`` skips pairs where either collider is outside the ``defaultPrim`` subtree (filters out ground planes) and walks to the nearest ``RigidBodyAPI`` ancestor for adjacency lookup, fixing false positives on nested collision layouts.
      - Fixed antipodal-quaternion matching in ``JointHasCorrectTransformAndState``.
      - Fixed false positives in drive-joint and collision-mesh-purpose rules.
      - Repaired the failing validator dedup mixin test.
      - Physics layer naming rules now accept the transformer output naming convention.

- **isaacsim.benchmark.services**

    - Added

      - Physics-step-interval recorder tracking the duration between physics update steps.
      - Support for warmup frames when starting a benchmarking phase.
      - ``rtf_stability`` recorder: windowed real-time factor (sim time / wall time) with mean/stdev. Controlled by ``/exts/isaacsim.benchmark.services/rtf_stability/window_wall_ms`` and ``/exts/isaacsim.benchmark.services/rtf_stability/export_window_samples``; default wall window 100 ms.
      - ``rtf_stability`` derived metrics: percent of windows within ±0.01 / ±0.10 of the phase mean windowed RTF.

    - Changed

      - Multitick validation features (timestamp tolerance, golden directory management) added to ``validation.py``.
      - Frametime metric sample trimming is now disabled by default.

- **isaacsim.code_editor.jupyter**

    - Changed

      - Added internal token-based authentication to prevent code execution by unauthenticated sources.

    - Fixed

      - ``from __future__ import annotations`` no longer shadows the ``__future__`` module.
      - Replaced mutable default arguments in ``Executor.__init__`` with ``None`` defaults.
      - ``SystemExit`` and ``BaseException`` subclasses in user code are now caught and returned as errors instead of crashing the application.

- **isaacsim.code_editor.python_server**

    - Added

      - Fire-and-forget mode (``"fire_and_forget": true`` in the envelope) returns an immediate ``{"status": "ok", "fire_and_forget": true, "task_id": "<uuid>"}`` and runs the code in the background; results are retained for up to 100 tasks (FIFO eviction) and retrievable via introspection.
      - Introspection endpoint (``{"introspect": "<command>"}``) for ``contexts``, ``context``, ``tasks``, ``task``, ``delete_context``, ``status``.
      - JSON envelope protocol: ``{"code": ..., "args": ..., "timeout": ..., "context": ..., "fire_and_forget": ...}``. Raw Python source is also accepted; a JSON-looking-but-invalid payload falls back to raw execution.
      - Keepalive elapsed time via the ``keepalive_interval`` setting (adds an ``elapsed_seconds`` field to the response when set and execution exceeds the interval).
      - Named execution contexts keyed by a string; the default context (``""``) preserves existing behaviour and each context is an independent persistent globals namespace.
      - Per-request execution timeout (``timeout`` in the envelope or the ``execution_timeout`` setting). Async code uses ``asyncio.wait_for``; sync code uses a background watchdog timer. Returns ``{"status": "error", "ename": "TimeoutError", ...}``.
      - New settings: ``execution_timeout`` (default ``0``), ``keepalive_interval`` (default ``0``), and ``require_auth`` / ``auth_token``. When authentication is required and no token is configured, the server generates one at startup.
      - Token authentication via the ``auth_token`` JSON envelope field or the ``# isaacsim-python-server-token:`` raw-source header.
      - New test suites ``test_advanced_features.py`` and ``test_protocol_robustness.py`` covering all new features and TCP fragmentation handling.

    - Fixed

      - Async user code (for example ``create_new_stage_async``, ``update_app_async``) no longer raises ``RuntimeError: Cannot enter into task`` on Python 3.12+. Replaced ``create_task(_await_and_reply)`` with manual coroutine stepping via ``_drive_coroutine()`` so user code never runs inside an asyncio Task.
      - TCP data is buffered until EOF instead of processing on first ``data_received`` call, preventing partial execution of fragmented payloads.
      - ``print()`` output from awaited coroutines is captured in the JSON response ``output`` field instead of being lost to real stdout.
      - ``RecursionError`` and ``MemoryError`` in user code no longer hang the server; exception handlers are resilient to secondary failures.
      - Replaced ``run_coroutine_threadsafe`` with ``ensure_future`` in ``data_received`` and scheduled execution via ``call_soon`` outside the transport's ``_read_ready`` callback to avoid ``cannot enter context`` errors on Python 3.12+.
      - ``SystemExit`` and ``sys.exit()`` in user code are caught and returned as errors instead of crashing the application.

- **isaacsim.code_editor.vscode**

    - Fixed

      - Eliminated a shell-injection risk by resolving ``code`` via ``shutil.which()`` and removing ``shell=True``.
      - Show a Kit warning notification when VS Code cannot be launched because ``code`` is not available on the system.

- **isaacsim.core.api**

    - Changed

      - ``ParticleMaterial`` ``lift`` / ``drag`` parameters, setters, and getters are now no-ops with deprecation warnings (PhysX removed ``physxPBDMaterial:lift`` / ``physxPBDMaterial:drag``).
      - Removed the ``cloth.py`` standalone example, the deprecated deformable/cloth/particle tests, and the deformable-body/cloth API implementations (replaced by error stubs; PhysX removed these features).
      - Updated ``PhysicsContext`` to use the renamed PhysX attribute ``GpuMaxDeformableVolumeContacts``.

    - Deprecated

      - Extension deprecated in favor of the Core Experimental extensions ``isaacsim.core.experimental.*``.

    - Fixed

      - Extensive correctness fixes (60+) across ``ArticulationController``, ``BaseTask``, ``PhysicsContext``, ``PhysicsMaterial``, ``Robot``/``RobotView``, ``Scene``/``SceneRegistry``, ``SimulationContext``, ``World``, and the example tasks (``FollowTarget``, ``PickPlace``, ``Stacking``). Common patterns include: missing returns after ``carb.log_error``, getters silently applying schemas as a side effect, NaN handling in ``apply_action``, wrong keyword (``position=`` vs ``translation=``) in ``set_local_pose`` calls, raising the documented ``RuntimeError`` instead of leaking ``AttributeError`` when called before ``initialize()``, and several incorrect default values / annotations in docstrings.
      - ``ArticulationController.get_applied_action`` / ``switch_control_mode`` / ``switch_dof_control_mode`` now raise the documented ``RuntimeError`` when called before ``initialize()`` (6132508).
      - ``PhysicsContext.get_gravity`` no longer crashes when the physics scene or gravity attribute is ``None``; ``PhysicsContext.set_gravity`` no longer rejects zero magnitude (preserves downward direction); ``PhysicsContext.set_solver_type`` no longer accepts invalid strings; ``PhysicsContext.enable_stabilization`` is now correctly spelled (6014961, 6036079, 6036084, 6060122).
      - ``SimulationContext.add_physics_callback`` registers callbacks as pre-step instead of post-step (6035957). ``SimulationContext.render`` no longer skips fabric initialization when ``current_time == 0`` (6035943). ``SimulationContext.get_physics_context()`` returns ``RuntimeError`` with an actionable message instead of ``None`` before ``reset_async()``.

- **isaacsim.core.cloner**

    - Fixed

      - Handle zero-clone grid requests and invalidate cached grid transforms when the clone count changes.
      - Initialize cloner listener state before listener enable/disable calls.
      - Restore USD / Fabric change listeners when cloning exits with an exception.
      - Validate clone source prim paths before calling USD bindings.

- **isaacsim.core.deprecation_manager**

    - Fixed

      - ``import_module`` no longer leaves the module unstubbed when an optional dependency (for example ``torch``) is missing.
      - Skip ``exit_app`` during stub generation to prevent Kit shutdown when optional dependencies are missing.

- **isaacsim.core.experimental.actuators**

    - New extension

- **isaacsim.core.experimental.materials**

    - Added

      - Non-visual material.

- **isaacsim.core.experimental.primdata**

    - New extension

- **isaacsim.core.experimental.prims**

    - Added

      - Filterless contact API capturing all contacts for prims, plus ``ContactPointData``, ``ContactEventData``, ``ContactReportData`` structs and contact event type constants (``kContactEventFound`` / ``Lost`` / ``Persist``) in ``IPrimDataReader.h``.
      - ``enableContactReporting()`` / ``getContactReport()`` virtual methods on the ``IPrimDataReader`` interface.
      - ``SdfPathToken.h`` with ``sdfPathToToken`` / ``tokenToSdfPath`` helpers for PhysX contact body identifiers.
      - Bumped ``CARB_PLUGIN_INTERFACE`` version to ``(2, 2)``.
      - Remote-simulator (``remotesim``) support for articulation DOF target writes; ``Articulation._deferred_switch_remotesim()`` switches engines after the PhysX prim query completes and is invoked from ``_on_physics_ready``.
      - Tests verifying ``Articulation`` link, joint, and DOF names and indices are non-empty before physics initialization and match the post-physics enumeration for fixed-base and floating-base assets.

    - Changed

      - Decoupled the prim-data-reader interface from its implementation (implementation moved to ``isaacsim.core.experimental.primdata``).
      - Added a configurable provider extension setting and lazy provider loading to enable the primdata extension on-the-fly.
      - Use ``SimulationManager.get_active_physics_engine()`` for Newton engine detection in ``RigidPrim`` and ``Articulation`` instead of checking for a ``_newton_stage`` attribute on the view object.
      - Quaternion reorder index array ``[6, 3, 4, 5]`` is cached per device at module level to avoid repeated allocation on ``get_world_poses`` / ``get_coms`` / ``set_world_poses`` / ``set_coms``.
      - ``Articulation.get_dof_*`` and ``get_world_poses`` / ``get_velocities`` skip Warp fancy-indexing when ``indices=None`` and ``dof_indices=None`` (guarded for heterogeneous safety).
      - Improve the exception message related to xformOp reset status.
      - Added tests for the PhysX tensor-backed world transform path in ``IPrimDataReader``.

    - Fixed

      - ``XformPrim.__init__`` no longer raises ``TypeError`` for non-root articulation links (the offending ``raise carb.log_warn(...)`` is now a plain ``carb.log_warn(...)``).
      - Populate ``Articulation`` metadata from USD when running with the ``remotesim`` backend.
      - Resolve descendant articulation targets to their containing articulation root.
      - Switch to the ``remotesim`` engine when other physics engines are still active, even if ``remotesim`` is already marked active.
      - Removed the obsolete SimState remote-push gate so articulation DOF commands continue writing to ``SimStateStorage`` when SimState mode is enabled.
      - Remove unused ``unitsResolve`` properties (other than ``xformOp:scale:unitsResolve``) when resetting transformation operation attributes.
      - Fixed the link mass inverse test to not add epsilon to the denominator.

- **isaacsim.core.experimental.utils**

    - Added

      - ``compute_relative_transform`` (transform utils, world matrices) and ``get_relative_transform`` (xform utils, USD prims).
      - ``look_at_matrix`` to compute a USD camera transform (``Gf.Matrix4d``) from eye and target positions, with automatic collinearity fallback.
      - ``upgrade_prim_semantics_to_labels`` for migrating deprecated ``Semantics.SemanticsAPI`` to ``UsdSemantics.LabelsAPI``.
      - ``SimStateMode`` enum and ``get_simstate_mode()`` for SimState backend selection.

    - Changed

      - **Breaking:** ``euler_angles_to_quaternion`` and ``euler_angles_to_rotation_matrix`` now expect ``[roll, pitch, yaw]`` (XYZ) input order for both extrinsic and intrinsic conventions, enabling clean euler-to-quaternion-to-euler round trips.
      - Cache ``arange`` index arrays globally in ``ops.resolve_indices`` (keyed by ``(count, dtype, device)``) so repeated ``x=None`` calls across callers reuse the same Warp array without re-allocating.

- **isaacsim.core.includes**

    - Added

      - ``PhysicsEngine.h`` header with ``getActivePhysicsEngineName()`` to query the active physics simulation backend.
      - ``BindingsPythonUtils.h`` header for pybind11 bindings utilities.

    - Changed

      - ``Transforms.h`` uses ``getActivePhysicsEngineName()`` for simulation-view creation instead of defaulting to ``nullptr``.

    - Fixed

      - Added Doxygen ``@cond`` to hide the internal template ``QuatFromAxisAngle`` in ``Quat.h``.
      - Added warning logs when rigid-body APIs fail.

- **isaacsim.core.nodes**

    - Changed

      - ``IsaacCreateRenderProduct`` supports SRTX render-product creation and reusing existing render products via the ``renderProductPrim`` input.
      - ``OgnIsaacComputeOdometry`` and ``OgnIsaacComputeTransformTree`` use ``getActivePhysicsEngineName()`` to select the simulation backend dynamically instead of hardcoding ``"physx"``.
      - ``IsaacComputeTransformTree`` caches parent world poses and uses quaternion math (instead of ``GfMatrix4d``) for relative-transform computation, improving performance.
      - ``OgnIsaacComputeOdometry`` calls ``update()`` on the articulation/rigid-body view at the start of each physics tick to flush pending PhysX data before reading transforms and velocities.
      - ``OgnIsaacComputeTransformTree`` resolves ``isaac:nameOverride`` lazily at compute time, reads physics poses from the active backend, composes non-physics prims from cached USD local transforms, and only resizes output arrays when the pair count changes.
      - Switched to ``app_utils.update_app_async(...)`` in tests for multitick compatibility.

    - Fixed

      - ``IsaacComputeTransformTree`` applies a 180° X-axis rotation for ``UsdGeomCamera`` prims to convert USD camera convention to ROS optical frame.
      - ``IsaacArticulationController`` rejects command arrays whose length does not match the explicit joint selection, skips ``NaN`` entries instead of reading previous targets, validates all three command arrays atomically, and promotes silent ``db.log_warn`` failures to ``db.log_error`` with the prim path and exception text (6109472, 6113767, 6114423).
      - ``OgnIsaacComputeOdometry`` binds ``chassisPrim`` to a rigid-body view whenever the prim has ``UsdPhysicsRigidBodyAPI`` (even if it also has ``UsdPhysicsArticulationRootAPI``), fixing incorrect odometry when Robot Assembler extends the articulation graph and shifts PhysX's auto-selected root onto a non-chassis link.
      - ``OgnIsaacComputeOdometry`` walks ``isaac:physics:robotLinks`` to find a link with the appropriate physics API when ``chassisPrim`` carries ``IsaacRobotAPI`` but not ``UsdPhysicsRigidBodyAPI`` / ``UsdPhysicsArticulationRootAPI``.
      - ``OgnIsaacComputeTransformTree`` reconstructs kinematic topology from ``isaac:physics:robotJoints`` when expanding ``IsaacRobotAPI`` targets so the emitted TF tree mirrors the joint graph instead of parenting every link to world.
      - ``OgnIsaacComputeTransformTree`` refines the ``IsaacRobotAPI`` fallback via ``isaacsim.robot.schema``'s ``GetAllRobotComponents`` helper, skips self-loops, and applies the ROS optical-frame rotation to camera-sites.
      - ``OgnIsaacJointNameResolver`` no longer prints garbled memory in error messages (pass ``state.m_robotPath.c_str()`` rather than the ``std::string`` itself); descends the prim hierarchy when the supplied ``targetPrim`` / ``robotPath`` lacks ``UsdPhysicsArticulationRootAPI``.
      - ``OgnOnPhysicsStep`` uses the generic ``IPhysicsSimulation`` API instead of the PhysX-specific ``IPhysx`` API for physics-step event subscriptions, enabling OmniGraph execution with any physics backend.

- **isaacsim.core.prims**

    - Changed

      - Cloth and deformable prim implementations replaced with error stubs (PhysX removed these features).
      - Joint or DOF indices can now be specified when accessing data via the ``joint_names`` parameter, with the last one set as the default option.
      - Updated ``ParticleSystem`` for the renamed PhysX attribute and updated the return types of the ``RigidPrim`` annotations.

    - Deprecated

      - Extension deprecated in favor of the Core Experimental extension ``isaacsim.core.experimental.prims``.

    - Fixed

      - Extensive correctness fixes (60+) across ``Articulation``, ``GeometryPrim``, ``RigidPrim``, ``XFormPrim``, ``Prim``, ``SdfShapePrim``, ``SingleArticulation``, ``SingleRigidPrim``, and ``ParticleSystem``. Common patterns: missing return after the not-initialized guard; getters silently applying ``UsdPhysics.*`` / ``PhysxSchema.*`` APIs as a side effect; ``RigidPrim`` USD-fallback gravity boolean inverted; ``Articulation.apply_action`` / ``set_joint_efforts`` zeroing unspecified joints when partial ``joint_indices`` were passed; ``RigidContactView.__init__`` missing the ``disable_stabilization`` parameter (6042901); ``RigidPrim`` ``len()`` on Warp arrays (use ``shape[0]``); 4 ``GeometryPrim`` contact-force methods missing ``| None`` in their return annotations.
      - ``Prim._on_prim_deletion`` no longer falsely invalidates wildcard views (the ``.*`` regex matched ``/``).
      - ``XFormPrim.set_world_poses(usd=False)`` no longer destroys non-uniform scale; ``XFormPrim.get_local_scales`` no longer returns ``NaN`` when a prim has no ``xformOp:scale``.
      - Default state is re-converted when the backend changes after initialization (for example automatic numpy-to-torch switch for GPU pipelines).

- **isaacsim.core.rendering_manager**

    - Added

      - ``_ensure_fabric_simulation_time`` class method to seed the ``/ExternalSimulationTime`` Fabric prim for the multitick renderer.

    - Changed

      - ``ViewportManager.set_camera_view`` now delegates look-at matrix computation to ``look_at_matrix`` from ``isaacsim.core.experimental.utils.transform``.

    - Fixed

      - ``RenderingManager.set_dt()`` now updates Fabric's default simulation-period settings (``/app/settings/fabricDefaultSimPeriodNumerator`` and ``/app/settings/fabricDefaultSimPeriodDenominator``) along with USD/timeline timing. Kit reads these defaults when creating Fabric history stages, so newly-created caches use a render-product period matching the requested rendering dt instead of Fabric's 1/30 s default.
      - ``test_callback`` no longer asserts an exact 1:1 mapping between ``RenderingManager.render_async()`` calls and ``NEW_FRAME`` dispatches.

- **isaacsim.core.simulation_manager**

    - Added

      - ``"remotesim"`` is supported in ``get_active_physics_engine()`` and ``switch_physics_engine()``, including a ``PhysicsScene`` wrapper branch in ``create_scene()``.
      - Optional multitick support: ``TimeSampleStorage`` and the plugin interface use physics time to drive rendering time via the ``onPhysicsStep`` callback.

    - Changed

      - Multitick simulation time is communicated via the ``/ExternalSimulationTime`` Fabric prim instead of via the previous ``set_next_simulation_time`` API.
      - Refactored the stage event subscription to be lazily initialized with null-safety checks for USD context and stage.
      - Route Newton simulation-view creation through ``omni.physics.tensors.create_simulation_view`` with ``backend="newton"`` instead of the Python ``isaacsim.physics.newton.tensors`` implementation.
      - Stop unconditionally applying ``PhysxSceneAPI`` in C++ ``UsdNoticeListener`` / ``PluginInterface``; the API is now applied by the engine-specific Python wrapper (``PhysxScene``).
      - Remove stale solver APIs (``PhysxSceneAPI``, ``MjcSceneAPI``, ``NewtonXpbdSceneAPI``) and re-create physics scene wrappers in ``SimulationManager._on_engine_switched()`` when switching engines.
      - When available, use integer time steps per second and step count to compute simulation time in the ``onPhysicsStep`` callback to eliminate accumulated bias from float timestep precision.
      - ``IPhysicsSimulation::getSimulationTimeStepsPerSecond()`` now returns the authoritative value, so the USD-attribute workaround in ``onPhysicsStep`` is removed.
      - ``PhysicsScene.get_dt()`` / ``set_dt()`` dispatch based on ``PhysxSceneAPI`` presence on the prim instead of querying the active engine.
      - Use local ``BindingsPythonUtils.h`` from ``isaacsim.core.includes`` instead of ``carb/BindingsPythonUtils.h``.
      - Removed the Newton pip prebundle dependency.

    - Removed

      - Removed the non-multitick code path.

    - Fixed

      - Add missing ``@staticmethod`` decorator to 5 internal event callbacks (``_on_simulation_registry_event``, ``_on_stage_opened``, ``_on_stage_closed``, ``_on_play``, ``_on_stop``).
      - Fix simulation time using stale steps-per-second from the physics runtime when the rate is changed between stop/play cycles. Read the authoritative value from ``PhysxSceneAPI::timeStepsPerSecond`` instead of relying on the cached ``IPhysicsSimulation::getSimulationTimeStepsPerSecond()``.
      - Raise ``RuntimeError`` in ``PhysicsScene.set_dt()``, ``set_enabled_gravity()``, and ``set_max_solver_iterations()`` when ``NewtonSceneAPI`` is not applied, matching the ``PhysxScene`` error-handling pattern.
      - Restore mode-specific ``TimeSampleStorage`` handling for render-product reference times (multitick vs non-multitick).
      - Route base ``PhysicsScene`` timestep updates to the active engine so PhysX scenes do not author Newton timestep values that can hang playback.

- **isaacsim.core.throttling**

    - Fixed

      - Async rendering is now disabled after the timeline play callback returns, preventing hangs when play-on-load examples start simulation while async rendering is enabled.
      - Async rendering no longer re-enables on timeline pause / stop while Replicator is capturing with attached annotators, preventing skipped writer frames.

- **isaacsim.core.utils**

    - Deprecated

      - Extension deprecated in favor of the Core Experimental extension ``isaacsim.core.experimental.utils``.

    - Fixed

      - Extensive correctness fixes (40+) across math, transform, stage, and prim utilities. Common patterns: zero-vector and zero-magnitude guards (``normalize()``, ``rotational_distance_single_axis()``, ``lookat_to_quatf()``); recursion on deep hierarchies (``_get_world_pose_transform_w_scale()``); crash-on-missing-prim or empty input (``compute_aabb``, ``compute_combined_aabb``, ``get_mesh_vertices_relative_to``, ``recompute_extents``); O(N²) BFS/DFS concatenation in ``get_all_matching_child_prims`` / ``get_first_matching_child_prim``; ``eval()`` security risk in ``set_prim_attribute_value()`` replaced with ``getattr`` resolution; ``save_stage()`` no longer destroys the existing USD file before content is committed.
      - Added the scalar-first ``(w, x, y, z)`` quaternion convention to the ``tf_matrix_from_pose`` docstring.
      - Preserve Warp quaternion conversion input device placement for CPU and CUDA arrays (6035739).
      - Stop treating valid semantic labels as incorrect merely because they are absent from the prim path (6036025).

- **isaacsim.cortex.behaviors**

    - Deprecated

      - Extension deprecated. Will be replaced in 7.0 with simple examples and open-source equivalents.

- **isaacsim.cortex.examples**

    - New extension

- **isaacsim.cortex.framework**

    - Changed

      - Added the missing ``isaacsim.robot.manipulators`` dependency; removed the unused ``isaacsim.robot.manipulators.examples`` dependency.

    - Deprecated

      - Extension deprecated. Will be replaced in 7.0 with simple examples and open-source equivalents.

    - Fixed

      - ``MotionCommand.__init__`` type annotation for ``approach_params`` corrected from ``Optional[np.ndarray]`` to ``Optional[ApproachParams]``.

- **isaacsim.examples.browser**

    - Changed

      - The detail view mirrors a file browser: a category shows its directly-registered examples plus a folder tile for each immediate sub-category. Double-clicking a folder tile drills the tree selection into that sub-category.
      - Each ``ExampleCategoryItem`` owns its examples directly, removing the previous flat-dict / string-prefix lookup in ``get_detail_items``.

    - Fixed

      - Added missing ``asyncio`` and ``omni.kit.app`` imports in ``property_delegate.py``; the dynamic thumbnail-resize callback no longer raises ``NameError``.
      - 6130501: Example browser detail panel was empty when clicking a synthetic parent category whose examples were only registered under sub-categories.

- **isaacsim.examples.extension**

    - Deprecated

      - Extension deprecated in favor of the ``repo.sh template`` CLI system (``./repo.sh template new``); moved to ``source/deprecated/``.

- **isaacsim.examples.interactive**

    - Added

      - Docstring deprecation plus runtime warnings; use ``isaacsim.examples.base`` instead.

    - Changed

      - Added ``isaacsim.robot_motion.cumotion`` and ``isaacsim.robot_motion.experimental.motion_generation`` dependencies.
      - Updated imports to use ``isaacsim.robot.experimental.manipulators.examples``; removed dependencies on Cortex.
      - Moved the ``base_sample`` module to the ``isaacsim.cortex.examples`` extension.
      - Updated Surface Gripper example to resolve the reverse-console functionality.

- **isaacsim.examples.ipc**

    - New extension

- **isaacsim.examples.ui**

    - Fixed

      - 6107587: Example UI window content overflowed on normal displays, hiding the lower frames. Window content is wrapped in a ``ui.ScrollingFrame`` with the vertical scrollbar always on, and the window is given an explicit default ``height=600``.

- **isaacsim.gui.components**

    - Changed

      - UI tweaks for the file icon.
      - Updated UI utility functions based on requirements from Isaac Sim importers.

    - Fixed

      - Eliminated shell-injection risk in ``on_open_IDE_clicked`` by resolving ``code`` via ``shutil.which()`` and removing ``shell=True``.
      - Eliminated shell-injection risk in ``on_open_folder_clicked`` by replacing ``subprocess.Popen(["start", ...], shell=True)`` with ``os.startfile()`` on Windows.
      - 6105784: ``SearchListItemModel.filter_text()`` crashed with ``AttributeError`` when callers passed a list or tuple. Added ``_normalize_search_filter_text()`` to coerce ``None``, ``list``, and ``tuple`` inputs to a single string before splitting.
      - ``StateButton.is_in_a_state()`` returns ``False`` (not ``None``) when not in state A; ``StateButton`` now guards against identical text for states A and B.
      - Widened ``style.get_style()`` return type to ``dict[str, Any]`` to accurately describe the ``"Tooltip"`` entry (a tuple of style dicts).

- **isaacsim.gui.content_browser**

    - Added

      - Added the Robot Multiphysics folder.

    - Changed

      - Added ``isaacsim.storage.native`` as a dependency.
      - Resolve content browser folder paths relative to ``persistent.isaac.asset_root.default`` instead of hardcoding full URLs.
      - Updated the USD Search API endpoint.
      - Use ``omni.simready.content.browser`` default settings instead of overriding them.

- **isaacsim.gui.menu**

    - Changed

      - Migrate extension implementation to the Core Experimental API.

    - Fixed

      - Help menu: ``OpenUSD Reference Guide``, ``Warp Getting Started``, and ``Warp Documentation`` now render reliably in ``isaacsim.exp.full.kit``. The actions and ``MenuItemDescription`` entries are registered locally instead of binding to ``source=`` items not provided by the app's dependency closure.

- **isaacsim.gui.property**

    - Added

      - New Joint Inspector window (``Tools > Robotics > Joint Inspector``): a searchable, dockable joint table with PhysX / MuJoCo backend toggles, per-axis columns, multi-row editing, and a ``Save to Robot Layer`` button (``SaveRobotSchemaToRobotLayer``).
      - Column catalogue across five groups tagged by backend: ``Joint Limits``, ``Drives``, ``Performance Envelope``, ``Joint State``, ``MuJoCo Joint``; column selection persists across robot switches.
      - Array Properties widget supports editing ``string[]`` and ``token[]`` USD attributes alongside the existing scalar/vector numeric arrays.
      - Added ``Attachment Point API`` to the Robot Schema UI menu.
      - ``JointInspectorWindowManager`` supports multiple concurrent windows via the ``+ New Inspector`` button.
      - Joint-name filter is a single rounded input with ``fnmatch`` wildcards over joint name and full path.
      - Per-axis columns collapse to one when every joint authors at most one axis; fan out only for multi-DOF ``D6Joint``.
      - Isaac API schemas registered with Kit's ``MultiSchemaPropertiesWidget.__known_api_schemas`` to prevent Extra Properties duplication.
      - ``RobotAPIWidget`` rewritten with Figma-style layout, editable attribute fields, drag-reorderable Robot Joints / Robot Links, and a ``force_update`` toggle.

    - Changed

      - Robot-schema widget registrations now use ``collapsed_by_default=True``.

- **isaacsim.gui.sensors.icon**

    - Added

      - Recognize ``IsaacRaycastSensor`` for icon display.

    - Changed

      - Marked ``Lidar``, ``IsaacLightBeamSensor``, and ``Generic`` as deprecated in the ``SENSOR_TYPES`` list (kept for backward compatibility).
      - Updated the test default prim type from the deprecated ``Generic`` to ``IsaacContactSensor``.

- **isaacsim.hsb.core**

    - New extension

- **isaacsim.hsb.nodes**

    - New extension

- **isaacsim.physics.newton**

    - Added

      - ``CTRL_DIRECT`` actuator PD control via the tensor API, bridging ``set_dof_stiffnesses`` / ``set_dof_dampings`` / ``set_dof_position_targets`` to MuJoCo actuator parameters (``gainprm``, ``biasprm``, ``ctrl``) and setting ``biastype=AFFINE``, so robot policies (for example Go2) work with Newton when USD uses ``mujoco:actuator`` rather than ``physics:driveAPI``.
      - Document Newton asset compatibility limitations and workarounds.
      - Perform a device check before running simulation in ``simulation_manager`` to prevent double initialization when the device changes.
      - Regression tests for Newton initialization error handling; unit test exercising imported URDF and MJCF asset behavior on both PhysX and Newton.

    - Changed

      - Updated Newton pip dependencies to ``newton 1.2.0rc3``, ``mujoco-warp 3.8.0.2``, ``newton-usd-schemas 0.2.0``.
      - Updated tensor frontend import paths for the ``omni.physics.tensors`` package restructuring.
      - Contact-force scaling in the tensor view uses ``SimulationManager.get_physics_dt()`` instead of the Newton stage ``sim_dt``.
      - ``get_simulation_time_steps_per_second`` returns ``int`` rather than ``float`` to comply with ``omni.physics.core`` bindings.

    - Removed

      - Removed the ``isaacsim.core.utils`` dependency.

    - Fixed

      - Added ``cleanup_stale_newton_index`` to ``FabricManager`` to remove leftover ``newton:index`` from prims no longer tracked as dynamic bodies; bounds checking added in ``set_fabric_transforms`` to skip out-of-range body indices.
      - ``shape_gap`` default for static colliders corrected from 0.1 m to 0.0.
      - Stale model references fixed in all tensor view classes (``NewtonSimView``, ``ArticulationSet``, ``RigidBodySet``, ``RigidContactSet``, and their frontend wrappers).
      - Unbounded growth of ``contact_callbacks`` and ``step_callbacks`` lists fixed by replacing tombstone lists with dict-based storage, so unsubscribed slots are reclaimed and iteration is O(active callbacks).
      - Forward the user-provided ``dt`` into ``simulate()`` when recording the CUDA graph so step times match the requested timestep.
      - MuJoCo solver: run ``Model.collide`` once per ``simulate()`` when ``use_mujoco_contacts`` is false, skip Newton collide when true, and call ``SolverMuJoCo.update_contacts`` after every ``simulate()`` so ``contacts.force`` and related fields match the solved MuJoCo state.
      - Newton contact tensor API: apply force sign convention in net and matrix kernels (add for shape0, subtract for shape1) so net contact forces match PhysX expectations.
      - Populate contact points from MuJoCo world-space positions when Newton Contacts do not provide ``rigid_contact_point0/1``.
      - Resolve pre-physics articulation link, joint, and DOF metadata by parsing the USD subtree with Newton's importer, so ``Articulation.dof_names`` and indices are available before physics is initialized and match the post-initialization order. Results are cached per ``(stage_id, prim_path)`` and invalidated on stage close.
      - Route ``set_dof_actuation_forces`` / ``get_dof_actuation_forces`` through ``control.joint_f`` so applied joint efforts drive the simulation.
      - Run the first simulation step without CUDA graph capture so Warp's link-time optimization compilation for ``tile_matmul`` / ``tile_cholesky`` does not get recorded into a bad graph.
      - Try to load USD with a flattened stage when composition cycles are present.
      - Use the Newton collision pipeline as the default instead of MuJoCo.

- **isaacsim.physics.newton.tensors**

    - New extension

- **isaacsim.pip.newton**

    - Added

      - Added ``coacd 1.0.7`` for convex-decomposition support.

    - Changed

      - Updated ``newton`` to 1.2.0, ``mujoco`` to 3.8.0, ``mujoco-warp`` to 3.8.0.3, ``newton-usd-schemas`` to 0.2.0, ``mujoco-usd-converter`` to 0.2.0, ``cbor2`` to 5.9.0, ``imgui-bundle`` to 1.92.601, ``absl-py`` to 2.4.0, and ``etils`` to 1.13.0 (pinned for Python 3.10 build tool compatibility).
      - Removed the ``newton-actuators`` dependency.

- **isaacsim.replicator.behavior**

    - Changed

      - The property-window refresh is dispatched via the new ``isaacsim.replicator.behavior.EXPOSED_VARS_CHANGED`` carb event (subscribed to by ``isaacsim.replicator.behavior.ui``), so the core behaviors can run headless. The ``omni.kit.window.property`` dependency is dropped from the core extension.
      - Clarified ``LocationRandomizer`` docstrings for ``frame:useRelativeFrame`` and ``frame:targetPrimPath``.

    - Fixed

      - ``_setup`` is now idempotent in ``TextureRandomizer``, ``RotationRandomizer``, ``LocationRandomizer``, ``LightRandomizer``, and ``LookAtBehavior``. A play/pause/play loop previously re-cached the already-randomized state as "initial" and restored stale values on stop (for example pallets left bound to a removed randomizer material and rendered gray). Prim resolution, initial-state caching, and material creation now run only on the first entry of a play session; exposed variables are still re-read on every call.
      - ``LightRandomizer._reset`` skips cached ``inputs:intensity`` / ``inputs:color`` values that were unauthored at setup time and logs a warning instead of writing ``None`` back to the prim.
      - ``TextureRandomizer._apply_behavior`` skips the tick with a warning when no texture URLs are configured.
      - ``decompose_rotation`` supports single-axis ``xformOp:rotateX|Y|Z`` ops and raises ``ValueError`` for unsupported rotation orders.

- **isaacsim.replicator.behavior.ui**

    - Added

      - Guarded the ``omni.kit.window.property`` import so the UI extension can be imported in headless contexts.
      - Subscribe to ``isaacsim.replicator.behavior.EXPOSED_VARS_CHANGED`` and refresh the property window when exposed variables are created or removed; replaces the direct ``omni.kit.window.property.request_rebuild()`` calls.

- **isaacsim.replicator.domain_randomization**

    - Changed

      - Added extension-structure validation files (``README.md``, ``isaac-sim.svg``, OGN node ``CategoryDefinition.json`` files).

- **isaacsim.replicator.episode_recorder**

    - New extension

- **isaacsim.replicator.episode_recorder.ui**

    - New extension

- **isaacsim.replicator.examples**

    - Added

      - Multiple-captures with toggled render product while the timeline is running test.

    - Changed

      - Augmentation examples now use custom event-based randomization.
      - SDG GeomSubset semantic segmentation test added for ``perSubsetSegmentation`` true/false.
      - SDG deformables test now compares semantic segmentation labels instead of images.
      - Tests now store results in uniquely-named temp directories to avoid run-to-run test pollution.
      - Enable multitick in all tests.

- **isaacsim.replicator.experimental.domain_randomization**

    - Changed

      - Registered OGN nodes under the ``isaacsim.replicator.domain_randomization`` namespace with backward-compatibility bridges for deprecated context, views, and simulation context.

    - Fixed

      - ``OgnWritePhysicsArticulationView`` no longer raises ``KeyError`` when randomizing tendon attributes on robots with no fixed tendons.
      - Module-level physics view state is now cleaned up on stage close/reload, fixing stale views accumulating across sessions.

- **isaacsim.replicator.experimental.mobility_gen**

    - Added

      - ``MobilityGenMultiSensorRobot`` and ``MobilityGenSensorRig`` for YAML-driven multi-sensor robots; camera rendering is supported, other sensor types (lidar, IMU, radar) are discovered but not yet rendered.
      - ``generate_sensor_rigs.py`` script to discover sensor prims in a robot USD and scaffold ``sensor_rig:`` YAML blocks.
      - Camera calibration overrides (intrinsics, distortion, extrinsics) made in the UI are persisted to ``sensor_overrides.usda`` at recording time and re-applied during replay.
      - ``nurec_overrides`` module exporting ``is_nurec_stage`` and ``apply_nurec_replay_overrides``. Detects NuRec stages by traversing for ``ParticleField`` prims; when detected, forces replay flags to the supported subset (RGB only) and re-asserts ``/rtx/rtpt/gaussian/skipTonemapping/enabled = False``.
      - ``sensor_overrides.py`` module with ``save_sensor_overrides``, ``apply_sensor_overrides``, ``log_camera_properties``.

    - Changed

      - ``state/common/`` steps are now saved as ``.npz`` (named arrays) instead of ``.npy`` (pickled dict); use ``migrate_recordings.py`` to convert older recordings.
      - ``replay_directory.py`` invokes ``apply_nurec_replay_overrides`` after each ``load_scenario`` so per-recording flag overrides take effect before render-product attachment.

    - Fixed

      - Recordings are now self-contained, fixing broken texture/material references on replay when the source scene used external assets.
      - ``GridPoseSampler.sample_px`` falls back to full-map uniform sampling when the selected grid block has no freespace (fixes a ``ValueError: high <= 0`` crash).
      - ``KeyboardButton._event_callback`` / ``KeyboardDriver._event_callback`` return ``True`` for handled WASD events so Kit's ``carb.input`` stops propagating them to focused text fields (fixes buffered ``wwww...`` appearing in text fields after teleoperation).
      - ``MobilityGenRobot.update_state`` caches PhysX joint-index and quaternion-reordering arrays and removes a redundant ``get_world_poses()`` call; ``get_pose_2d`` replaces ``quaternion_to_euler_angles().numpy()`` with direct ``np.arctan2`` yaw, eliminating per-step GPU-to-CPU sync.
      - ``MobilityGenWriter.write_state_dict_common`` offloads npz disk flush to a background thread with a bounded queue (``max_pending=8``).
      - ``OccupancyMap`` precomputes ``_freespace_mask_cache`` at construction and eliminates a duplicate ``world_to_pixel_numpy`` call.
      - Test runner: converted test classes from ``unittest.TestCase`` to ``omni.kit.test.AsyncTestCase`` so tests are awaitable; ``np.load`` mmap handles fixed on Windows to allow tempdir cleanup.

- **isaacsim.replicator.grasping**

    - Fixed

      - ``get_gripper_joint_states`` returns POSIX joint keys on Windows (replaced ``os.path.relpath`` with a string slice).
      - ``simulate_physics_async`` and ``simulate_physics_with_forces_async`` restore the PhysX scene's original ``updateType`` (or clear it if it was unauthored) via ``try/finally`` instead of permanently leaving the scene set to ``Disabled``.

- **isaacsim.replicator.grasping.ui**

    - Fixed

      - Set explicit checkbox / label widths so checkboxes are reliably toggled via the Omniverse Kit API.

- **isaacsim.replicator.mobility_gen.examples**

    - Added

      - YAML robot configs (``carter.yaml``, ``jetbot.yaml``, ``h1.yaml``, ``spot.yaml``) and concrete ``CarterMultiSensorRobot``, ``JetbotMultiSensorRobot``, ``H1MultiSensorRobot``, ``SpotMultiSensorRobot``; new ``WheeledMultiSensorRobot`` and ``PolicyMultiSensorRobot`` base classes.
      - ``generate_sensor_rigs.py`` script (same as in the core extension) to scaffold ``sensor_rig:`` YAML blocks.

    - Changed

      - Force USD payload loading before ``Articulation`` initialization to ensure ``ArticulationRootAPI`` is visible.
      - Migrated to ``isaacsim.core.experimental.prims`` (``Articulation``) in place of ``isaacsim.core.prims``.

    - Fixed

      - ``RandomAccelerationScenario.step``: removed a redundant ``update_state()`` call after ``write_action()``.

- **isaacsim.replicator.mobility_gen.ui**

    - Changed

      - Migrated from the deprecated ``isaacsim.replicator.mobility_gen`` to ``isaacsim.replicator.experimental.mobility_gen``.
      - Replaced ``objects.GroundPlane`` (``core.api``) with ``GroundPlane`` from ``isaacsim.core.experimental.objects``.
      - Replaced ``set_active_viewport_camera`` with ``ViewportManager.set_camera``.
      - Replaced legacy world-based simulation control with ``SimulationManager`` and the ``SimulationEvent.PHYSICS_POST_STEP`` callback.
      - Use ``save_stage`` without the deprecated ``save_and_reload_in_place`` argument.

    - Fixed

      - Call ``save_sensor_overrides`` on recording start to persist camera calibration changes made in the UI.
      - Use ``export_as_stage`` when caching the scene stage to prevent black images on replay.

- **isaacsim.replicator.synthetic_recorder**

    - Changed

      - S3 checkbox bound directly to ``backend_type`` (single source of truth); the legacy ``use_s3`` flag is still honored when loading old configs.

    - Fixed

      - "Use S3" UI checkbox now actually switches the backend (previously a no-op and recordings silently fell back to disk).
      - ``backend_params`` is rebuilt from scratch on Start so toggling Disk / S3 no longer leaks stale keys into ``backend.initialize()``.

- **isaacsim.replicator.teleop**

    - New extension

- **isaacsim.replicator.teleop.ui**

    - New extension

- **isaacsim.replicator.writers**

    - Changed

      - Marked the ``PytorchListener`` and ``PytorchWriter`` implementations as deprecated.

    - Fixed

      - ``invert_fisheye_polynomial`` now logs a warning with the residual and iteration count when Newton-Raphson fails to converge within ``max_iterations``, instead of silently returning the last iterate.
      - ``project_pinhole`` returns the screen center for camera points whose homogeneous ``w`` is near zero, preventing a divide-by-zero crash when projecting points on the camera's projection plane.

- **isaacsim.robot.experimental.manipulators.examples**

    - New extension

- **isaacsim.robot.experimental.wheeled_robots**

    - Added

      - ``WheeledRobot`` integration test with kinematic distance assertion; directional sanity test for pure-forward command.

    - Changed

      - Removed ``[::-1]`` reversal in ``HolonomicController`` to match the new ``[roll, pitch, yaw]`` euler-angle convention.

    - Fixed

      - Added missing public property accessors on ``HolonomicRobotUsdSetup`` (``wheel_radius``, ``wheel_positions``, ...).
      - Fixed the euler-angle convention bug in ``HolonomicController`` that reversed motion direction.
      - Raise ``ValueError`` (instead of a cryptic ``TypeError``) when ``HolonomicController`` is constructed without ``wheel_radius`` / ``wheel_positions`` / ``wheel_orientations`` / ``mecanum_angles``.
      - Raise a clear ``ValueError`` when ``WheeledRobot`` is constructed without wheel DOF names or indices.
      - Raise an error when ``quintic_polynomials_planner()`` cannot find a trajectory satisfying acceleration and jerk constraints.
      - Reject non-finite ``normalize_angle()`` inputs instead of looping indefinitely.

- **isaacsim.robot.manipulators**

    - Deprecated

      - Extension deprecated in favor of ``isaacsim.robot.experimental.manipulators.examples``.

    - Fixed

      - Added a ``None`` guard in ``ParallelGripper.post_reset`` to prevent a crash when called before ``initialize()``.
      - ``PickPlaceController.__init__`` and ``reset`` now reject ``events_dt`` with fewer than 10 entries.

- **isaacsim.robot.manipulators.examples**

    - Deprecated

      - Extension deprecated in favor of ``isaacsim.robot.experimental.manipulators.examples``.

    - Removed

      - ``FrankaExperimental``, ``FrankaPickPlace``, ``Franka Stacking (experimental)``, ``UR10Experimental``, ``UR10FollowTarget``, ``UR10 Stacking (experimental)``, and the interactive pick-place / follow-target UI extensions moved to ``isaacsim.robot.experimental.manipulators.examples``.

- **isaacsim.robot.manipulators.ui**

    - Deprecated

      - Extension deprecated in favor of ``isaacsim.robot.experimental.manipulators.examples``.

- **isaacsim.robot.policy.examples**

    - Added

      - Newton can be used as a physics backend.
      - Standing test for the Go2 policy that holds a zero command and asserts the robot remains upright.
      - Unit tests covering the snapshot / restore helpers in ``isaacsim.robot.policy.examples.interactive.utils``, plus per-example roundtrip tests for Quadruped, Go2, and Humanoid.

    - Changed

      - Extracted the snapshot / restore physics-state logic shared by the interactive Quadruped, Go2, and Humanoid examples into ``isaacsim.robot.policy.examples.interactive.utils``.
      - Defer the ``torch`` import to avoid loading it at startup.
      - Set ``reset_xform_op_properties=True`` when instantiating the ``Articulation``.

    - Fixed

      - Apply ``PhysxArticulationAPI`` to the articulation root prim in ``PolicyController._set_articulation_props`` if missing, avoiding ``Empty typeName`` USD errors when the asset's Physics variant does not author the API.
      - Fix physics-variant selection to match USD variant names case-insensitively (resolves H1 robot loading failure when the variant set uses ``Physx`` instead of ``physx``); log a warning when the requested ``Physics`` variant is not declared.
      - Select the USD ``Physics`` variant from ``SimulationManager.get_active_physics_engine()`` so the Newton-compatible variant is chosen when Newton is active.
      - Select the asset's ``Physics`` variant before constructing the ``Articulation`` in ``PolicyController.__init__`` so ``UsdPhysics.ArticulationRootAPI`` is authored on a descendant prim before root resolution.
      - Restore the prior physics sim device and fabric state in the cleanup paths of the interactive examples so the PhysX direct-GPU API flag is not left enabled (which previously caused ``PxArticulationJointReducedCoordinate::setDriveTarget`` errors in subsequent sessions).
      - Register ``isaacsim.robot.policy.examples.robots`` as a public module in the extension manifest.
      - Spot fall-over issue in example resolved by reverting the physics dt to 500 Hz.

- **isaacsim.robot.poser**

    - Changed

      - Cold-start IK ladder attempts now run concurrently on a ``concurrent.futures.ThreadPoolExecutor``; latency is bounded by the slowest single solve instead of the sum of all attempts (the LM solver and ``chain.compute_fk`` are stateless with respect to the chain).
      - ``RobotPoser.apply_pose`` accepts either ``dict[str, float]`` (legacy) or a ``PoseResult``; when a ``PoseResult`` with ``success=False`` is passed the call is a no-op and logs a warning instead of teleporting the robot to the lowest-error random-restart configuration.

    - Fixed

      - Cold-start IK (no ``seed=`` and no cached ``_last_solution``) now seeds the Levenberg-Marquardt solver from a prioritized ladder (joint-limit midpoint, deterministic random restarts within joint limits, then zeros) instead of always starting from the all-zero configuration. Fixes silent ``success=False`` failures on redundant arms such as the 7-DOF Franka Panda.
      - ``solve_ik`` no longer trusts a stale ``_last_solution`` blindly: the cached seed is tried first, but if it does not converge the full cold-start ladder runs in parallel as a fallback.
      - Sanitize pose names via ``pxr.Tf.MakeValidIdentifier``; empty, colon-containing, and non-ASCII names no longer crash ``store_named_pose`` / ``get_named_pose`` / ``delete_named_pose``.
      - ``store_named_pose`` logs a warning when a sanitized name collides with an existing pose stored under a different raw name.

- **isaacsim.robot.poser.ui**

    - Changed

      - Migrate extension implementation to the Core Experimental API.

- **isaacsim.robot.schema**

    - Added

      - ``IsaacRaycastSensor`` USD schema type, ``plugInfo`` entry, sensor tokens, and a Python compatibility wrapper.
      - ``GetAllRobotComponents`` helper (C++ and Python): returns every prim in a robot's subtree that applies any Isaac robot-schema API (``IsaacRobotAPI``, ``IsaacLinkAPI``, ``IsaacJointAPI``, ``IsaacSiteAPI``, ``IsaacReferencePointAPI``).
      - ``RecalculateRobotSchema`` gains a ``force_update`` kwarg that rebuilds ``robotLinks`` / ``robotJoints`` and authors cross-layer ``deletedItems``.
      - ``SaveRobotSchemaToRobotLayer`` flushes composed state onto the layer authoring ``IsaacRobotAPI`` only, with referenced-layer support via namespace translation.
      - ``get_allowed_tokens(attribute)`` helper that reads ``allowedTokens`` directly from the bundled ``RobotSchema.usda``.
      - Articulation-root scoring now picks the highest-parentness rigid body when the articulation root is a grouping ``Xform``.
      - New shared ``_discover_articulation_graph`` helper with a ``root_link_override`` input for seeding traversal from a user-chosen base link.
      - Sub-robot boundary handling registers each sub-robot as one collapsed entry at its first boundary joint.

    - Changed

      - Migrated ``rangeSensorSchema`` and ``isaacSensorSchema`` from pre-built C++ typed schema libraries (``omni-isaacsim-schema`` packman package) to codeless USD schemas. Added Python compatibility wrappers (``omni.isaac.RangeSensorSchema``, ``omni.isaac.IsaacSensorSchema``) so existing Python consumers work without changes. All C++ consumers now use generic ``prim.GetAttribute(token)`` / ``prim.GetTypeName()`` instead of typed schema classes.
      - Removed the ``omni-isaacsim-schema`` packman dependency and associated native library entries.
      - Removed ultrasonic sensor schemas (``UltrasonicArray``, ``UltrasonicEmitter``, ``UltrasonicFiringGroup``, ``UltrasonicMaterialAPI``) — no code references existed.
      - Removed the ``omni.usd`` dependency from ``extension.toml``.
      - Added ``sensor_tokens.h`` header providing token constants for all sensor schema attributes and type names.
      - Replaced ``CARB_LOG_WARN`` with ``fprintf(stderr, ...)`` in the C++ header; replaced ``carb.log_*`` with Python ``logging``.
      - Replaced ``omni.usd.get_world_transform_matrix`` with pure ``pxr`` ``UsdGeom.Xformable.ComputeLocalToWorldTransform``.
      - Targets now written as prepend list ops via ``_set_targets_as_prepend``, preserving additive composition with downstream layers.
      - ``PopulateRobotSchemaFromArticulation`` and ``RecalculateRobotSchema`` traverse DFS by default with a ``traversal`` kwarg (``"dfs"`` | ``"bfs"``); only register ``RigidBodyAPI`` prims as ``robotLinks`` and ``JointAPI`` prims as ``robotJoints``; grouping Xforms skipped.
      - ``_apply_api`` is a no-op when the schema is already applied, preventing ``apiSchemas`` churn on recalculation.

    - Deprecated

      - ``IsaacLightBeamSensor`` and the ``rangeSensorSchema`` ``Lidar`` / ``Generic`` types — used only by the deprecated ``isaacsim.sensors.physx`` extension. Use ``IsaacRaycastSensor`` with ``isaacsim.sensors.experimental.physics`` or ``isaacsim.sensors.experimental.rtx`` instead.
      - The ``IsaacLightBeamSensor`` Python wrapper and the ``omni.isaac.RangeSensorSchema`` module now emit ``DeprecationWarning`` on construction / import.

    - Fixed

      - ``GenerateRobotLinkTree`` grafts links and physics joints from nested sub-robots onto the parent's kinematic tree, so forward kinematics propagates through the entire assembly (gripper variants attached at a wrist link, etc.). Per sub-robot, prims carrying ``IsaacRobotLinkAPI`` / ``IsaacRobotJointAPI`` are preferred; bare ``UsdPhysicsRigidBodyAPI`` / ``UsdPhysicsJoint`` prims are picked up only as a fallback.
      - ``GenerateRobotLinkTree``: rewrote the two ``UsdPrimRange`` loops to conventional range-for shape so ``utils.h`` is includable from C++ consumers.
      - ``PopulateRobotSchemaFromArticulation`` / ``RecalculateRobotSchema`` fall back to ``robot_prim`` as a synthetic articulation root and sweep ``Usd.PrimRange`` to apply ``JointAPI`` / ``LinkAPI`` when BFS yields no chain, ensuring relationships are populated on vehicle and drone assets.
      - ``robot_schema`` imports ``pxr.Usd`` during module initialization so ``pxr.Usd`` annotations resolve in standalone wheel environments.
      - Added ``GetRobotLinkParentMap`` helper to ``utils.h`` for resolving ``isaac:physics:robotJoints`` ``body0``/``body1`` relationships into a child-link to parent-link path map.

- **isaacsim.robot.schema.ui**

    - Changed

      - Gate USD ``SELECTION_CHANGED`` subscription and ``ObjectsChanged`` listener on effective visibility; background tabs and hidden windows no longer pay per-click or per-stage-tick handler cost.
      - Resolve the active robot via ``usdrt.Usd.Stage.GetPrimsWithAppliedAPIName("IsaacRobotAPI")`` against Fabric, replacing the per-selection USD ``prim.HasAPI`` ancestor walk.
      - Pin the active robot scope across selection changes (eliminates the per-click flash); selecting a child robot in nested-robot setups now shows only the child.
      - ``MaskingOperations.bypass_prim`` / ``unbypass_prim`` return ``(success: bool, joint_info: tuple[str, str] | None)`` instead of an overloaded ``None``.
      - ``SelectionWatch._on_selection_changed`` early-returns when the resolved tree-view item set is unchanged.

    - Fixed

      - Inspector no longer crashes with ``AttributeError: '_StageModel__usdrt_stage'`` when filtering the tree after a view-mode switch.
      - ``MaskingState.toggle_bypassed`` / ``toggle_anchored`` / ``toggle_deactivated`` (and ``set_*``) no longer silently report success and pollute the in-memory sets when ``MaskingOperations`` rejected the prim. In-memory state and the USD masking sublayer are now guaranteed to stay in sync.
      - The unbypass path honors ``(success, _)`` and restores the prior mask if a pre-emptive unmask was performed and the subsequent bypass was rejected by the backend.

- **isaacsim.robot.surface_gripper**

    - Added

      - ``create_surface_gripper`` public Python API as a direct replacement for the Kit command.
      - ``SurfaceGripper`` OmniGraph node (``OgnSurfaceGripper``) gains explicit ``Open`` and ``Close`` execution-input pins alongside the existing ``Toggle`` pin. OGN node version bumped from 2 to 3.

    - Changed

      - ``OgnSurfaceGripper.compute`` dispatches on the firing execution-state of each pin (``db.inputs.<pin> == omni.graph.core.ExecutionAttributeState.ENABLED``) rather than on truthiness, with ``Close`` taking precedence over ``Open`` and ``Open`` over ``Toggle`` when multiple pins fire in the same tick. Existing graphs that only wire ``Toggle`` retain their prior behaviour.

    - Deprecated

      - ``CreateSurfaceGripper`` Kit command, in favor of ``create_surface_gripper()``.

    - Fixed

      - ``SurfaceGripperComponent`` now defaults the joint forward axis to ``X`` everywhere (cache initialization, per-joint parse fallback, and ``_getJointForwardAxis`` out-of-range fallback) to match the ``isaac:forwardAxis`` schema default. Previously the three C++ fallbacks returned ``Z``, producing inconsistent behavior on attachments whose joint was missing the attribute.

- **isaacsim.robot.surface_gripper.ui**

    - Changed

      - Replaced ``omni.kit.commands.execute("CreateSurfaceGripper")`` call sites with direct ``create_surface_gripper()`` API.

- **isaacsim.robot.wheeled_robots**

    - Changed

      - Deprecated extension in favor of ``isaacsim.robot.experimental.wheeled_robots`` and ``isaacsim.robot.wheeled_robots.nodes``; moved to ``source/deprecated``; OmniGraph nodes removed (now in ``isaacsim.robot.wheeled_robots.nodes``).

    - Fixed

      - Add validation for ``wheel_radius`` in ``DifferentialController.__init__`` to reject zero/negative values (division by zero).
      - Documented ``stanley_control`` PID parameters (``p``, ``i``, ``d``) as unused/reserved to match the experimental version.
      - Fixed an incorrect unit label in the ``DifferentialController`` docstring (``cms`` → ``meters``).
      - Raise a clear ``ValueError`` when ``WheeledRobot`` is initialized without wheel DOF names or indices.
      - Reject non-finite ``normalize_angle()`` inputs instead of looping indefinitely.

- **isaacsim.robot.wheeled_robots.nodes**

    - New extension

- **isaacsim.robot.wheeled_robots.ui**

    - Changed

      - Migrated to experimental APIs (``app_utils``, ``prim_utils``, ``stage_utils``) replacing deprecated ``isaacsim.core.utils``; updated the dependency from ``isaacsim.robot.wheeled_robots`` to ``isaacsim.robot.wheeled_robots.nodes``.
      - Converted test file to use ``SimulationManager``, experimental ``Articulation``, and ``GroundPlane``.

- **isaacsim.robot_motion.cumotion**

    - Added

      - ``CumotionWorldInterface`` accepts a ``device`` constructor parameter (any value ``wp.get_device`` accepts; defaults to ``None``) and dispatches per-frame collider transform composition to either a vectorized NumPy (CPU) path or a Warp (CUDA) kernel.
      - ``RmpFlowController`` gains ``maximum_substep_size`` for sub-stepping when more stable integration is required.
      - ``compute_collider_transforms_cpu`` utility: vectorized NumPy mirror of the Warp collider-transform kernel.
      - ``normalize_urdf_for_urdfdom(urdf_text)`` helper (``urdf_normalize.py``): rewrites a URDF in-memory so it satisfies urdfdom 4.0.1's strict parser without modifying any kinematically meaningful values (inserts default ``effort`` / ``velocity`` on ``<limit>``, adds a wide-open ``<limit>`` to ``revolute`` / ``prismatic`` joints missing one, adds ``k_velocity="0"`` to ``<safety_controller>``, drops empty ``<dynamics/>``, removes ``<mimic>`` without a target joint). Idempotent on already-clean URDFs.

    - Changed

      - ``get_world_to_robot_base_transform`` memoizes its return and yields the same ``wp.array`` tuple until the base pose is updated.
      - ``load_cumotion_robot`` pre-processes the URDF through ``normalize_urdf_for_urdfdom`` and calls ``cumotion.load_robot_from_memory`` (instead of ``load_robot_from_file``), so URDFs produced by ``isaacsim.asset.exporter.urdf.UsdToUrdfConverter`` and similar generators load correctly. Disk content is never mutated.

    - Fixed

      - ``TrajectoryOptimizer`` is now functional on Windows.

- **isaacsim.robot_motion.cumotion.examples**

    - Added

      - Best-effort per-class GUI warmup in ``async setUp`` (prevents Windows hangs).
      - Unit tests for button presses, slider values, and stateful behavior of all GUI components.

    - Changed

      - Refactored all five example sub-extensions (``graph_planner``, ``trajectory_optimizer``, ``rmp_flow``, ``trajectory_generator``, ``world_interface``) so each ``Scenario`` owns its scene loading, async lifecycle, and prim-wrapper teardown, while ``UIBuilder`` is a strict view that only builds widgets and forwards events.
      - Loading helpers are now async; reduced the number of GPU copies needed (some Warp arrays are only needed for ``reset``).
      - ``TrajectoryOptimizer`` example functional on Windows; ``Extension`` removes no-op physics-step subscriptions.

    - Fixed

      - ``UIBuilder`` now tracks and cancels in-flight ``_load_scene_async`` tasks on cleanup and reload, preventing expired-prim errors when a new stage is created between tests.
      - ``LOAD`` no longer hangs when clicked while a previous load is still in flight; ``LOAD`` is not cancelled mid-flight on the graph-planner.
      - Removed ``timeline.play()`` / frame-wait / ``timeline.stop()`` from ``_load_scene_async`` so a failing CUDA init does not block the Kit update thread and prevent ``next_update_async()`` from resolving.
      - We no longer force physics or rendering dt; throwing an uncaught ``RuntimeError`` was possible because timeline could be playing.
      - ``wait_until`` poll interval reduced from 250 ms to 50 ms, cutting idle delay.

- **isaacsim.robot_motion.experimental.motion_generation**

    - Changed

      - ``JointState`` and ``SpatialState`` build their per-row valid views (``positions``, ``velocities``, ``position_indices``, ...) lazily on first property access, reusing zero-copy NumPy slices instead of eagerly allocating ``wp.array``\ s in the constructor. Public API and semantics are unchanged.

- **isaacsim.robot_motion.lula**

    - Changed

      - Moved to ``source/deprecated``.

- **isaacsim.robot_motion.lula_test_widget**

    - Changed

      - Moved to ``source/deprecated``.

- **isaacsim.robot_motion.motion_generation**

    - Changed

      - Moved to ``source/deprecated``.

    - Fixed

      - Added missing ``return None`` after ``carb.log_error`` in ``LulaCSpaceTrajectoryGenerator.compute_timestamped_c_space_trajectory`` (invalid interpolation mode), ``LulaTrajectory.get_joint_targets`` (out-of-bounds time), ``ArticulationKinematicsSolver.compute_end_effector_pose``, ``compute_inverse_kinematics``, and ``set_end_effector_frame``.
      - ``ArticulationTrajectory.get_action_at_time`` raises ``ValueError`` immediately after ``carb.log_error`` for out-of-bounds time instead of returning a structurally valid but semantically wrong action (6131126).

- **isaacsim.robot_motion.motion_generation.examples**

    - Changed

      - Renamed extension and Python package namespace from ``isaacsim.robot_motion.motion_generation.tutorials`` to ``isaacsim.robot_motion.motion_generation.examples``; moved to ``source/deprecated``.
      - Example UIs register under a shared ``Motion Generation Examples`` menu (RMPflow, Kinematics, RRT, Trajectory Generation).
      - Old load/reset buttons changed out for newer button types.

- **isaacsim.robot_motion.pink**

    - New extension

- **isaacsim.robot_motion.pink.examples**

    - New extension

- **isaacsim.robot_setup.assembler**

    - Changed

      - Variant payloads written by ``RobotAssembler.begin_assembly`` / ``finish_assemble`` are now stored under ``payloads/<variant_set>/<variant_name>.usd`` (relative to the base robot asset) instead of ``configuration/<variant_set>_<variant_name>.usd``. The variant-set name acts as a subdirectory rather than a filename prefix; the destination directory is created automatically.
      - Made ``assemble_rigid_bodies`` and ``create_fixed_joint`` private (``_assemble_rigid_bodies``, ``_create_fixed_joint``).
      - ``RobotAssembler.__del__`` no longer calls ``reset()`` / ``cancel_assembly()`` because finalizers must not touch USD or schedule coroutines (the event loop and ``omni.usd`` context may already be torn down). Callers needing in-flight teardown must invoke ``reset()`` explicitly.

    - Fixed

      - ``RobotAssembler.cancel_assembly()`` no longer raises ``AttributeError: 'RobotAssembler' object has no attribute '_assembly_identifier'`` when called on a fresh instance or before ``begin_assembly()``; ``reset()`` now initializes the assembly sublayer state.

- **isaacsim.robot_setup.gain_tuner**

    - Added

      - ``Snap to Limits`` test mode with per-joint pass / blocked / fail results, and ``Stress Test`` mode with Random Walk and Adversarial sub-modes.
      - ``get_test_result_metrics()`` API.
      - Pluggable ``RobotTest`` registry on ``GainTuner``.
      - Toggles to disable self-collisions and velocity limits.
      - ``GainTuner.add_inertia_updated_callback()`` and ``JointListModel.refresh_inertia_derived_columns()`` so the gains table refreshes Natural Frequency / Damping Ratio after deferred inertia computation.
      - ``usd_layer_utils`` helpers to resolve the robot physics layer for save (prim stack, nested sublayers, on-disk ``payloads/Physics/physics.usda``); unit tests for nested physx→physics sublayer composition.
      - Closed-form theory unit tests (no physics solver) with golden literal stiffness/damping references; RK4 discrete damped-oscillator test for ``_analyze_oscillation`` (isolates peak analysis from PhysX).

    - Changed

      - Default test mode is now ``Snap to Limits``; per-mode duration controls replace the shared ``Test Duration`` field.
      - Menu entry moved to ``Tools > Robotics > Asset Editors > Gain Tuner``.
      - Removed the dedicated extension ``[[test]] name = "newton"`` oscillation job and ``TestGainTunerOscillationDynamicsNewton`` until Newton-backed dynamics testing is fully integrated.

    - Fixed

      - Natural Frequency and Damping Ratio table columns refresh when accumulated joint inertia becomes available (after deferred ``compute_joints_accumulated_inertia``).
      - Save Gains to Physics Layer targets ``physics.usda`` / ``_physics.usd`` via joint prim-stack lookup, nested sublayers, and the conventional ``payloads/Physics/physics.usda`` path beside the root asset.
      - ``JointDriveMode.MIMIC`` is now ``3`` (was ``0``, aliased to ``NONE``) so mimic joints are distinct in ``list(JointDriveMode)``.
      - Oscillation harness deletes ``/World/robot`` before each rebuild (avoids PhysX tensor views on deleted ``root_joint``), uses ``base_mass=1.0`` so effective mass matches table math, and retries ``GainTuner.setup`` until the articulation is bindable.
      - ``project_inertia_onto_axis()`` logs a ``carb.log_warn`` when the joint rotation axis norm is below ``1e-9`` instead of silently returning ``0.0``.
      - Bulk edit preserves multi-selection; first column no longer collapses on small window sizes; stale test metrics cleared on new run; menu and ``CreateUIExtension:Gain Tuner`` show and focus the panel instead of toggling visibility; visibility callback branches on the ``visible`` argument.

- **isaacsim.robot_setup.grasp_editor**

    - Changed

      - Migrate extension implementation to the Core Experimental API.

    - Fixed

      - Fixed the silent failure of Skip Simulation → Export Grasp; export state is preserved across internal timeline stops and errors are surfaced in the UI.
      - Spelling corrections; user guide updated to use ``object_frame`` / ``gripper_frame`` field names matching the actual ``isaac_grasp`` schema written by ``DataWriter``.
      - Wrong shape on forces/torques being added into the RigidBody during simulation.

- **isaacsim.robot_setup.wizard**

    - Deprecated

      - Extension deprecated and moved to ``source/deprecated``.

- **isaacsim.robot_setup.xrdf_editor**

    - Changed

      - Migrate extension implementation to the Core Experimental API.
      - Decomposed the monolithic ``extension.py`` into focused modules.
      - Per-DOF arrays now size exactly to the selected articulation's DOF count instead of using a fixed ``MAX_DOF_NUM = 100`` buffer.
      - UI is split into per-panel modules under ``ui/`` (``InfoPanel``, ``SelectionPanel``, ``JointPropertiesPanel``, ``SphereEditorPanel``, ``EditorToolsPanel``).
      - ``editor_state.py`` provides a UI-free ``EditorState`` domain object that owns articulation data and high-level import/export operations.
      - ``xrdf_io.py`` and ``lula_io.py`` expose pure, UI-free read/write/merge helpers (``write_xrdf_file``, ``read_xrdf_file``, ``is_valid_xrdf_file``, ``merge_passthrough_dict``, ``write_lula_robot_description_file``, ``read_lula_robot_description_file``).
      - Replaced ``sphere_generation.compute_link_frame_mesh`` with ``isaacsim.core.experimental.utils.xform.get_relative_transform``; removed the local ``gf_quat_to_np_array`` helper.

    - Fixed

      - Exported XRDF no longer contains mimic joints.
      - ``UIBuilder.on_stage_closed`` no longer references the stage and raises a ``ValueError``.

- **isaacsim.ros2.bridge**

    - Removed

      - Removed the ``omni.isaac.ml_archive`` dependency.

- **isaacsim.ros2.core**

    - Added

      - ``wait_for_publishers_on_topic`` and ``wait_for_subscribers_on_topic`` helpers on ``ROS2TestCase`` for waiting on DDS endpoint discovery before asserting on message delivery. Uses a wall-clock timeout to handle platforms with no frame rate limiter; failure messages include the last-observed endpoint count.

    - Changed

      - Added ``LibraryLoader.h`` include to ``Ros2Types.h`` for SRTX integration support.
      - Camera info now reads OpenCV distortion coefficients from ``OmniLensDistortion`` schemas (``OmniLensDistortionOpenCvPinholeAPI``, ``OmniLensDistortionOpenCvFisheyeAPI``).
      - Migrated ``camera_info_utils`` from deprecated ``isaacsim.sensors.camera`` to ``isaacsim.sensors.experimental.rtx``.
      - Removed deprecated ``isaacsim.core.api``, ``isaacsim.core.utils``, ``isaacsim.sensors.camera``, ``isaacsim.sensors.rtx`` dependencies; added ``isaacsim.sensors.experimental.rtx`` and ``isaacsim.sensors.rtx.nodes``.
      - Removed legacy physical-distortion model support (``physicalDistortionModel``, ``physicalDistortionCoefficients``).
      - Replaced ``render_product_utils.py`` with ``ViewportManager`` from ``isaacsim.core.rendering_manager``.
      - Updated internal ROS 2 libraries to support the latest simulation-interfaces versions (v1.4.0 Humble, v1.5.0 Jazzy).

    - Fixed

      - Downgraded bundled Fast-RTPS from 2.6.11 to 2.6.10 in the Humble ``nv_ros2`` linux packages to avoid an upstream regression in 2.6.11.
      - ``read_camera_info()`` now applies the render-product resolution and scales ``fx``, ``fy``, ``cx``, ``cy`` accordingly for ``opencvPinhole`` / ``opencvFisheye`` lens models, fixing stale ``CameraInfo`` after retargeting.
      - Fixed joint state publisher writing no position / velocity data when effort retrieval fails.
      - Fixed handling for fixed-size array types in ``ROS2DynamicMessage.cpp`` when the input array length differs from the expected size.
      - Make ``Ros2TestBase`` use the sourced distro so tests load the same backend the plugin already initialized.
      - Raise an error if ``/exts/omni.replicator.srtx/enabled=true`` on non-Linux platforms.
      - Added an explicit import of ``_ros2_core`` bindings module for stubgen discoverability.

- **isaacsim.ros2.examples**

    - Changed

      - Migrated to ``isaacsim.core.experimental.utils``, ``isaacsim.core.rendering_manager``, and ``isaacsim.core.simulation_manager``.
      - MoveIt extension and standalone samples feed ``ROS2PublishJointState`` from a dedicated ``IsaacReadJointState`` node and use its ``sensorTime`` for the published timestamp.
      - Replaced ``PhysicsContext`` with ``PhysicsScene`` from ``isaacsim.core.simulation_manager``.
      - Replaced ``set_camera_view`` with ``ViewportManager.set_camera_view``.

- **isaacsim.ros2.nodes**

    - Added

      - SRTX publisher support for ROS 2 image, lidar point cloud, and laser scan topics. New C++ classes: ``ImagePublisher``, ``PointCloudPublisher``, ``PublisherBase``, ``SrtxPublisherFactory``. SRTX support added in ``ROS2CameraHelper``, ``ROS2CameraInfoHelper``, and ``ROS2RtxLidarHelper`` OGN nodes.
      - ``OgnROS2RtxRadarHelper`` node for publishing RTX Radar data as ``PointCloud2``.
      - Optional multitick support: LaserScan and PointCloud2 messages are built from the ``GenericModelOutput`` annotator directly, and RTX Lidar sensor inputs are assumed to be full frames.
      - ``test_sim_clock_physics_step`` validates ROS 2 clock publishing from an ``OnPhysicsStep``-driven on-demand graph; ``test_joint_state_subscriber_with_name_override`` verifies ``JointNameResolver`` correctly maps ``isaac:nameOverride`` joint names.
      - Camera and camera-info tests using ``isaacsim.sensors.experimental.rtx``; multitick rendering test coverage for RTX sensor nodes.

    - Changed

      - Enabled multitick and removed the non-multitick code paths (including ``build_rtx_sensor_pointcloud_writer`` and dynamically-generated writers, replaced by a single PointCloud writer based on ``isaacsim.sensors.experimental.nodes.IsaacExtractRtxSensorPointCloud``).
      - Migrated sensor nodes and tests to ``isaacsim.sensors.experimental.physics`` 3.0.0 and ``isaacsim.sensors.experimental.rtx``; raycast sensor creation goes through ``RaycastSensor.create()`` (the authoring class) directly.
      - Migrated to ``isaacsim.core.experimental.utils``, ``isaacsim.core.experimental.objects``, ``isaacsim.core.experimental.prims``, ``isaacsim.core.rendering_manager``, and ``isaacsim.core.simulation_manager``.
      - Query the active physics engine at runtime via ``omni::physics::IPhysics`` and pass it to ``createSimulationView`` so ROS 2 tensor-backed nodes work with any registered engine.
      - ``OgnROS2CameraHelper``: renamed the ``compressionType`` input to ``srtxCompressionType`` (and marked it hidden).
      - Deprecated the ``frameSkipCount`` and ``fullScan`` inputs in all helper nodes (``OgnROS2CameraHelper``, ``OgnROS2CameraInfoHelper``, ``OgnROS2RtxLidarHelper``); deprecation messages direct users to set the input to 0; runtime warning now fires once per node lifetime.
      - ``OgnROS2PublishLaserScan`` legacy array path synthesizes binary hit/miss intensities when ``intensitiesData`` is unconnected.
      - Refactored ``OgnROS2PublishPointCloud`` to use the shared ``PublisherBase`` / ``PointCloudPublisher`` classes.

    - Removed

      - ``OgnROS2PublishPointCloud``: removed the unused ``gmoDataPtr`` / ``gmoBufferSize`` / ``gmoMaxElements`` inputs and the ``publishFromGMO`` code path; point cloud publishing always goes through the per-field pointer inputs populated by ``IsaacExtractRTXSensorPointCloud``.

    - Fixed

      - **Behavior change**: ``OgnROS2PublishPointCloud`` now gates optional metadata fields (intensity, timestamp, emitter/channel/material/tick IDs, hit normal, velocity, object ID, echo ID, tick state, radial velocity) on the matching ``output*`` boolean inputs **in addition to** the pointer being non-zero. Wiring a pointer through ``IsaacExtractRTXSensorPointCloud`` no longer forces the field into the message; if you were driving the publisher's pointer inputs directly without setting the matching ``output*`` flag, you will need to set the flag.
      - The SRTX sensor-set name used by ``OgnROS2CameraHelper`` and ``OgnROS2RtxLidarHelper`` is overridable via ``/exts/omni.replicator.srtx/sensorSetName``; previously both helpers hard-coded ``"default-sensor-set"`` and clobbered each other in Mega simulations.
      - ``OgnROS2PublishJointState`` no longer creates a tensor simulation view when publishing from connected joint-state inputs (the tensor view is created only for the deprecated ``targetPrim`` path).
      - ``OgnROS2RtxLidarHelper`` / ``OgnROS2RtxRadarHelper``: ``showDebugView`` now sets ``doTransform=True`` on the debug-draw writer when ``outputFrameOfReference`` is anything other than ``WORLD`` (fixes inverted condition); ``OgnROS2RtxLidarHelper`` 2D lidar (``LaserScan``) publishing no longer fails on the unsupported ``max_points`` key; drop the legacy ``Camera + IsaacRtxLidarSensorAPI`` branch from validation (only ``OmniLidar + OmniSensorGenericLidarCoreAPI`` is accepted).
      - ``OgnROS2RtxLidarHelper`` uses the new ``RtxSensorDebugDrawPointCloud`` writer rather than the deprecated ``RtxLidarDebugDrawPointCloudBuffer``.
      - Null checks for the simulation view in ``OgnROS2PublishJointState`` and ``OgnROS2PublishTransformTree`` to prevent crashes when the physics backend initialization fails.
      - ``OgnROS2CameraHelper`` uses ``.IsValid()`` instead of ``is None`` to check render-product prim existence; ``OgnROS2PublishPointCloud`` uses ``db.inputs.frameId()`` instead of its own uninitialized frame ID.
      - ``OgnROS2PublishLaserScan`` calls ``generateBuffers`` before ``writeData`` so output buffers are correctly sized.
      - Numerous DDS-discovery stabilizations and Windows flake fixes in subscriber-queue, transform-tree, laser-scan, and golden-image tests.

- **isaacsim.ros2.sim_control**

    - Added

      - ``GetSpawnables`` service for discovering available USD assets for spawning (defaults to ROS assets under ``/Isaac/Samples/ROS2/Robots``, excludes ``.thumbs`` thumbnails).
      - ``SpawnEntities`` batch spawning service.
      - ``GetEntityBounds`` service for retrieving axis-aligned bounding boxes of scene entities.
      - Shared ``_resolve_source_path`` helper so both ``GetSpawnables`` and ``GetAvailableWorlds`` resolve Nucleus-relative paths from user-supplied sources.

    - Changed

      - Migrated to ``isaacsim.core.experimental.utils`` for stage and prim operations; replaced direct ``GetPrimAtPath`` calls with ``prim_utils.get_prim_at_path``; use ``backend="fabric"`` for Fabric stage access.

    - Fixed

      - Missing service/action types now skip registration with a warning naming the type, instead of a generic error.
      - ``GetSimulatorFeatures`` advertises the subset of constants present in the installed ``simulation_interfaces`` instead of returning an empty list when a constant is missing.
      - ``GetAvailableWorlds``: user-provided ``additional_sources`` are no longer mangled by Nucleus-relative resolution when ``offline_only=True`` on Windows.

- **isaacsim.ros2.tf_viewer**

    - Changed

      - Added ``isaacsim.core.experimental.utils`` dependency; migrated test utilities to ``stage_utils`` from ``isaacsim.core.experimental.utils``.

- **isaacsim.ros2.ui**

    - Changed

      - Migrated to ``isaacsim.core.experimental.utils`` and ``isaacsim.core.rendering_manager``; TF and Odometry builders use the ``IsaacComputeTransformTree`` node.
      - Replaced ``DomeLight`` with ``DistantLight`` in test scene setup.

    - Fixed

      - Fixed a ``SIGSEGV`` in ``test_odometry_null_conditions`` and ``test_tf_null_conditions`` when empty prim fields are submitted; ``_check_params`` in ``Ros2OdometryGraph`` and ``Ros2TfPubGraph`` now rejects empty required prims before graph creation.
      - ``Ros2RtxLidarGraph._check_params``: drop the legacy ``Camera + IsaacRtxLidarSensorAPI`` branch from lidar-prim validation; only ``OmniLidar + OmniSensorGenericLidarCoreAPI`` is accepted.

- **isaacsim.ros2.urdf**

    - Added

      - "Base Type" dropdown (Source / Fixed / Mobile) driving the tri-state ``URDFImporterConfig.fix_base`` field.
      - Robot type dropdown in the UI.
      - Error message when a package cannot be resolved in the URDF.

    - Changed

      - Updated UI status language on failed / successful imports; updated the import path to use ``isaacsim.gui.components`` UI utilities; tests preserve temp output on failure for debugging.

    - Deprecated

      - ``URDFImportFromROS2Node`` Kit command, in favor of using ``RobotDefinitionReader`` and ``URDFImporter`` directly.

    - Fixed

      - The intermediate URDF and (when no output folder is set) the USD are now written to a system temp directory.
      - Handled ``RCLError`` when the ROS 2 context is shut down during a background service call in ``RobotDefinitionReader``.

- **isaacsim.sensors.camera**

    - Deprecated

      - Extension deprecated in favor of ``isaacsim.sensors.experimental.rtx`` (updated deprecation warning and ``Overview.md`` were updated to point to ``...rtx``, not ``...camera``).

    - Fixed

      - ``Camera.get_dt`` returns ``0.0`` (not ``-1.0``) when the rendering frequency is unknown; ``Camera.set_dt`` accepts valid sub-rendering-rate frequencies despite float-modulo precision.
      - Fixed lens-distortion behavior: ``set_lens_distortion_model("pinhole")`` only removes lens-distortion schemas instead of all applied schemas; case-sensitive ``"pinhole"`` substring check now matches ``"opencvPinhole"`` in four projection methods.
      - ``set_fisheye_polynomial_properties`` no longer silently skips valid ``0.0`` values; ``set_kannala_brandt_properties`` warning message corrected.
      - Log a warning when ``Camera.set_frequency()`` / ``set_dt()`` falls back to "process all frames" because ``/app/runLoops/main/rateLimitFrequency`` is unset.
      - Raise a clear error when ``Camera.attach_annotator()`` is called before ``Camera.initialize()``.
      - ``CameraView`` docstring fix: ``instance_segmentation_fast`` and ``instance_id_segmentation_fast`` runtime dtype is ``uint32`` (not ``int32``).

- **isaacsim.sensors.camera.ui**

    - Added

      - New depth- and 2D-camera vendors: Luxonis OAK4-D, OAK4-D Wide, OAK-D Pro PoE / Pro W PoE, OAK-D ToF; SICK Inspector83x, InspectorP61x, safeVisionary2, Visionary-T Mini.
      - Dependency on ``isaacsim.core.experimental.utils`` and ``isaacsim.sensors.experimental.rtx`` for ``SUPPORTED_CAMERA_CONFIGS`` / ``get_camera_metadata`` / ``RtxCamera`` / ``SingleViewDepthCameraSensor``.

    - Changed

      - Menu actions load camera USDs via ``RtxCamera.create()`` (experimental) instead of a raw Xform reference. Depth-sensor entries: every Camera in the loaded asset with a template render product carrying ``OmniSensorDepthSensorSingleViewAPI`` is wrapped with ``SingleViewDepthCameraSensor``.
      - The sensor list is now sourced from ``isaacsim.sensors.experimental.rtx.SUPPORTED_CAMERA_CONFIGS`` (``Extension.SENSORS`` is built at import time via ``get_camera_metadata``), so adding a new camera vendor/model is a one-place change. The legacy ``Extension.SENSORS`` shape is preserved for backward compatibility.
      - Default ``prim_prefix`` for menu-created sensors is now derived from the USD file stem (hyphens and dots replaced by underscores), so menu-placed prim names change in some cases (for example ``/RealsenseD455`` → ``/rsd455``, ``/Femto`` → ``/orbbec_femtomega_v1_0``, ``/OAK4D`` → ``/oak4_d``). Prim names that already matched the stem are unchanged.

    - Removed

      - Dependency on the deprecated ``isaacsim.sensors.camera`` extension. The ``SingleViewDepthSensorAsset`` import is replaced by ``RtxCamera.create()`` + ``SingleViewDepthCameraSensor``.
      - Implicit dependency on the deprecated ``isaacsim.core.utils.stage`` (``get_next_free_path`` replaced by ``generate_next_free_path``; ``clear_stage`` replaced by ``stage_utils.create_new_stage_async()`` in tests).

    - Fixed

      - Depth-sensor wrappers returned by ``_wrap_depth_sensor_cameras`` are now stored in ``Extension._depth_sensors`` instead of being discarded, preventing a create/destroy cycle that corrupted the RTX pipeline and made asset materials invisible.

- **isaacsim.sensors.experimental.physics**

    - Added

      - Raycast Sensor C++ implementation, Python bindings, backend, commands, and examples.

    - Changed

      - Aligned the ``IMUSensor``, ``ContactSensor``, and ``RaycastSensor`` APIs with ``isaacsim.sensors.experimental.rtx``:
      - Split authoring (``IMU`` / ``Contact`` / ``Raycast``) from runtime; runtime constructors take a path or authoring instance; ``create()`` lives only on the authoring classes. Replace ``IMUSensor.create(path, ...)`` with ``IMUSensor(IMU.create(path, ...))`` (same for ``Contact`` and ``Raycast``).
      - Constructors take keyword-only ``positions`` / ``translations`` / ``orientations`` / ``scales`` arrays (``(N, 3)`` / ``(N, 4)`` wxyz) plus ``reset_xform_op_properties`` (default ``True``), instead of singular ``Gf`` types. Constructor parameter ``prim_path`` renamed to ``path``.
      - Removed ``*Backend`` classes (``ImuSensorBackend``, ``ContactSensorBackend``, ``RaycastSensorBackend``, ``EffortSensorBackend``, ``JointStateSensorBackend``). The runtime sensors own the C++ Carbonite interface directly and expose both ``get_data()`` (dict) and ``get_sensor_reading()`` (raw struct) — replace ``XxxSensorBackend(path)`` with ``XxxSensor(path)``. Renamed ``get_current_frame()`` → ``get_data()``. Removed the ``prim_path`` property, the no-op ``initialize()`` method, and ``ContactSensor.{get,set}_min_threshold`` / ``_max_threshold`` / ``_radius`` shims (use ``sensor.contact.<method>`` instead).
      - Removed ``__getattr__`` attribute forwarding from the runtime; go through the typed ``sensor.imu`` / ``sensor.contact`` / ``sensor.raycast`` accessor for ``paths``, ``prims``, ``set_visibilities``, ``get_world_poses``, etc.
      - Multi-prim ``path``, conflicting ``positions`` / ``translations``, and wrapping an existing prim whose USD type does not match the sensor's ``_PRIM_TYPE`` now raise ``ValueError``. Dropped the unused ``name`` parameter.
      - Internal sensor maps keyed by prim path (``std::string``) instead of a monotonic counter; ``createSensor()`` returns ``bool`` instead of ``int64`` and ``removeSensor`` / ``getSensorReading`` / ``getRawContacts`` take a prim path.
      - Bumped C++ Carbonite interface versions to 2.0 (``IImuSensor``, ``IContactSensor``, ``IEffortSensor``, ``IJointStateSensor``).
      - Hardened the C++ runtime against prim deletion and recreation; ``getSensorReading`` (and Contact's ``getRawContacts``) invalidate the cached entry when the underlying USD prim has been removed. The ``createSensor`` early-out tears down the cached entry when the parent rigid body / articulation root no longer matches.
      - Migrated ContactSensor and IMUSensor world-transform reads from ``computeWorldXformNoCache`` to ``IXformDataView`` (``IPrimDataReader``); port ContactSensor to use the IPrimDataReader contact API (``enableContactReporting`` / ``getContactReport``) instead of direct PhysX contact event subscription.
      - Removed ``commands_api.md``; updated ``api.rst`` and ``Overview.md`` to document the class-based creation API.

    - Fixed

      - ``ContactSensor.__init__`` parent validation walks up the hierarchy and accepts both ``CollisionAPI`` and ``RigidBodyAPI`` ancestors; no longer accesses ``self._prim`` before assignment when applying threshold/radius overrides.
      - Refresh IMU prim-data-reader initialization on read/step so IMU data is available after physics-only simulation steps.
      - Added ``update()`` flush calls in ``EffortSensorImpl`` and ``ImuSensorImpl`` before reading physics data; null guards for deferred prim-data-reader provider loading in ``_initializeStage``.

- **isaacsim.sensors.experimental.rtx**

    - New extension

- **isaacsim.sensors.physics**

    - Deprecated

      - Extension deprecated in favor of ``isaacsim.sensors.experimental.physics``.

    - Fixed

      - Added ``is_valid`` to ``IMUSensor.get_current_frame()`` output, plus the scalar-first ``(w, x, y, z)`` quaternion convention to the ``IMUSensor.get_current_frame`` docstring.
      - ``ContactSensor.__init__`` no longer raises ``UnboundLocalError`` when no PhysicsScene exists on stage; no longer uses ``int(1/frequency)`` (which truncates to 0 for sub-Hz frequencies); validates ``self._body_prim_path`` (not ``prim_path``) for the CollisionAPI check.
      - ``EffortSensor.change_buffer_size`` no longer creates aliased object references via ``np.resize`` on an object-dtype array; ``EffortSensor.get_sensor_reading()`` fallback uses the newest valid buffered reading without mutating buffered state; no longer raises ``ZeroDivisionError`` when ``step_size`` is 0 and timestamps are equal.

- **isaacsim.sensors.physics.examples**

    - Added

      - Example for creating solid-state, rotating, and beam-curtain raycast sensors.

    - Changed

      - Beam-curtain raycast example derives the hit-count threshold from each sensor's configured ``max_range`` instead of a hardcoded ``100.0``.
      - Migrated examples and tests to the ``isaacsim.sensors.experimental.physics`` 3.0.0 API: call ``IMU.create()``, ``Contact.create()``, ``Raycast.create()`` (the authoring classes) and wrap the returned authoring object with the runtime sensor for data reads.

    - Fixed

      - IMU example no longer raises ``AttributeError`` when reading orientation; reads scalar ``orientation_w/x/y/z`` fields individually instead of indexing.

- **isaacsim.sensors.physics.nodes**

    - Added

      - Isaac Read Raycast Sensor OmniGraph node.

    - Changed

      - Migrated OGN test fixture (``AntConfig``) and OGN tests to the ``isaacsim.sensors.experimental.physics`` 3.0.0 API.
      - Updated OmniGraph nodes to use the prim-path-based sensor API instead of integer sensor IDs.

- **isaacsim.sensors.physics.ui**

    - Added

      - Menu items for creating solid-state, rotating, and beam-curtain raycast sensors.

    - Changed

      - Migrated menu callbacks to the ``isaacsim.sensors.experimental.physics`` 3.0.0 API.

- **isaacsim.sensors.physx**

    - Deprecated

      - Extension deprecated in favor of ``isaacsim.sensors.experimental.physics``.

    - Fixed

      - Update the rotating PhysX LiDAR during physics-only simulation steps and avoid double simulation on the next stage update.

- **isaacsim.sensors.physx.examples**

    - Deprecated

      - Extension deprecated in favor of ``isaacsim.sensors.physics.examples``.

    - Fixed

      - Run ``_plot_pattern`` in a background thread to avoid blocking Kit's main event loop.
      - Fixed an ``AttributeError`` in ``lidar_info.py`` when adding a translate op to the lidar prim.

- **isaacsim.sensors.physx.ui**

    - Deprecated

      - Extension deprecated in favor of ``isaacsim.sensors.physics.ui``.

- **isaacsim.sensors.rtx**

    - Added

      - Optional multitick support: when enabled, switches to nodes that consume ``GenericModelOutput`` assuming it contains a full scan, eliminating lidar accumulation post-processing.
      - WAR for ``omni.replicator.core`` 1.13.5: specify RTX Lidar and Radar ``auxOutputType`` as the ``channels`` attribute on ``GenericModelOutput`` ``RenderVar``.
      - ``IsaacSensorCreateRtxLidar`` ``variant`` parameter accepts ``dict[str, str]`` for USDs with multiple variant sets (for example the SICK family ``Product`` × ``Profile``), matching ``Lidar.create()`` in ``isaacsim.sensors.experimental.rtx``.

    - Changed

      - Multitick now enabled by default; scan accumulation controlled by ``omni:sensor:Core:accumulateOutputs`` on the ``OmniLidar`` prim.
      - ``OmniLidar`` ``omni:Sensor:Core:accumulateOutputs`` defaults to ``True`` and ``omni:sensor:Core:skipDroppingInvalidPoints`` defaults to ``False`` when using the command.
      - Moved ``generic_model_output``, ``sensor_checker`` and supported lidar configurations to the experimental extension.
      - Formally deprecated ``outputNormal`` in favor of ``outputHitNormal`` in ``IsaacCreateRTXLidarScanBuffer``.

    - Deprecated

      - Extension deprecated in favor of ``isaacsim.sensors.experimental.rtx``.

    - Removed

      - Removed the CUDA-based post-processing paths for lidar scan accumulation; multitick annotator tests replace non-multitick tests.

    - Fixed

      - Restored the deprecated ``outputNormal`` input on ``IsaacCreateRTXLidarScanBufferNew`` as an alias for ``outputHitNormal``, emitting a deprecation warning when used (5985827).
      - ``IsaacCreateRTXLidarScanBuffer`` / ``...New``: insufficient ``auxType`` on the ``OmniLidar`` prim now logs at ``ERROR`` with explicit remediation naming the ``omni:sensor:Core:auxOutputType`` USD attribute and the level required for each output (5985774).
      - Annotator tests correctly set RTX Radar output level to ``BASIC`` instead of ``FULL``.

- **isaacsim.sensors.rtx.nodes**

    - New extension

- **isaacsim.sensors.rtx.ui**

    - Added

      - RTX Acoustic menu (``Create > Sensors > RTX Acoustic``) with a generic NVIDIA entry; auto-populates per-vendor entries from ``SUPPORTED_ACOUSTIC_CONFIGS``.
      - RTX Radar menu reorganized into vendor submenus driven by ``SUPPORTED_RADAR_CONFIGS``; Generic RTX Radar moved under ``NVIDIA``; Texas Instruments IWRL6432AOP added.

    - Changed

      - Lidar / Radar / Acoustic menu actions pass a default variant from ``SUPPORTED_*_CONFIGS`` so multi-variant-set USDs (for example SICK ``Product`` × ``Profile``) materialize a valid prim from a single click.
      - Migrated Lidar creation from the ``IsaacSensorCreateRtxLidar`` Kit command to ``Lidar.create()`` from ``isaacsim.sensors.experimental.rtx``; Radar creation from ``IsaacSensorCreateRtxRadar`` to ``Radar()``.
      - Replaced ``isaacsim.core.utils.stage`` with ``isaacsim.core.experimental.utils.stage``; replaced ``isaacsim.sensors.rtx`` dependency with ``isaacsim.sensors.experimental.rtx``.

- **isaacsim.simulation_app**

    - Added

      - ``MinimalRendering`` renderer support in ``SimulationApp`` via the ``renderer`` launch-config option, plus a ``minimal_shading_mode`` option that sets ``/rtx/minimal/mode`` when using Minimal rendering.
      - Optional multitick support: the loop runner resets simulation time to 0.0 on ``SimulationApp.__init__``.
      - Emit telemetry event for app startup duration via ``isaacsim.core.telemetry``.

    - Changed

      - Added a forked watchdog process in ``close()`` that sends ``SIGKILL`` on timeout to prevent indefinite hangs from native-thread deadlocks.
      - Atexit handler now calls ``close(wait_for_replicator=False)`` to avoid hanging during interpreter shutdown.
      - Unload plugins before ``os._exit()`` in the fast_shutdown path to avoid glibc destructor deadlocks.

    - Removed

      - Removed direct telemetry calls from ``SimulationApp`` startup.
      - Removed the optional multitick support; when multitick is enabled, time now routes through a Fabric prim via ``SimulationManager``.
      - Removed the shutdown watchdog (no longer needed now that ``close()`` avoids the deadlock-prone framework release path).

    - Fixed

      - Replaced ``shutdown_and_release_framework()`` with ``app.shutdown()`` in ``close()`` to avoid a GIL deadlock where the main thread held the GIL while ``carb.tasking`` worker threads waited for it during plugin teardown (5948099).
      - Replaced the deprecated ``isaacsim.core.utils.carb.get_carb_setting`` import with the direct ``carb.settings`` API.
      - ``SimulationApp.close()`` flushes Python stdout/stderr before shutdown paths that can terminate the process through fast shutdown.
      - ``SimulationApp.close(exit_code=...)`` preserves nonzero script/test failure status when fast shutdown is enabled, removing the need for per-test ``os._exit`` hooks.

- **isaacsim.storage.native**

    - Added

      - Support overriding the default asset root via the ``ISAACSIM_ASSET_ROOT`` environment variable.

    - Fixed

      - ``path_join`` uses forward-slash concatenation for all URL schemes (not just ``omniverse://``), fixing backslash-corrupted paths on Windows when the assets root is an ``https://`` URL.
      - ``path_join`` ``../`` traversal uses ``rsplit`` instead of ``os.path.dirname`` to avoid the same backslash issue; normalizes backslashes in relative path components to forward slashes; treats any URL-scheme path (including ``file://``) as forward-slash on Windows.

- **isaacsim.streaming.rtsp**

    - New extension

- **isaacsim.test.collection**

    - Changed

      - Adapted rotation test helpers to the new ``[roll, pitch, yaw]`` euler-angle input convention.
      - Added a test for environment golden images.

    - Fixed

      - Improved Leatherback ROS 2 test reliability by using ``ROS2TestCase`` helpers and waiting for ROS publishers, subscribers, and camera data.
      - Made Leatherback ``test_cameras`` resilient to multitick rendering publisher-discovery latency.

- **isaacsim.test.docstring**

    - Fixed

      - Catch ``SystemExit`` during doctest execution to prevent application shutdown from docstring examples that call ``sys.exit()``.
      - Added ``from __future__ import annotations`` for PEP 604 union type syntax.

- **isaacsim.test.utils**

    - Added

      - New UI-automation modules: ``button_utils`` (``get_widget_screen_center``, ``deferred_click``, ``deferred_click_widget``, ``discover_template_buttons``), ``layout_utils`` (``ensure_dock_height``, ``ensure_window_visible``, ``close_windows``, ``reset_to_default_layout``), ``stage_utils`` (``poll_until``, ``wait_for_prim``, ``wait_for_stage_prims``), ``usd_utils`` (``compare_usd_files``), ``viewport_utils`` (``project_world_to_screen``).
      - Image capture helpers in ``image_capture``: ``capture_app_screenshot_async`` (full-application swapchain), ``capture_viewport_screenshot_async`` (viewport-only via replicator annotators), and ``capture_frame_sequence_async`` (multi-frame sequences in app, viewport, or replicator modes).
      - ``save_annotator_data`` in ``image_io`` to dispatch and save any annotator output (array, dict, or PNG).
      - ``menu_utils`` additions: ``_poll_async``, ``list_menu_paths``, ``navigate_menu_visual``, ``perform_widget_action``.
      - ``scroll_to_widget`` helper (and ``MenuUITestCase.scroll_to_widget``) for scrolling widgets off-screen into view.
      - ``compare_articulation_properties`` for pairwise comparison of articulation member values.
      - ``isaacsim.core.experimental.prims`` and ``omni.kit.viewport.window`` dependencies.

    - Changed

      - ``compare_images_in_directories`` prints the golden and test directory paths in its header and the full file paths on each failure.
      - ``compare_usd_files`` articulation check now detects whether the asset uses ``NewtonArticulationRootAPI`` or ``PhysxArticulationRootAPI`` and tests attributes accordingly.

    - Fixed

      - ``menu_click_with_retry`` waits for the requested menu path to resolve before clicking, absorbing the async menubar rebuild that ran after a prior test's window destruction (fixes flaky ``ui.Menu item failed to become show``).

- **isaacsim.ucx.core**

    - Added

      - Python bindings exposing ``UCXListener`` and ``UCXListenerRegistry`` via ``isaacsim.ucx.core``.

    - Fixed

      - Clear endpoint close callback during shutdown to prevent dangling pointer if external code holds stale endpoint references.
      - Explicitly request ``cuda_copy,sm,self,tcp`` TLS so the CUDA transport is active for GPU buffer rendezvous sends; pre-load ``libucm_cuda.so.0`` with ``RTLD_GLOBAL`` before ``ucxx::createContext()`` to make CUDA symbols available without requiring ``ucx/`` in ``LD_LIBRARY_PATH`` at launch; set ``UCX_MODULE_DIR`` via ``dladdr`` so the UCS module loader finds ``libuct_cuda.so.0`` and ``libucm_cuda.so.0``.

- **isaacsim.ucx.nodes**

    - Added

      - Camera streaming over UCX in ``OgnUCXPublishImage`` / ``OgnUCXCameraHelper``, controlled via the ``sendCudaBuffer`` bool input. When ``true``, a metadata FlatBuffer is sent first followed by the raw CUDA buffer on the same UCX tag; the receiver pre-allocates a device buffer and posts a ``tagRecv`` directly into it, avoiding any CPU copy when the transport supports it (GPU-direct RDMA, NVLink, CUDA IPC, or TCP with host staging). When ``false``, pixel bytes are copied to host memory and embedded in a single FlatBuffer.
      - Reads ``cudaDeviceIndex`` from the input into the ``DLDevice`` metadata for multi-GPU systems.
      - Metadata + tensor sends are atomic at queue time: if the tensor send fails to queue, the metadata send is cancelled so the receiver does not desync.
      - FlatBuffers schemas and package dependency for UCX bridge message types.
      - ``get_image_pixel_data_size`` helper in ``tests/common.py`` that returns the expected pixel byte count from the Image FlatBuffer's ``Tensor.shape[0]``.

    - Changed

      - Removed ``targetPrim`` input from ``UCXPublishJointState``; node now accepts ``jointPositions`` / ``jointVelocities`` / ``jointEfforts`` arrays from upstream nodes (for example Isaac Read Articulation State).
      - Removed ``targetPrim`` input from ``UCXPublishOdometry``; direct data inputs are now the sole data source.
      - Removed the unused ``renderProductPath`` input from ``UCXPublishImage``.
      - UCX publish and subscribe nodes use the Isaac OS FlatBuffers wire format.
      - Enabled multitick; deprecated ``frameSkipCount`` in ``UCXCameraHelper`` (deprecation message directs users to set the input to 0).

    - Fixed

      - Fixed a shutdown crash caused by an async send request outliving the UCX listener, triggering a close callback on a destroyed mutex.
      - ``OgnUCXCameraHelper``: ``frameSkipCount`` is once again honored (``publishStepSize = frameSkipCount + 1``); in 1.5.1, ``publishStepSize`` was hard-coded to ``1``, silently ignoring any user-set value.
      - ``test_camera.py``: ``receive_image_message`` now performs the second ``tag_recv`` required by the GPU-direct two-message protocol; added matching ``step`` and ``len(image_data)`` asserts so the CPU-/GPU-direct pixel payload is actually verified.
      - ``tests/common.py``: added ``cuda_copy`` to ``UCX_TLS`` so the GPU-direct recv has a CUDA memtype module.

- **isaacsim.util.camera_inspector**

    - Changed

      - Migrate extension implementation to the Core Experimental API.

    - Removed

      - Remove the check for deprecated lidar schema on USD Camera prims.

- **omni.isaac.ml_archive**

    - Changed

      - Update to PyTorch 2.11.0+cu128, torchaudio 2.11.0+cu128, torchvision 0.26.0+cu128, and updated dependencies.

    - Deprecated

      - Extension deprecated.

- **omni.kit.loop-isaac**

    - Removed

      - Removed the ``set_next_simulation_time`` API and ``SWHExternalSimulationTime`` event parameter. Multitick simulation time is now communicated via the ``/ExternalSimulationTime`` Fabric prim instead.

- **omni.pip.cloud**

    - Changed

      - Downgrade ``boto3`` and ``botocore`` to 1.40.61; update ``cryptography`` to 46.0.7.

- **omni.usd.schema.newton**

    - Changed

      - Updated ``newton-usd-schemas`` to 0.2.0.

Isaac Sim ROS Workspaces Changelog Summary
-------------------------------------------

The `Isaac Sim ROS Workspaces <https://github.com/isaac-sim/IsaacSim-ros_workspaces>`_ companion repository for Isaac Sim ROS Bridge has the following changes for Isaac Sim 6.0.0:

.. note::

   🎉 **We're now open to external contributions!** The community can help
   shape Isaac Sim ROS Workspaces. See the refreshed
   `CONTRIBUTING.md <https://github.com/isaac-sim/IsaacSim-ros_workspaces/blob/main/CONTRIBUTING.md>`_ for how to get involved — file issues,
   propose features, and open pull requests.

Added
^^^^^
- **Pixi-managed Jazzy workspace**: ``jazzy_ws/pixi.toml``, ``pixi.lock``, ``README_PIXI.md`` Windows dependency management via Pixi + RoboStack, including PyPI-based ``isaacsim`` install support and ``torch`` as a Pixi dependency.
- ``isaacsim_clearpath_nav2`` **package** (Humble + Jazzy): Nav2 integration for Clearpath robots, with ``dd100`` nav2/robot params, namespaced RViz config, launch file, and a ``clearpath_common`` dependency.
- **Simulation interfaces package** added to the workspace.
- **RTX radar RViz config** (``rtx_radar.rviz``) added to ``isaac_tutorials`` for radial-velocity visualization.
- **Windows long-paths warning** for Pixi on Windows.

Changed
^^^^^^^
- **Renamed** ``isaacsim`` **→** ``isaacsim_bringup`` in both Humble and Jazzy workspaces, with updated descriptions, changelog, and Humble parity.
- **Build type migration**: ``isaacsim``, ``cmdvel_to_ackermann``, ``h1_fullbody_controller``, and ``isaac_moveit`` converted from ``ament_cmake`` to ``ament_python``. Scripts moved into Python module layouts (``scripts/*.py`` → ``<pkg>/<pkg>/*.py``), with ``setup.py``/``setup.cfg``/``resource/`` markers replacing ``CMakeLists.txt``.
- ``use_internal_libs`` **default** changed from ``True`` to ``False`` on Jazzy (Python 3.12 sources ROS 2 from the system; Humble keeps ``True``). Jazzy users relying on internal libs must pass ``use_internal_libs:=True``.
- ``run_isaacsim.py`` ``dds_type`` is now opt-in and defaults to empty, preserving the surrounding ``RMW_IMPLEMENTATION`` (e.g. ``rmw_zenoh_cpp`` from Pixi activation); explicit values map to ``fastdds``/``cyclonedds``/``zenoh``.
- ``run_isaacsim.py`` **install path** falls back to the ``isaac_sim_package_path`` env var (set by Pixi activation) when ``install_path:=`` is not provided.
- ``moveit_resources`` bumped to widen ``allowed_start_tolerance``.
- ``topic_based_ros2_control`` submodule bumped (includes a Windows crash fix).
- ``open_isaacsim_stage.py`` path resolution uses ``get_package_share_directory`` instead of ``__file__``.
- Optimized the MoveIt sample for Jazzy: added a local ``panda_isaac.urdf.xacro`` (omits ``PandaHandFakeSystem``) and extended ``gripper_to_isaac.py`` to forward finger positions.
- Pixi environment setup, ``clearpath_common``, and pip dependency for ``h1_fullbody_controller``.

Removed
^^^^^^^
- ``CMakeLists.txt`` files for the four migrated packages (``isaacsim``, ``cmdvel_to_ackermann``, ``h1_fullbody_controller``, ``isaac_moveit``) in both workspaces, replaced by the ``ament_python`` layout.
- The old ``topic_based_ros2_control`` dependency on Jazzy (now integrated into ``ros2_control`` for Jazzy onward).

Fixed
^^^^^
- **Windows launch support** for Isaac Sim:

  - ``run_isaacsim`` launcher fix for Pixi/Windows.
  - ``--exec`` quoting on Windows (cmd.exe does not strip single quotes) so the ``gui:=`` USD path opens correctly.
  - Replaced POSIX-only ``start_new_session=True`` with ``creationflags=CREATE_NEW_PROCESS_GROUP`` for the Isaac Sim subprocess.
  - ``use_internal_libs``/``ros_installation_path`` now exit non-zero with a clear error on Windows instead of silently exiting.
  - Windows robot state publisher command fix.

- ``isaac_moveit`` (Jazzy): malformed JointState warnings on ``/isaac_joint_commands`` and the mimic-loop fault that destabilized ``panda_arm_controller``.
- Launch-file fixes for Windows; scan-topic launch fix for local/global costmaps in navigation samples.

6.0.0 Early Developer Release
=============================

Release Highlights
------------------

General
^^^^^^^

- Updated to `Kit 110.0 <https://docs.omniverse.nvidia.com/dev-guide/latest/release-notes/110_0_highlights.html>`__

  - Support for 3D Gaussian Splatting with Fabric Scene Delegate integration, multi-GPU rendering, light interaction with mesh scenes, and MaterialX support.
  - CAD and DGN Converter enhancements with ACIS solid modeling support, BSplineSurface translation, and enhanced tessellation controls.
  - Nested rigid body physics with GPU acceleration, and significant RTX rendering improvements enhance both visual fidelity and simulation accuracy.
  - Expanded XR support, improved Scene Optimizer tools, and Fabric Scene Delegate performance enhancements.

- Extend the integration/usage of the Core Experimental API into the source code.
- New extensions based on the Core Experimental API with updated interfaces.

PhysX and Newton
^^^^^^^^^^^^^^^^

- Experimental support for the Newton physics engine

  - Newton/MuJoCo-Warp solver can be used as a physics simulation backend.
  - ``isaacsim.core.experimental.prims`` APIs can be used with both PhysX and Newton.

Synthetic Data Generation
^^^^^^^^^^^^^^^^^^^^^^^^^

- **Perception Data Generation (Replicator)**

  - Getting started example using various optimized randomizations using write to fabric (``enableWriteToFabric``) and skip syncing with stage (``wait_for_render``).
  - Useful snippet example using deformable assets with the Core Experimental API to generate synthetic data.

- **Action and Event Data Generation**

  - *AgentSim (isaacsim.replicator.agent)*: IRA introduces a character USD schema stored within USD files for cross-scene portability, and a config-driven method to spawn characters and issue character behaviors. IRA features a new UI for configuring agent simulations. IRA and scene captioning (IRC) now work together in a single pipeline, producing both annotated sensor data and VLM captions from one simulation run.
  - *Object Simulation and Physics (isaacsim.replicator.object)*: IRO now supports randomization of physics attributes (mass, friction, restitution) across scene objects for domain-randomized synthetic data generation. New placement strategies (pyramid stacking, world/local-space force application) to enable a variety of physical scenes.
  - *Incident Simulation (isaacsim.replicator.incident)*: Extended toppling events now apply to a broader set of objects. A new FlowUSD fire and smoke writer captures volumetric fire and smoke data from NVIDIA Flow alongside standard SDG outputs (RGB, depth, semantic segmentation).
  - *Sensors (isaacsim.sensor.rtx.placement, isaacsim.sensor.rtx.calibration)*: Maximum coverage based camera placement now supports placement randomization. A new Omniverse-native API for sensor calibration provides direct access to camera intrinsics, extrinsics, and field-of-view coverage visualization.

Robots
^^^^^^

- **Isaac Sim URDF Importer 3.0**: Exports to Asset Structure 3.0, multi-engine backend support with MuJoCo to PhysX conversion, Newton schema support, new UI and API, standalone Python interface, and joint tuning moved to gains tuner. New UI for ROS robot state based imports (``isaacsim.ros2.urdf``).
- **Isaac Sim MJCF Importer 3.0**: Asset Structure 3.0, multi-engine backend support with URDF to MuJoCo and PhysX conversion, Newton schema support, new UI and API, standalone Python interface, and joint tuning moved to gains tuner.
- **Asset Structure 3.0**: USDC (binary) for geometry; Material, Instances, Base, Physics defined in USDA (ascii) for easier version control and readability. Separated physics, MuJoCo, and PhysX definitions for different tuning values.
- **Asset Transformer**: Rule-based USD tool for performing USD operations on assets. Comes with profile to convert robot assets to Asset Structure 3.0. Available rules include: generate robot schema, make schemas non-explicit, prim/schema/attribute routing, variant composition, geometry deduplication, shared materials between geometries.
- **Gains Tuner**: Migrated to use ``core.experimental.prims``, enabling Newton backend.
- **Robot Poser**: Create robot named poses to change robot pose configuration, and manipulate robot based on a given link position on task space.
- **Robot Self Collision Detector**: Visually detecting overlapping colliders in a robot.
- **Robot Inspector**: Robot inspector window to enable viewing robot links and prims as flattened or nested. Interactively fix or disable robot joints for debugging.

Sensors
^^^^^^^

- **Cameras and Depth Sensors**: ``isaacsim.sensors.camera`` deprecated in favor of ``isaacsim.sensors.experimental.camera``. Camera sensor now uses ``_fast`` annotator variants for improved performance. Fixed tiled sensor data slicing.
- **RTX Non-Visual Sensors**: Added explicit RTX Radar support via new Annotator. RTX Sensor models now use Hydra time (``omni.timeline``) for accurate simulation time tracking. Scan accumulation and post-processing moved to host by default, reducing GPU resource contention. Fixed point cloud "flickering" and broken scans when using RTX Lidar. New and updated standalone examples.
- **Physics Sensors**: ``isaacsim.sensors.physics`` deprecated in favor of ``isaacsim.sensors.experimental.physics``. Added dedicated GPU codepath for IMU sensor using a separate CUDA stream and pinned memory buffer for improved performance.

ROS
^^^

- **Architecture and Modularization**: The monolithic ``isaacsim.ros2.bridge`` extension was split into focused extensions: ``isaacsim.ros2.core`` (core libraries and message backends), ``isaacsim.ros2.nodes`` (OmniGraph nodes), ``isaacsim.ros2.ui`` (UI components), and ``isaacsim.ros2.examples`` (sample code and demos).
- **ROS 2 Jazzy**: System level installations can now be sourced directly with Isaac Sim, enabled by full Python 3.12 support.
- ROS 2 H.264 compressed RGB image support with hardware-accelerated encoding.
- RTX Lidar metadata (e.g., intensity) can now be included in ROS 2 PointCloud2 messages.
- Experimental support for any ROS 2 distribution built with Python 3.12.
- Added ``rclpy`` MultiThreadedExecutor-based async spinning to the ROS 2 test case base class.

Docker
^^^^^^

- Added Docker Compose deployment for Isaac Sim + WebRTC web-viewer as a single stack.
- Support for running multiple Isaac Sim instances in parallel on a single machine.
- Full Docker container support for DGX Spark.

Live-streaming
^^^^^^^^^^^^^^

- Added web-based livestreaming via WebRTC client accessible through Docker Compose.
- Configurable signal port and stream port via environment variables.
- Full DGX Spark livestreaming support.

Motion Generation
^^^^^^^^^^^^^^^^^

- **New Experimental Motion Generation API**: Includes new tools to easily populate and synchronize a planning scene to the USD stage with independent collision geometry representation. Includes a new controller composition framework that allows simple controllers to be combined to build more complex controllers.
- **New cuMotion Integration**: Added full integration with NVIDIA's cuMotion library, built on the new experimental motion generation API. Includes a centralized collision world state which can be passed to any collision-aware algorithm. Includes bindings to several trajectory and real-time planning algorithms, including minimal-time collision-aware trajectory planning with very flexible end-effector constraints.

SimReady Content
^^^^^^^^^^^^^^^^

- Experimental search functions that extend the content browser with "Assets Search" mode: search SimReady Profiles, Features, natural language search, and tags.
- A new curated collection of SimReady assets is available in the Content Browser, including robot models from FANUC. These assets have passed both USD validation and runtime tests for improved out-of-the-box reliability.

  - 85 Fanuc Robots
  - 1 Comau
  - 1000 SimReady Props

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



