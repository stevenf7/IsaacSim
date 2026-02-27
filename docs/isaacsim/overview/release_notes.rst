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

6.0.0 Early Developer Release
=============================

- Updated to Kit SDK 109.0.2
- Updated to Python 3.12
- Updated to use RT 2.0 rendering mode by default
- In the early developer release, Neural Reconstruction (NuRec) scenes which include a matte object will not render correctly. To avoid this, you may disable the matte object by making it invisible, or you can force the older RT 1.0 rendering mode using these command-line settings:
  
  ``--/persistent/rtx/modes/rt/enabled=true``
  ``--/rtx/rendermode=RaytracedLighting``

Kit SDK Version
---------------

Changed: 107.3.3+isaac.229672.69cbf6ad.gl -> 109.0.2+production.256123.dc36eb6f.gl

Dependencies
------------

Added
^^^^^
- isaacsim.replicator.agent.schema: 0.0.1
- isaacsim.replicator.incident.core: 0.11.2
- isaacsim.replicator.incident.ui: 0.6.0
- isaacsim.replicator.object.core: 0.11.3
- isaacsim.replicator.object.ui: 0.11.1
- isaacsim.sensors.rtx.calibration: 0.3.2
- omni.ai.langchain.agent.chat_iro: 2.2.5
- omni.ai.langchain.core: 2.2.0
- omni.ai.langchain.widget.core: 3.0.0
- omni.anim.behavior.asset: 109.0.6
- omni.anim.behavior.bundle: 109.0.6
- omni.anim.behavior.core: 109.0.7
- omni.anim.behavior.ui: 109.0.6
- omni.behavior.composer: 0.5.3
- omni.behavior.composer.schema: 0.4.0
- omni.behavior.composer.ui: 0.5.2
- omni.kit.livestream.app: 9.0.0
- omni.mesh_tools.libs: 109.0.8
- omni.replicator.nv: 1.0.0
- omni.scene.optimizer.analysis: 109.0.2
- omni.scene.optimizer.validators: 109.0.2

Removed
^^^^^^^
- isaacsim.replicator.incident: 0.1.28
- isaacsim.replicator.object: 0.4.13
- isaacsim.xr.input_devices: 1.0.2
- isaacsim.xr.openxr: 1.0.0
- omni.anim.people: 0.7.9
- omni.cuopt.examples: 1.3.0
- omni.kit.streamsdk.plugins: 7.6.3
- omni.kit.window.modifier.titlebar: 105.2.16
- omni.kit.xr.advertise: 107.3.109
- omni.kit.xr.profile.ar: 107.3.109
- omni.kit.xr.profile.common: 107.3.109
- omni.kit.xr.profile.tabletar: 107.3.109
- omni.kit.xr.profile.vr: 107.3.109
- omni.kit.xr.scene_view.core: 107.3.109
- omni.kit.xr.scene_view.utils: 107.3.109
- omni.services.livestream.nvcf: 7.2.0

