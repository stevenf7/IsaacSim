# Changelog

## [1.17.8] - 2026-04-29
### Fixed
- Fixed `OgnROS2PublishLaserScan` to call `generateBuffers` before `writeData` so output buffers are correctly sized before being populated
- Updated joint state subscriber tests to use `get_dof_positions`/`get_dof_velocities`; extended velocity convergence timeout and broadened multi-joint condition check
- Stabilized camera and camera info tests with fixed frame counts, proper `None` resets before timeline replay, and increased max frame limits
- Replaced manual `threading.Thread` spinning with `start_async_spinning` in waypoint follower tests
- Clean up subscriber queue tests

### Changed
- Added simulate until condition functions to tests to reduce test time
## [1.17.7] - 2026-04-30
### Changed
- Migrated `create_raycast_lidar_sensor` test helper and physics raycast tests to the new `isaacsim.sensors.experimental.physics` 3.0.0 API: call `Raycast.create(...)` (the authoring class) directly, return the authoring object's `paths[0]` instead of going through the runtime sensor, and use plural `translations=[[x, y, z]]` instead of singular `translation=Gf.Vec3d(...)`. The runtime sensor no longer forwards XformPrim attribute access or exposes a `create()` class method, so callers go through the typed authoring accessor.

## [1.17.6] - 2026-04-27
### Fixed
- Fix `OgnROS2CameraHelper` using `is None` instead of `.IsValid()` to check render product prim existence

## [1.17.6] - 2026-04-27
### Fixed
- Fixed flaky `test_*_subscriber_queue` tests on Windows by splitting each four-subscriber test into `_small` and `_large` variants. Removing the stop/play cycle inside a single test method avoids DDS discovery stale-match on re-play, which `wait_for_subscribers_on_topic` alone cannot work around.
- Fixed race at iteration 0 of `test_transform_tree_subscriber` and `test_transform_tree_subscriber_nova_carter` by waiting for DDS discovery after `timeline.play()` before publishing the first TF.
- Fixed `test_camera_info_sim_time` float-precision flake (`0.1 > 0.0999999996`) by replacing the 1.2x ratio tolerance with an absolute upper bound (≤ 1.0s) after stop/play reset, matching the intent of the assertion.

### Changed
- Refactored `test_subscribers.py` to share a single `_run_queue_test` helper across JointState, Clock, Twist, and AckermannDriveStamped queue tests; each test now does exactly one timeline cycle.

## [1.17.5] - 2026-04-27
### Changed
- Move deprecated extension dependencies to test dependencies
- Migrate test cases to core experimental API

## [1.17.4] - 2026-04-27
### Added
- Support configured SRTX sensor sets for `OgnROS2CameraHelper` and `OgnROS2RtxLidarHelper` by resolving per-render-product sensor-set maps from carb settings and declaring shared render-product path lists before registering local outputs.

## [1.17.3] - 2026-04-24
### Changed
- Query active physics engine at runtime via `omni::physics::IPhysics` and pass it to `createSimulationView` so ROS 2 tensor-backed nodes work with any registered engine
- Add Newton backend test configuration for joint state, pose tree, odometry, and differential base tests

## [1.17.2] - 2026-04-24
### Added
- SRTX-aware code path for publishing camera info topics.

## [1.17.1] - 2026-04-23
### Fixed
- Fixed test failures caused by slow DDS endpoint discovery. Added discovery waits after `timeline.play()` in `test_laser_scan.py`, `test_publisher.py`, `test_subscribers.py`, and `test_semantic_labels.py`.
- Fixed DDS message drops in subscriber queue tests by increasing publisher QoS depth from 1 to `MAX_COUNT` so the DDS writer can buffer all messages during burst publishing.

## [1.17.0] - 2026-04-23
### Added
- `OgnROS2RtxRadarHelper` node for publishing RTX Radar data as `PointCloud2` messages to ROS 2
- Camera and camera info tests (`test_camera.py`, `test_camera_info.py`) using `isaacsim.sensors.experimental.rtx`
- Multitick rendering test coverage for RTX sensor nodes

### Changed
- Updated extension dependency from `isaacsim.sensors.rtx` to `isaacsim.sensors.experimental.rtx`
## [1.16.3] - 2026-04-21
### Fixed
- Removed duplicate `destroy_publisher`/`destroy_node` calls in joint state subscriber test teardown

### Added
- `test_joint_state_subscriber_with_name_override`: verifies `JointNameResolver` correctly maps `isaac:nameOverride` joint names to prim names for articulation control