Changed
^^^^^^^
- isaacsim.action_and_event_data_generation.setup: 0.0.9 -> 0.6.0
- isaacsim.anim.robot: 0.0.15 -> 1.0.3
- isaacsim.exp.full: 5.1.0 -> 6.0.0
- isaacsim.replicator.agent.core: 0.7.28 -> 1.0.11
- isaacsim.replicator.agent.ui: 0.7.11 -> 1.0.7
- isaacsim.replicator.caption.core: 0.0.32 -> 0.6.6
- isaacsim.sensors.rtx.placement: 0.6.14 -> 0.16.4
- isaacsim.util.debug_draw: 3.1.0 -> 3.2.0
- omni.anim.asset: 107.3.0 -> 109.0.6
- omni.anim.behavior.schema: 107.3.0 -> 109.0.6
- omni.anim.curve.bundle: 1.2.3 -> 1.3.0
- omni.anim.curve.core: 1.3.1 -> 1.5.3
- omni.anim.curve.ui: 1.4.1 -> 1.6.1
- omni.anim.curve_editor: 106.4.1 -> 109.0.0
- omni.anim.graph.bundle: 107.3.3 -> 109.0.6
- omni.anim.graph.core: 107.3.4 -> 109.0.6
- omni.anim.graph.schema: 107.3.3 -> 109.0.6
- omni.anim.graph.ui: 107.3.3 -> 109.0.6
- omni.anim.navigation.bundle: 107.3.3 -> 109.0.6
- omni.anim.navigation.core: 107.3.8 -> 109.0.6
- omni.anim.navigation.schema: 107.3.3 -> 109.0.6
- omni.anim.navigation.ui: 107.3.6 -> 109.0.6
- omni.anim.retarget.bundle: 107.3.3 -> 109.0.6
- omni.anim.retarget.core: 107.3.3 -> 109.0.6
- omni.anim.retarget.preview: 107.3.3 -> 109.0.6
- omni.anim.retarget.ui: 107.3.3 -> 109.0.6
- omni.anim.shared.core: 107.0.1 -> 109.0.2
- omni.anim.skelJoint: 107.3.3 -> 109.0.6
- omni.anim.timeline: 107.0.0 -> 109.0.1
- omni.anim.widget.timeline: 0.1.14 -> 0.3.0
- omni.anim.window.timeline: 106.5.0 -> 109.0.2
- omni.asset_validator.core: 1.1.6 -> 1.8.0
- omni.asset_validator.ui: 1.1.6 -> 1.8.0
- omni.convexdecomposition: 107.3.26 -> 109.0.10
- omni.cuopt.service: 1.3.0 -> 1.3.1
- omni.cuopt.visualization: 1.3.0 -> 1.3.2
- omni.curve.manipulator: 107.0.4 -> 108.2.0
- omni.flowusd: 107.1.8 -> 109.0.2
- omni.genproc.core: 107.0.3 -> 109.0.0
- omni.graph.action: 1.130.0 -> 2.0.0
- omni.graph.action_nodes: 1.50.4 -> 2.0.2
- omni.graph.action_nodes_core: 1.2.0 -> 2.0.1
- omni.graph.bundle.action: 2.30.0 -> 3.0.1
- omni.graph.examples.cpp: 1.50.2 -> 2.0.1
- omni.graph.nodes: 1.170.10 -> 2.1.5
- omni.graph.nodes_core: 1.1.0 -> 2.0.3
- omni.graph.scriptnode: 1.50.0 -> 2.1.2
- omni.graph.telemetry: 2.40.2 -> 3.1.3
- omni.graph.ui: 1.101.6 -> 2.1.5
- omni.graph.ui_nodes: 1.50.5 -> 2.0.3
- omni.graph.visualization.nodes: 2.1.3 -> 2.1.4
- omni.graph.window.action: 1.50.2 -> 2.2.1
- omni.graph.window.core: 2.0.0 -> 3.1.0
- omni.graph.window.generic: 1.50.2 -> 2.2.1
- omni.importer.onshape: 1.0.1 -> 2.0.1
- omni.kit.asset_converter: 5.0.17 -> 5.0.22
- omni.kit.browser.asset: 1.3.12 -> 1.3.15
- omni.kit.browser.core: 2.3.13 -> 2.3.17
- omni.kit.browser.folder.core: 1.10.9 -> 1.12.1
- omni.kit.browser.material: 1.6.2 -> 1.6.5
- omni.kit.converter.cad: 205.0.0 -> ~207.0
- omni.kit.converter.common: 507.1.2 -> 508.0.1
- omni.kit.converter.dgn: 509.1.0 -> 509.3.0
- omni.kit.converter.dgn_core: 510.1.0 -> 511.2.0
- omni.kit.converter.hoops: 509.1.0 -> 509.2.4
- omni.kit.converter.hoops_core: 509.1.0 -> 510.1.3
- omni.kit.converter.jt: 508.1.0 -> 508.2.5
- omni.kit.converter.jt_core: 508.1.0 -> 508.2.7
- omni.kit.core.collection: 0.2.3 -> 0.2.4
- omni.kit.data2ui.core: 1.1.2 -> 1.1.4
- omni.kit.data2ui.usd: 1.1.2 -> 1.1.4
- omni.kit.environment.core: 1.3.24 -> 1.4.1
- omni.kit.gfn: 107.0.4 -> 108.0.0
- omni.kit.graph.delegate.default: 1.2.3 -> 1.2.5
- omni.kit.graph.delegate.modern: 1.10.9 -> 1.10.11
- omni.kit.graph.editor.core: 1.5.3 -> 1.5.4
- omni.kit.graph.usd.commands: 1.3.1 -> 1.3.2
- omni.kit.graph.widget.variables: 2.1.0 -> 2.1.1
- omni.kit.livestream.core: 7.5.0 -> 9.0.0
- omni.kit.livestream.webrtc: 7.0.0 -> 9.0.2
- omni.kit.mesh.raycast: 107.0.1 -> 108.0.0
- omni.kit.playlist.core: 1.3.5 -> 1.3.7
- omni.kit.pointclouds: 1.5.14 -> 1.6.5
- omni.kit.preferences.animation: 1.2.0 -> 1.4.0
- omni.kit.prim.icon: 1.0.15 -> 1.1.0
- omni.kit.profiler.window: 2.3.5 -> 2.3.7
- omni.kit.property.collection: 0.2.3 -> 0.2.4
- omni.kit.property.environment: 1.2.2 -> 1.2.3
- omni.kit.property.physx: 107.3.26 -> 109.0.10
- omni.kit.scripting: 107.3.2 -> 109.0.4
- omni.kit.sequencer.core: 108.0.2 -> 108.1.1
- omni.kit.sequencer.usd: 108.0.2 -> 108.1.1
- omni.kit.stage_column.payload: 2.0.3 -> 2.0.5
- omni.kit.stage_column.variant: 1.0.17 -> 1.0.20
- omni.kit.stagerecorder.bundle: 105.0.2 -> 109.0.0
- omni.kit.stagerecorder.core: 107.0.3 -> 109.0.0
- omni.kit.stagerecorder.ui: 107.0.1 -> 109.0.0
- omni.kit.thumbnails.mdl: 1.0.27 -> 1.0.28
- omni.kit.timeline.minibar: 1.2.11 -> 1.2.13
- omni.kit.tool.asset_importer: 4.3.2 -> 5.1.3
- omni.kit.tool.measure: 107.0.2 -> 200.0.4
- omni.kit.tool.remove_unused.controller: 0.1.4 -> 0.2.0
- omni.kit.tool.remove_unused.core: 0.1.3 -> 0.1.4
- omni.kit.variant.editor: 107.5.3 -> 107.5.6
- omni.kit.variant.presenter: 107.0.0 -> 107.1.1
- omni.kit.viewport.menubar.lighting: 107.3.1 -> 107.3.2
- omni.kit.waypoint.core: 1.4.62 -> 1.6.3
- omni.kit.waypoint.playlist: 1.0.9 -> 1.1.1
- omni.kit.widget.collection: 0.3.1 -> 0.3.3
- omni.kit.widget.material_preview: 1.0.16 -> 1.1.2
- omni.kit.widget.schema_api: 1.0.3 -> 1.0.4
- omni.kit.widget.sliderbar: 1.0.13 -> 1.1.0
- omni.kit.widget.timeline: 107.0.1 -> 107.0.2
- omni.kit.widget.zoombar: 1.0.6 -> 1.0.7
- omni.kit.widgets.custom: 1.0.13 -> 1.1.2
- omni.kit.window.collection: 0.3.1 -> 0.3.4
- omni.kit.window.material: 1.7.2 -> 1.8.0
- omni.kit.window.material_graph: 1.9.1 -> 1.9.5
- omni.kit.window.movie_capture: 2.5.6 -> 2.7.3
- omni.kit.window.section: 107.0.3 -> 107.1.2
- omni.kit.window.usddebug: 1.1.2 -> 1.1.4
- omni.kit.xr.core: 107.3.109 -> 109.0.0
- omni.kit.xr.system.openxr: 107.3.109 -> 109.0.0
- omni.kit.xr.system.simulatedxr: 107.3.109 -> 109.0.0
- omni.kit.xr.ui.stage: 107.3.109 -> 109.0.0
- omni.kit.xr.ui.window.profile: 107.3.109 -> 109.0.0
- omni.kit.xr.ui.window.viewport: 107.3.109 -> 109.0.0
- omni.kvdb: 107.3.26 -> 109.0.10
- omni.localcache: 107.3.26 -> 109.0.10
- omni.metropolis.utils: 0.1.20 -> 0.14.7
- omni.no_code_ui.bundle: 1.1.2 -> 1.1.4
- omni.physics: 107.3.26 -> 109.0.10
- omni.physics.physx: 107.3.26 -> 109.0.10
- omni.physics.stageupdate: 107.3.26 -> 109.0.10
- omni.physics.tensors: 107.3.26 -> 109.0.10
- omni.physx: 107.3.26 -> 109.0.10
- omni.physx.asset_validator: 107.3.26 -> 109.0.10
- omni.physx.bundle: 107.3.26 -> 109.0.10
- omni.physx.camera: 107.3.26 -> 109.0.10
- omni.physx.cct: 107.3.26 -> 109.0.10
- omni.physx.commands: 107.3.26 -> 109.0.10
- omni.physx.cooking: 107.3.26 -> 109.0.10
- omni.physx.demos: 107.3.26 -> 109.0.10
- omni.physx.fabric: 107.3.26 -> 109.0.10
- omni.physx.foundation: 107.3.26 -> 109.0.10
- omni.physx.graph: 107.3.26 -> 109.0.10
- omni.physx.pvd: 107.3.26 -> 109.0.10
- omni.physx.supportui: 107.3.26 -> 109.0.10
- omni.physx.telemetry: 107.3.26 -> 109.0.10
- omni.physx.tensors: 107.3.26 -> 109.0.10
- omni.physx.tests: 107.3.26 -> 109.0.10
- omni.physx.tests.visual: 107.3.26 -> 109.0.10
- omni.physx.ui: 107.3.26 -> 109.0.10
- omni.physx.vehicle: 107.3.26 -> 109.0.10
- omni.ramp: 107.0.1 -> 107.0.2
- omni.replicator.core: 1.12.27 -> 1.12.34
- omni.scene.optimizer.bundle: 107.3.12 -> 109.0.2
- omni.scene.optimizer.core: 107.3.12 -> 109.0.2
- omni.scene.optimizer.ui: 107.3.12 -> 109.0.2
- omni.scene.visualization.core: 107.0.2 -> 109.0.1
- omni.services.client: 0.5.3 -> 0.5.4
- omni.services.convert.asset: 508.0.2 -> 509.0.0
- omni.services.convert.cad: 507.0.2 -> 507.1.5
- omni.services.core: 1.9.0 -> 1.9.3
- omni.services.facilities.base: 1.0.4 -> 1.0.5
- omni.services.facilities.monitoring.metrics: 0.3.0 -> 0.3.1
- omni.services.pip_archive: 0.16.0 -> 0.18.3
- omni.services.starfleet.auth: 0.1.5 -> 0.1.6
- omni.services.transport.client.base: 1.2.4 -> 1.2.5
- omni.services.transport.client.http_async: 1.4.0 -> 1.4.2
- omni.services.transport.server.base: 1.1.1 -> 1.1.2
- omni.services.transport.server.http: 1.3.1 -> 1.3.2
- omni.services.transport.server.zeroconf: 1.0.9 -> 1.0.10
- omni.services.usd: 1.1.0 -> 1.1.1
- omni.simready.explorer: 1.1.3 -> 1.1.4
- omni.tools.array: 107.0.0 -> 108.0.0
- omni.usd.fileformat.e57: 1.4.3 -> 1.7.0
- omni.usd.fileformat.pts: 107.1.1 -> 108.0.0
- omni.usd.metrics.assembler: 107.3.1 -> 109.0.0
- omni.usd.metrics.assembler.physics: 107.3.26 -> 109.0.10
- omni.usd.metrics.assembler.ui: 107.3.1 -> 109.0.0
- omni.usd.schema.flow: 107.1.1 -> 109.0.1
- omni.usd.schema.metrics.assembler: 107.3.1 -> 109.0.0
- omni.usd.schema.physx: 107.3.26 -> 109.0.10
- omni.usd.schema.sequence: 3.0.1 -> 3.1.2
- omni.usdex.libs: 1.2.2 -> 2.1.2
- omni.usdphysics: 107.3.26 -> 109.0.10
- omni.usdphysics.ui: 107.3.26 -> 109.0.10
- omni.vdb_timesample_editor: 0.2.0 -> 0.2.3
- omni.warp: 1.8.2 -> 1.10.0
- omni.warp.core: 1.8.2 -> 1.10.0

Extensions
==========

- **isaacsim.app.about**

    - Changed

      - Update description

- **isaacsim.app.setup**

    - Changed

      - Add wait for viewport to be ready before printing app ready status
      - Change startup behavior so that app ready status is delayed until after the app has started
      - Remove unused imports
      - Remove unused omni.pip.cloud from test dependencies
      - Remove extra omni.rtx.settings.core from test dependencies
      - Make omni.isaac.ml_archive an explicit test dependency

- **isaacsim.asset.browser**

    - Changed

      - Update assets path
      - Migrate extension implementation to core experimental API
      - Remove omni.pip.cloud from extension.toml
      - Remove requests dependency, use urllib instead

    - Fixed

      - Update unit tests for kit 109.0
      - Add missing documentation for the asset browser extension
      - Replaced deprecated `onclick_fn` with `onclick_action` in "Isaac Sim Assets" menu item to eliminate deprecation warnings
      - Registered proper toggle action for the asset browser
      - Fix issue where cache json file could not be created if the cache directory did not exist

- **isaacsim.asset.exporter.urdf**

    - Changed

      - Update lxml==6.0.2
      - Migrate extension implementation to core experimental API
      - Make omni.isaac.ml_archive an explicit test dependency

- **isaacsim.asset.gen.conveyor**

    - Changed

      - Update to Kit 109 and Python 3.12