## [1.16.2] - 2026-04-22
### Fixed
- Make the SRTX sensor-set name used by `OgnROS2CameraHelper` and `OgnROS2RtxLidarHelper` overridable via the `/exts/omni.replicator.srtx/sensorSetName` carb setting. Previously both helpers hard-coded `"default-sensor-set"`, which caused every Isaac Sim bridge in a Mega simulation to register the same sensor-set ID against the shared SRTX runtime stage, clobbering each other and causing `triggerSensorSet ... not found` / `requestCaptureFrames: timed out waiting for previous capture` cascades. The helper `get_srtx_sensor_set_name()` reads the override and falls back to the previous default for standalone Isaac Sim use. The Mega Isaac Sim bridge publishes a per-bridge unique value derived from `<robotStackId>-<robotName>`.

## [1.16.1] - 2026-04-21
### Changed
- Replaced `omni.kit.commands` raycast sensor creation in test helpers with `RaycastSensor.create()` class method

## [1.16.0] - 2026-04-20
### Changed
- Replaced `isaacsim.sensors.physx` dependency with `isaacsim.sensors.experimental.physics` and `isaacsim.sensors.physics.nodes`
- Migrated point cloud and laser scan tests from PhysX lidar to physics raycast sensor (`IsaacReadRaycastSensor`)
- `OgnROS2PublishLaserScan` legacy array path now synthesizes binary hit/miss intensities when `intensitiesData` is unconnected

## [1.15.4] - 2026-04-20
### Fixed
- Fix `test_subscriber.py` and `test_publisher.py` issues where the subscriber and publisher were not properly handling the `vertex_indices` array when it was not set

## [1.15.3] - 2026-04-16
### Fixed
- Fix `OgnROS2PublishPointCloud` issue where the publisher was using its own uninitialized frame ID instead of `db.inputs.frameId()`

## [1.15.2] - 2026-04-15
### Changed
- Updated tests to check fixed sized array edge-cases for publisher and subscriber.

## [1.15.1] - 2026-04-08
- Added `test_bbox.py` with ROS 2 bounding box publisher tests. Includes tight vs loose (i.e., occlusions included vs excluded), and "golden" csv files with ground truth bbox.

### Changed
- Moved bounding-box tests out of `test_camera.py` into `test_bbox.py`

## [1.15.0] - 2026-04-07
### Added
- Add optional multitick support. When enabled, LaserScan and PointCloud2 messages built from GenericModelOutput annotator directly, and all sensor inputs (including RTX Lidar) are assumed to be full frames.

## [1.14.1] - 2026-04-03
### Changed
- Adapt camera test euler angles to new `[roll, pitch, yaw]` input convention
- Added camera TF test verifying 180-degree x-axis rotation is applied to UsdGeomCamera prims in the ComputeTransformTree -> PublishTransformTree pipeline

## [1.14.0] - 2026-04-01
### Changed
- Removed deprecated `isaacsim.core.api` and `isaacsim.core.utils` dependencies
- Migrated to `isaacsim.core.experimental.utils`, `isaacsim.core.experimental.objects`, `isaacsim.core.experimental.prims`, `isaacsim.core.rendering_manager`, and `isaacsim.core.simulation_manager`
- Consolidated `_simulate_async` into shared `common.py` test utility
- Replaced `_find_unique_string_name` with `stage_utils.generate_next_free_path`
- Migrated `OgnROS2RtxLidarHelper` to use `ViewportManager` from `isaacsim.core.rendering_manager`

## [1.13.1] - 2026-03-26
### Changed
- Update the test dependencies to use isaacsim.robot.wheeled_robots.nodes

## [1.13.0] - 2026-03-21
### Added
- SRTX publisher support for ROS 2 image, lidar point cloud, and laser scan topics
- New C++ SRTX publisher classes: ImagePublisher, PointCloudPublisher, and PublisherBase
- SrtxPublisherFactory for creating SRTX-based ROS 2 publishers
- SRTX support in ROS2CameraHelper, ROS2CameraInfoHelper, and ROS2RtxLidarHelper OmniGraph nodes

### Changed
- Refactored OgnROS2PublishPointCloud to use shared PublisherBase/PointCloudPublisher classes

## [1.12.2] - 2026-03-21
### Fixed
- Fix test publisher hang and reduce test time

## [1.12.1] - 2026-03-19
### Fixed
- Fix broken test and reduce test time

## [1.12.0] - 2026-03-17
### Changed
- Updated documentation with AI agent.

## [1.11.0] - 2026-03-10
### Changed
- ROS2PublishTransformTree accepts optional parentFrames, childFrames, translations, and orientations inputs to receive pre-computed transform data from IsaacComputeTransformTree, deprecating direct use of targetPrims

## [1.10.1] - 2026-03-10
### Changed
- Updated test_spinning_camera_golden_images unit test with new golden USD