- **isaacsim.asset.gen.conveyor.ui**

    - Changed

      - Migrate to Events 2.0.

- **isaacsim.asset.gen.omap**

    - Changed

      - Update to use new debug draw plugin interface
      - Improve docstrings and cleanup codebase
      - Update to Kit 109 and Python 3.12
      - Migrate extension implementation to core experimental API
      - Add omni.physics.stageupdate to extension.toml

- **isaacsim.asset.gen.omap.ui**

    - Changed

      - Migrate to Events 2.0.
      - Refactor codebase and improve docstrings
      - Migrate extension implementation to core experimental API
      - Make omni.isaac.ml_archive an explicit test dependency

- **isaacsim.asset.importer.heightmap**

    - Changed

      - Renamed Block World Generator to Heightmap Importer
      - Refactored to separate importer logic from extension UI
      - Standardized terminology from "block world" to "heightmap" throughout codebase
      - Updated all documentation, comments, and test names to use heightmap terminology
      - Migrate extension implementation to core experimental API
      - Make omni.isaac.ml_archive an explicit test dependency

- **isaacsim.asset.importer.mjcf**

    - Changed

      - Update description
      - Update to Kit 109 and Python 3.12

- **isaacsim.asset.importer.urdf**

    - Changed

      - Update description
      - Migrate to Events 2.0.
      - Add missing docstrings
      - Restore deprecated behavior of merging bodies with inertia; issue warning
      - Update to Kit 109 and Python 3.12

    - Fixed

      - Fixed issue that caused crash of Isaac sim on failed mesh conversion

- **isaacsim.asset.validation**

    - Changed

      - Migrate PhysX subscription and simulation control interfaces to Omni Physics

- **isaacsim.benchmark.examples**

    - Changed

      - Update description
      - Make omni.isaac.ml_archive an explicit test dependency

- **isaacsim.benchmark.services**

    - Added

      - Add error handling if set_phase() is called without a matching store_measurements()

    - Removed

      - Removed stop_recording_runtime arg to benchmark.store_measurements()

    - Changed

      - Converted log statements to use logger for independent visibility control
      - Update description
      - Migrate to Events 2.0.
      - Get the CUDA device names using Warp API
      - Make omni.isaac.ml_archive an explicit test dependency
      - Migrate PhysX subscription and simulation control interfaces to Omni Physics

    - Fixed

      - Write privacy.toml file to temporary directory

- **isaacsim.code_editor.jupyter**

    - Changed

      - Migrate to Events 2.0.

- **isaacsim.core.api**

    - Changed

      - Migrate to Events 2.0.
      - Add missing docstrings
      - Update to Kit 109 and Python 3.12
      - Remove unused omni.pip.cloud from dependencies
      - Replace import statements with the deprecation function when importing PyTorch
      - Make omni.isaac.ml_archive an explicit test dependency
      - Remove extra carb settings from tests
      - Migrate PhysX subscription and simulation control interfaces to Omni Physics

- **isaacsim.core.cloner**

    - Changed

      - Fix clang tidy issues in cpp code
      - Add missing docstrings
      - Update to Kit 109 and Python 3.12
      - Convert input arguments to NumPy without explicitly import PyTorch
      - Migrate PhysX subscription and simulation control interfaces to Omni Physics

- **isaacsim.core.deprecation_manager**

    - Added

      - Expose function to import a deprecated/removed module safely

    - Changed

      - Removed code to enable the `omni.isaac.ml_archive` extension when importing PyTorch via `import_module`
      - Enable the `omni.isaac.ml_archive` extension when importing PyTorch via `import_module`

- **isaacsim.core.experimental.materials**

    - Removed

      - Remove checking for the deformable beta feature, as it is now active by default

    - Changed

      - Define ranges for visual material inputs and clip them accordingly
      - Standardize test args in extension.toml

- **isaacsim.core.experimental.objects**

    - Changed

      - Define the `reset_xform_op_properties` parameter to True by default for all objects

- **isaacsim.core.experimental.prims**

    - Removed

      - Remove checking for the deformable beta feature, as it is now active by default

    - Changed

      - Migrate to Events 2.0
      - Update check condition on DOF to ensure it checks if it's a valid DOF before checking limits
      - Update implementation to Warp 1.10.0
      - Update array output in docstrings example due to changes in the NumPy representation
      - Make isaacsim.storage.native an explicit test dependency
      - Replace the use of deprecated core utils functions within implementations
      - Migrate PhysX subscription and simulation control interfaces to Omni Physics

    - Fixed

      - Fix physics setup when a prim instance is created while the simulation is running

- **isaacsim.core.experimental.utils**

    - Added

      - Add timeline-related functions to app utils
      - Add xform utils
      - Support USD schemas when getting a prim or prim path
      - Add app utils
      - Add semantics utils
      - Add stage utils functions to:
      - Check whether the stage is loading
      - Generate a string representation of the stage
      - Move a prim to a different location on the stage hierarchy
      - Delete a prim from the stage
      - Add prim utils functions to:
      - Find all the prim paths in the stage that match the given (regex) path
      - Check whether a prim corresponds to a non-root link in an articulation

    - Changed

      - Update app module docstrings example and add module summaries for docs purposes
      - Return the input as it is when getting a prim or prim path, provided that the input is of the expected return type

- **isaacsim.core.includes**

    - Changed

      - Run clang tidy
      - Migrate BaseResetNode to Events 2.0.
      - Update to Kit 109 and Python 3.12

- **isaacsim.core.nodes**

    - Changed

      - Migrate OgnOnPhysicsStep to Events 2.0.
      - Update description
      - Migrate to Events 2.0.
      - Set ResetOnStop to True for all Simulation Time OG nodes
      - Moved handle interface to isaacsim.ros2.nodes extension where it was used.
      - Update to Kit 109 and Python 3.12
      - Update deprecated python unittest methods
      - Make omni.isaac.ml_archive an explicit test dependency
      - Remove deprecated dependencies
      - Remove deprecated time related APIs from CoreNodes interface
      - Remove extra carb settings from tests

- **isaacsim.core.prims**

    - Changed

      - Migrate to Events 2.0.
      - Replace import statements with the deprecation function when importing PyTorch
      - Make omni.isaac.ml_archive an explicit test dependency
      - Migrate PhysX subscription and simulation control interfaces to Omni Physics

    - Fixed

      - Fix the `PhysxCollisionAPI` schema when checking for collision properties

- **isaacsim.core.simulation_manager**

    - Added

      - Add the `SimulationEvent` enum
      - Allow to perform a fabric update when stepping physics

    - Changed

      - Run clang tidy
      - Raise a RuntimeError if the physics dt is being set while simulation is running/playing
      - Mark as deprecated the `IsaacEvents` enum and the backend-related methods
      - Make set_physics_dt a classmethod
      - Add unit tests for SimulationManager
      - Update to Kit 109 and Python 3.12
      - Replace the use of deprecated core utils functions by the core experimental implementations
      - Migrate PhysX subscription and simulation control interfaces to Omni Physics

- **isaacsim.core.throttling**

    - Changed

      - Migrate to Events 2.0.
      - Remove extra carb settings from tests

- **isaacsim.core.utils**

    - Removed

      - Removed deprecated `nucleus` module (use `isaacsim.storage.native` instead):
      - `get_url_root`, `create_folder`, `delete_folder`, `_list_files`, `download_assets_async`
      - `check_server`, `check_server_async`, `build_server_list`, `find_nucleus_server`
      - `get_server_path`, `get_server_path_async`, `verify_asset_root_path`
      - `get_full_asset_path`, `get_full_asset_path_async`
      - `get_nvidia_asset_root_path`, `get_isaac_asset_root_path`
      - `get_assets_root_path`, `get_assets_root_path_async`, `get_assets_server`
      - `_collect_files`, `is_dir_async`, `is_file_async`, `is_file`
      - `recursive_list_folder`, `list_folder`
      - Removed deprecated `create_hydra_texture` from `render_product` (use `omni.replicator.core.create.render_product` instead)
      - Removed deprecated semantics functions using old SemanticsAPI (use new LabelsAPI equivalents):
      - `add_update_semantics` -> use `add_labels`
      - `remove_all_semantics` -> use `remove_labels`
      - `get_semantics` -> use `get_labels`
      - `check_missing_semantics` -> use `check_missing_labels`
      - `check_incorrect_semantics` -> use `check_incorrect_labels`
      - `count_semantics_in_scene` -> use `count_labels_in_scene`

    - Changed

      - set_camera_prim_path now also applies the OmniRtxCameraExposureAPI_1 schema to the camera prim
      - set_camera_prim_path now also sets the exposure:time attribute to 0.02
      - Add missing docstrings
      - Update to Kit 109 and Python 3.12
      - Fix invalid escape sequences
      - Update deprecated python unittest methods
      - Replace import statements with the deprecation function when importing PyTorch
      - Make omni.isaac.ml_archive an explicit test dependency
      - Remove deprecated dependencies
      - Migrate PhysX subscription and simulation control interfaces to Omni Physics

- **isaacsim.cortex.behaviors**

    - Changed

      - Make omni.isaac.ml_archive an explicit test dependency

- **isaacsim.examples.browser**

    - Fixed

      - Replaced deprecated `onclick_fn` with `onclick_action` in "Robotics Examples" menu item to eliminate deprecation warnings
      - Registered proper toggle action for the examples browser

- **isaacsim.examples.extension**

    - Changed

      - Fix event name usage.
      - Migrate to Events 2.0.
      - Make omni.isaac.ml_archive an explicit test dependency
      - Migrate PhysX subscription and simulation control interfaces to Omni Physics

- **isaacsim.examples.interactive**

    - Removed

      - base_sample_experimental.py
      - base_sample_extension_experimental.py
      - Build window function use
      - The Simple Stack example
      - The Franka Pick-and-Place and UR10 Follow Target examples have been removed from this extension and moved to a new location

    - Changed

      - Update description
      - Migrate to Events 2.0.
      - Updated inference examples to use GPU physics and the new experimental APIs
      - Moved policy based examples to isaacsim.robot.policy.examples
      - Add missing docstrings
      - Update imports from isaacsim.base_samples to isaacsim.examples.base
      - The Start with Robot, Kaya Gamepad, Omnigraph Keyboard, and Hello World examples now depend on the new Warp-based APIs
      - Make omni.isaac.ml_archive an explicit test dependency
      - Remove deprecated dependencies
      - Remove extra carb settings from tests
      - Migrate PhysX subscription and simulation control interfaces to Omni Physics

    - Fixed

      - Fix Kaya Gamepad example test

- **isaacsim.examples.ui**

    - Changed

      - Rename startup.py to test_startup.py