## [1.10.0] - 2026-03-05
### Changed
- ROS2PublishJointState node now publishes from sensor inputs (e.g. IsaacReadJointState) for joint state data

## [1.9.0] - 2026-03-02
### Changed
- Shifted RTX sensor scan accumulation and post-processing back to host by default to reduce GPU resource contention and improve frametime & frametime consistency. Post-processing-on-device still available as option by setting app.sensors.nv.[modality].outputBufferOnGPU=true.

## [1.8.0] - 2026-02-27
### Changed
- Converted OgnROS2QoSProfile node from Python to C++ for improved performance and consistency with other C++ OG nodes

## [1.7.0] - 2026-02-26
### Added
- ROS 2 H.264 Compressed Image support with H.264 RGB unit tests
- omni.replicator.nv extension automatically enabled by omni.replicator.core and implictily used for HW H.264 encoding

## [1.6.2] - 2026-02-18
### Fixed
- Fix `eFloat` and `eUnknown` cases in `writeNodeAttributeFromMessage` incorrectly hardcoding `"outputs:"` prefix instead of using `inputOutput(isOutput)` and `prependStr`

### Changed
- Move some test assertions into node subscription callbacks

## [1.6.1] - 2026-02-16
### Changed
- Add missing dependency for isaacsim.sensors.physics.nodes

## [1.6.0] - 2026-02-05
### Changed
- Update isaacsim.sensors.physics dependency to isaacsim.sensors.experimental.physics

## [1.5.10] - 2026-02-05
### Removed
- Moved test_menu_graphs to isaacsim.ros2.ui
- Simplified test dependencies
- Replaced fields_to_dtype with sensors_msgs_py.point_cloud2.read_points where applicable
- Cleaned up setUp and tearDown methods in tests

## [1.5.9] - 2026-01-30
### Changed
- Update waypoint follower action graph to use ReadPrimLocalTransform node
- Fix quaternion normalization in ROS2 waypoint follower tests

## [1.5.8] - 2026-01-26
### Added
- Also run ros2 image buffer tests with async rendering handshake enabled

## [1.5.7] - 2026-01-24
### Changed
- Fix issues with menu click and context menu tests being flaky

## [1.5.6] - 2026-01-21
### Added
- Added ros2 image buffer util unit tests

## [1.5.5] - 2025-12-23
### Changed
- Update unit tests to reduce overall test time

## [1.5.4] - 2025-12-19
### Removed
- Remove rendering manager as a test dependency since the extension already depends on it indirectly

## [1.5.3] - 2025-12-11
### Changed
- Update ros2 test case to wait for viewport to be ready
- Increase wait time for test_camera_info.py to 1.25 seconds
- Set resetSimulationTimeOnStop to True for ROS2CameraHelper, ROS2CameraInfoHelper, ROS2RtxLidarHelper

## [1.5.2] - 2025-12-02
### Fixed
- ROS2PublishObjectIdMap correctly generates 128-bit unsigned integer strings from 4xuint32

## [1.5.1] - 2025-12-01
### Added
- ros2_common.build_rtx_sensor_pointcloud_writer to build Writer for ROS2 PointCloud2 for user-selected metadata

### Changed
- ROS2RtxLidarHelper uses ros2_common.build_rtx_sensor_pointcloud_writer

## [1.5.0] - 2025-11-26
### Added
- OgnROS2RtxLidarPointCloudConfig to simplify setting metadata to include in RTX Lidar PointCloud2

### Changed
- OgnROS2RtxLidarHelper now takes selectedMetadata input to specify which metadata to include in RTX Lidar PointCloud2
- OgnROS2PublishPointCloud updated with new CUDA kernel to add RTX Lidar and Radar metadata to PointCloud2 message when data is on device

## [1.4.0] - 2025-11-26
### Changed
- Optimized to use a single publish thread rather than tasks. Can be controlled with /exts/isaacsim.ros2.bridge/publish_with_queue_thread=true|false

## [1.3.0] - 2025-11-24
### Added
- Added support for pinned memory buffers to increase memcpy performance

## [1.2.0] - 2025-11-24
### Changed
- Update code to use new handle interface from isaacsim.ros2.core extension.

## [1.1.1] - 2025-11-20
### Changed
- Cleaned up test_camera_info.py: removed unused imports and centralized visualization flag

## [1.1.0] - 2025-11-10
### Changed
- Removed "viewport" input from ROS2 camera helper node

## [1.0.1] - 2025-11-07
### Changed
- Update to Kit 109 and Python 3.12

## [1.0.0] - 2025-11-02
### Added
- Initial release of `isaacsim.ros2.nodes` extension
- Moved ROS 2 OmniGraph nodes and components from isaacsim.ros2.bridge to this extension