- **isaacsim.gui.components**

    - Changed

      - Add missing docstrings
      - Migrate extension implementation to core experimental API
      - Make omni.isaac.ml_archive an explicit test dependency
      - Migrate PhysX subscription and simulation control interfaces to Omni Physics

- **isaacsim.gui.content_browser**

    - Changed

      - Fix missing icon error in Isaac content browser
      - Update description
      - Revert the protocol to match the current Isaac Sim version
      - Fix navigation issue caused by incorrect protocol
      - Update assets path
      - Update to Kit 109 and Python 3.12

    - Fixed

      - Fix getting Carb settings API for protocol designation

- **isaacsim.gui.menu**

    - Changed

      - Update golden image for environment test
      - Update description
      - Renamed Block World Generator to Heightmap Importer
      - Make omni.isaac.ml_archive an explicit test dependency

- **isaacsim.gui.property**

    - Added

      - Introduced widgets for the Robot Schema

    - Changed

      - Add missing license headers

- **isaacsim.gui.sensors.icon**

    - Removed

      - Remove the deprecated and unused isaacsim.core.utils dependency

    - Changed

      - Update description
      - Migrate to Events 2.0.
      - Update test module import

- **isaacsim.replicator.behavior**

    - Changed

      - Added explicit seed to randomizers to make them deterministic
      - Updated sdg pipeline golden images
      - Make omni.isaac.ml_archive an explicit test dependency
      - Migrate PhysX subscription and simulation control interfaces to Omni Physics

- **isaacsim.replicator.behavior.ui**

    - Changed

      - Update test module import

- **isaacsim.replicator.domain_randomization**

    - Changed

      - Replace import statements with the deprecation function when importing PyTorch
      - Make omni.isaac.ml_archive an explicit test dependency

- **isaacsim.replicator.examples**

    - Changed

      - Improved simready assets SDG example output results
      - Fixed sequential sphere scan randomizer example to work in script editor in sync with docs
      - Added explicit `.reset()` to events 2.0 subscribers in sync with docs examples
      - Migrate to Events 2.0.
      - Added an app update after switching to pathtracing in the palletizing example test
      - Fixed scatter plane parent path in scene based SDG example test
      - Fixed SDG box stacking randomizer example test by waiting for the data to be written to disk
      - Make consistent use of SimulationManager
      - Added scene based SDG example test
      - Added object based SDG example test
      - Added AMR navigation example test
      - Switched to RealtimePathTracing in the motion blur example
      - Updated replicator examples to use replicator functional api where applicable
      - Writers use explicit backends to write data to disk
      - Changed data augmentation tests to use a fixed seed in the kernel functions as well, updated golden images
      - UR10 palletizing example uses realtime pathtracing and backend for its writer
      - Switched to core.experimental rigid prims where applicable
      - Switched to SimulationManager instead of World
      - Make omni.isaac.ml_archive an explicit test dependency
      - Migrate PhysX subscription and simulation control interfaces to Omni Physics

- **isaacsim.replicator.mobility_gen**

    - Changed

      - Fix clang tidy issues in cpp code
      - Update to Kit 109 and Python 3.12
      - Update deprecated python unittest methods
      - Make omni.isaac.ml_archive an explicit test dependency

- **isaacsim.replicator.mobility_gen.examples**

    - Changed

      - Fix USD path for placement of front camera on Carter with latest USD asset
      - Fix issue where H1 and Spot policies command must be provided as torch tensor
      - Make omni.isaac.ml_archive an explicit test dependency

- **isaacsim.replicator.mobility_gen.ui**

    - Changed

      - Make omni.isaac.ml_archive an explicit test dependency

- **isaacsim.replicator.synthetic_recorder**

    - Changed

      - Migrate to Events 2.0.
      - Separated recorder and UI configuration
      - Refactored to use explicit `backend_type` and `backend_params` for custom backend support
      - Added file validation to tests and reorganized them by specific test cases for clarity and speed
      - Renamed test files (`test_recorder_outputs.py`, `test_recorder_timeline.py`)
      - Added `colorize_depth` parameter for depth visualization

- **isaacsim.replicator.writers**

    - Changed

      - Deprecate DOPEWriter and YCBVideoWriter writers
      - Deprecate OgnPose and OgnDope nodes
      - Updated pose writer to support explicit backends
      - Updated pose writer tests to use golden images and functional API
      - Replace import statements with the deprecation function when importing PyTorch
      - Make omni.isaac.ml_archive an explicit test dependency

- **isaacsim.robot.manipulators**

    - Changed

      - Update description
      - Add missing docstrings
      - Make omni.isaac.ml_archive an explicit test dependency

- **isaacsim.robot.manipulators.examples**

    - Added

      - Franka Pick-and-Place and UR10 Follow Target interactive examples

    - Removed

      - Build window function use

    - Changed

      - Updated description
      - Add missing docstrings
      - Update imports from isaacsim.base_samples to isaacsim.examples.base
      - Make omni.isaac.ml_archive an explicit test dependency

- **isaacsim.robot.manipulators.ui**

    - Changed

      - Update description
      - Make omni.isaac.ml_archive an explicit test dependency

- **isaacsim.robot.policy.examples**

    - Changed

      - Removed rendering manager test time dependency (moved to base sample)
      - Removed unnecessary dependencies
      - Removed remaining experimental api references
      - Changed the backend to experimental API using warp and torch
      - Enabled GPU physics to inference policies
      - Moved policy based interactive examples to the isaacsim.robot.policy.examples folder
      - Replace import statements with the deprecation function when importing PyTorch
      - Make omni.isaac.ml_archive an explicit test dependency
      - Migrate PhysX subscription and simulation control interfaces to Omni Physics

- **isaacsim.robot.schema**

    - Changed

      - Add missing docstrings
      - Fixed parsing of robot tree to ignore bodies in joints that are not rigid bodies
      - Updated Robot Schema definitions:
      - Removed Attributes for DofOrder
      - Created DofOrderOP list to be used with DofType tokens
      - Updated Add RobotAPI util such that it automatically scans the robot prim for Links and joints and populates it in the traversal order
      - Update to Kit 109 and Python 3.12
      - Fixed issue in `__init__.py` with running with `coverage.py`

- **isaacsim.robot.surface_gripper**

    - Changed

      - Fix clang tidy issues in cpp code
      - Update to Kit 109 and Python 3.12
      - Performance Updates
      - Make omni.isaac.ml_archive an explicit test dependency
      - Update test cases to use Python's compliant regex when instantiating the view class

- **isaacsim.robot.surface_gripper.ui**

    - Changed

      - Make omni.isaac.ml_archive an explicit test dependency

- **isaacsim.robot.wheeled_robots**

    - Changed

      - Add missing docstrings
      - Update to Kit 109 and Python 3.12
      - Delete deprecated AckermannControllerDeprecated node
      - Delete deprecated ackermann_controller_deprecated.py file
      - Fix invalid escape sequences
      - Update deprecated python unittest methods
      - Replace import statements with the deprecation function when importing PyTorch
      - Make omni.isaac.ml_archive an explicit test dependency
      - Remove deprecated dependencies

- **isaacsim.robot.wheeled_robots.ui**

    - Changed

      - Make omni.isaac.ml_archive an explicit test dependency

- **isaacsim.robot_motion.lula**

    - Changed

      - Update fix build issues with py 3.12 lula package

    - Fixed

      - Issue with python bindings for lula working with numpy 2.x

- **isaacsim.robot_motion.lula_test_widget**

    - Changed

      - Migrate to Events 2.0.
      - Add missing docstrings
      - Make omni.isaac.ml_archive an explicit test dependency
      - Migrate PhysX subscription and simulation control interfaces to Omni Physics

- **isaacsim.robot_motion.motion_generation**

    - Changed

      - Increased tolerances on flaky tests in `tests/test_trajectory_generator.py`.
      - Update to Kit 109 and Python 3.12
      - Fix invalid escape sequences
      - Replace import statements with the deprecation function when importing PyTorch
      - Make omni.isaac.ml_archive an explicit test dependency
      - Remove extra carb settings from tests

- **isaacsim.robot_setup.assembler**

    - Changed

      - Fix event name usage.
      - Migrate to Events 2.0.
      - Make omni.isaac.ml_archive an explicit test dependency
      - Remove extra carb settings from tests
      - Migrate PhysX subscription and simulation control interfaces to Omni Physics

- **isaacsim.robot_setup.gain_tuner**

    - Removed

      - Remove unused import statement and commented code

    - Changed

      - Migrate to Events 2.0.
      - Migrate PhysX subscription and simulation control interfaces to Omni Physics

    - Fixed

      - Fixed consumption of events downstream on UI builder

- **isaacsim.robot_setup.grasp_editor**

    - Changed

      - Migrate to Events 2.0.
      - Make omni.isaac.ml_archive an explicit test dependency
      - Migrate PhysX subscription and simulation control interfaces to Omni Physics

    - Fixed

      - Fixed Events 2.0 assets loaded and timeline play / stop events

- **isaacsim.robot_setup.xrdf_editor**

    - Changed

      - Considers visual mesh scaling when generating collision spheres.
      - No longer deletes portions of the robot prim when generating collision spheres.
      - Migrate to Events 2.0.
      - Add missing docstrings
      - Update deprecated numpy in1d to np.isin
      - Make omni.isaac.ml_archive an explicit test dependency
      - Migrate PhysX subscription and simulation control interfaces to Omni Physics

- **isaacsim.ros2.bridge**

    - Changed

      - Split extension into multiple extensions.
      - isaacsim.ros2.core: Core ROS 2 libraries and backend functionality
      - isaacsim.ros2.examples: ROS 2 examples
      - isaacsim.ros2.nodes: ROS 2 OmniGraph nodes and components
      - isaacsim.ros2.ui: ROS 2 UI components
      - Replace import statements with the deprecation function when importing PyTorch in tests
      - Make omni.isaac.ml_archive an explicit test dependency
      - Remove deprecated dependencies

- **isaacsim.ros2.sim_control**

    - Changed

      - Make omni.isaac.ml_archive an explicit test dependency

- **isaacsim.ros2.tf_viewer**

    - Changed

      - Added CUDA build dependencies
      - Update to Kit 109 and Python 3.12
      - Make omni.isaac.ml_archive an explicit test dependency

- **isaacsim.ros2.urdf**

    - Changed

      - Make omni.isaac.ml_archive an explicit test dependency

- **isaacsim.sensors.camera**

    - Added

      - Unit test for get_view_matrix_ros

    - Changed

      - Added validation checks and warmup warnings to camera sensor data methods to handle unavailable data
      - Added warmup tests for camera sensor checking for warnings and data availability
      - Migrate to Events 2.0.
      - Replace import statements with the deprecation function when importing PyTorch
      - Make omni.isaac.ml_archive an explicit test dependency
      - Remove deprecated time related APIs from CoreNodes interface

    - Fixed

      - Removed `do_array_copy=True` workaround in tiled sensor (fixed upstream in replicator.core 1.12.32 by changing strides type from int32 to int64 to avoid warp array arithmetic when getting annotator data)
      - Fixed issue with tiled sensor data slicing by copying the data from the annotator (do_array_copy=True)

- **isaacsim.sensors.camera.ui**

    - Added

      - New Realsense category, with D455, D457, and D55 models.

    - Removed

      - Intel as category

    - Changed

      - Make omni.isaac.ml_archive an explicit test dependency

- **isaacsim.sensors.physics**

    - Added

      - Add dedicated GPU codepath for IMU to use separate stream and pinned memory buffer

    - Changed

      - Fix clang tidy issues in cpp code
      - Migrate to Events 2.0.
      - Update to Kit 109 and Python 3.12
      - Update deprecated python unittest methods
      - Make omni.isaac.ml_archive an explicit test dependency
      - Remove deprecated time related APIs from CoreNodes interface
      - Migrate PhysX subscription and simulation control interfaces to Omni Physics

- **isaacsim.sensors.physics.examples**

    - Changed

      - Migrate to Events 2.0.
      - Make omni.isaac.ml_archive an explicit test dependency
      - Migrate PhysX subscription and simulation control interfaces to Omni Physics

- **isaacsim.sensors.physics.ui**

    - Changed

      - Make omni.isaac.ml_archive an explicit test dependency

- **isaacsim.sensors.physx**

    - Changed

      - Migrate to Events 2.0.
      - Update to Kit 109 and Python 3.12
      - Make omni.isaac.ml_archive an explicit test dependency
      - Remove extra carb settings from tests
      - Migrate PhysX subscription and simulation control interfaces to Omni Physics

- **isaacsim.sensors.physx.examples**

    - Changed

      - Migrate to Events 2.0.
      - Fix invalid escape sequences
      - Make omni.isaac.ml_archive an explicit test dependency
      - Migrate PhysX subscription and simulation control interfaces to Omni Physics

- **isaacsim.sensors.physx.ui**

    - Changed

      - Make omni.isaac.ml_archive an explicit test dependency

- **isaacsim.sensors.rtx**

    - Added

      - IsaacCreateRTXRadarPointCloud annotator to explicitly support RTX Radar
      - Link sensor_checker utility as Python module
      - Add sensor_checker to unit tests to verify supported Lidar configs

    - Removed

      - No longer dependent on RtxSensorMetadata AOV

    - Changed

      - RtxLidar.get_object_ids correctly handles GenericModelOutput.objId
      - Migrate to Events 2.0.
      - OgnIsaacCreateRTXLidarScanBuffer uses lambda function to initialize and allocate buffers
      - OgnIsaacCreateRTXLidarScanBuffer includes support for RTX Radar metadata
      - Fix tests after updating to kit 109.0.1.
      - Compute maximum points per Lidar scan from Lidar configuration
      - Update to Kit 109 and Python 3.12
      - Make omni.isaac.ml_archive an explicit test dependency
      - Exclude Simple Example Solid State config from tests

- **isaacsim.sensors.rtx.ui**

    - Changed

      - Change test to use RealTimePathTracing render mode
      - Make omni.isaac.ml_archive an explicit test dependency

- **isaacsim.simulation_app**

    - Added

      - Add carb settings for RealTimePathTracing mode
      - Fix create_new_stage not working correctly

    - Changed

      - Increased MAX_FRAMES in _wait_for_viewport for Windows so NEW_FRAME event fires when expected (again)
      - Change startup behavior so that app ready status is delayed until after the app has started
      - Increased MAX_FRAMES in _wait_for_viewport for Windows so NEW_FRAME event fires when expected
      - Add missing docstrings
      - Change default renderer to RealTimePathTracing

- **isaacsim.storage.native**

    - Added

      - Added `resolve_asset_path` function to synchronously resolve asset paths with the same logic as the async variant.

    - Changed

      - Update description
      - Add missing docstrings
      - Add docstring tests
      - Update assets path

    - Fixed

      - Update assets path

- **isaacsim.test.collection**

    - Removed

      - Remove commented code

    - Changed

      - Updated deprecated imports to isaacsim.storage.native
      - Update deprecated python unittest methods
      - Make omni.isaac.ml_archive an explicit test dependency
      - Remove extra carb settings from tests

- **isaacsim.test.docstring**

    - Changed

      - Update description
      - Add API documentation
      - Add missing docstrings
      - Add more example usage to documentation

- **isaacsim.test.utils**

    - Added

      - Specify --/app/settings/fabricDefaultStageFrameHistoryCount=3 for startup test
      - Added `compare_images_in_directories()` function to compare images in two directories

    - Removed

      - Remove omni.replicator.core as an explicit test dependency

    - Changed

      - Update description
      - Add omni.replicator.core as an explicit dependency for image capture utils
      - Fix invalid escape sequence

- **isaacsim.ucx.core**

    - Added

      - Add UCXListenerRegistry::tryRemoveListener for reference-counted listener cleanup
      - Added `UCXListener::tagSendWithRequest` for better monitoring of send requests.
      - Added `UcxUtils.h`.
      - Added UCX Python dependencies.

    - Changed

      - Fix issues found by clang tidy
      - Regenerate pip prebundle
      - Refactored UCXListener's tag messaging functions.

- **isaacsim.util.camera_inspector**

    - Changed

      - Make omni.isaac.ml_archive an explicit test dependency

- **isaacsim.util.physics**

    - Changed

      - Update description
      - Add missing docstrings

- **omni.isaac.core_archive**

    - Changed

      - Update to kiwisolver-1.4.5
      - Removed numba and gunicorn from dependencies
      - Remove omni.pip.cloud from dependencies, users should explicitly enable if needed
      - Remove unused tornado and pint packages
      - Remove markupsafe from dependencies, its in omni.kit.pip_archive

- **omni.kit.loop-isaac**

    - Fixed

      - Issue where setting manual mode to false in the carb settings did not work if set before app startup completed

- **omni.pip.cloud**

    - Changed

      - Update to aioboto3==15.2.0
      - Update to aiobotocore==2.24.2
      - Update to boto3==1.40.18
      - Update to botocore==1.40.18
      - Update to msal==1.29.0

- **omni.pip.compute**

    - Changed

      - Update opencv-python-headless==4.12.0.88


.. toctree::
	:maxdepth: 2

	./known_issues



