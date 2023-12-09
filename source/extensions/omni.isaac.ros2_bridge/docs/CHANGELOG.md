# Changelog

## [2.5.1] - 2023-12-08
### Fixed
- Removed conflicting TF Publishers from standalone ROS2 Moveit tutorial

## [2.5.0] - 2023-11-28
### Added
- ROS2 Ackermann Subscriber and Publisher nodes using non-default ROS2 AckermannDriveStamped message type.

## [2.4.0] - 2023-11-27
### Added
- Option to publish a full scan from RTX lidar
- APIs to dynamically load ROS2 libraries at runtime depending on what messages are being created. Will only be used for select non-default ROS 2 messages. 

## [2.3.10] - 2023-11-20
### Fixed
- Queue Size (QOS depth) settings now enforced when creating subscriber nodes.
- Added unit tests for variable queue sizes in subscribers

## [2.3.9] - 2023-10-17
### Fixed
- Added fix for foxy backend to match humble backend

## [2.3.8] - 2023-10-13
### Fixed
- CameraInfo publisher now includes identity Rectification matrix

## [2.3.7] - 2023-10-11
### Changed
- Disable extension if rclpy cannot load

## [2.3.6] - 2023-10-09
### Fixed
- Joint State Subscriber supports input state messages with only one mode of drive specified
- camera noise example errors

## [2.3.5] - 2023-10-09
### Fixed
- Moveit Tutorial had incorrect OG input name

## [2.3.4] - 2023-10-07
### Changed
- Set ROS2 Context node to read ROS_DOMAIN_ID from env vars by default

## [2.3.3] - 2023-10-05
### Fixed
- Bug with  ROS2 windows loading internal libs

## [2.3.2] - 2023-10-04
### Added
- Tests for JointState Publisher
### Fixed
- Carter 1 Unit tests
- JointState Publisher sign correction when a joint's parents are in reversed order 

## [2.3.1] - 2023-10-03
### Fixed
- Windows message for setting PATH
## [2.3.0] - 2023-09-26
### Added
- Added enable flag for the lidar and camera helper
- Improved description for the frame ID for the camera and lidar helper
- Add menu item for Isaac ROS VSLAM tutorial
## [2.2.3] - 2023-09-27

### Changed
- Made several warnings into print and log statements 

### Fixed
- rclpy not working in script editor

## [2.2.2] - 2023-09-25
### Fixed
- Transform tree node can accept multiple target prims as input

## [2.2.1] - 2023-09-22
### Fixed
- missing ros2 libs when running using internal libs
- windows startup issues
- rclpy not working on windows
- clock subscriber not properly getting time

## [2.2.0] - 2023-09-20
### Changed
- Load internal ROS2 libs when ROS2 is not sourced
- Print warning telling user how to source ROS2 to use internal libs with rclpy


## [2.1.0] - 2023-09-18
### Fixed
- error when shutting down extension
- properly handle case where ROS2 bridge carb plugin did not startup correctly

### Changed
- load system rclpy, fallback onto internal rclpy if its not found

## [2.0.0] - 2023-09-06
### Changed
- Re-written to use rclc APIs
- User must source their local ROS2 workspace in the terminal before starting isaac sim
- Foxy and humble are supported
- The ROS_DISTRO env variable is used to determine what ROS backend to use
- The separate Humble bridge extension has been removed

## [1.13.3] - 2023-08-25
### Changed
- added stdout fail pattern for the expected no prim found edge case for the ogn test
- Changed test_camera test to expect identical fx and fy as vertical aperture is computed from horizontal aperture. 

## [1.13.3] - 2023-08-25
### Fixed
- Add default values for World transform attributes when fetching fabric in computeWorldXformNoCache function used in processAllFrames
## [1.13.2] - 2023-08-18
### Fixed
- Pixel are square in 105.1 Vertical aperture is not used, and based off of horizontal

## [1.13.1] - 2023-08-10
### Changed
- Changed omnigraph targetPrim types from bundle to target
## [1.13.0] - 2023-08-03
### Changed
- Image and PCL publishers to use ptrs instead of arrays when possible to reduce memory copies

## [1.12.4] - 2023-07-05
### Fixed
- Joint efforts not being applied in joint state subscriber

## [1.12.3] - 2023-06-12
### Changed
- Update to kit 105.1
- rename synthetic data writer templates to match rendervar names

## [1.12.2] - 2023-03-13
### Fixed
- Incorrect 2D, 3D bbox data
- Bug with RTX Lidar not publishing flatscan correctly
- invalid json string if semantic message was empty


## [1.12.1] - 2023-03-09
### Changed
- Modified Omnigraph for Moveit example to match tutorials provided by Moveit2
### Fixed
- Negative bbox sizes

## [1.12.0] - 2023-02-28
### Fixed
- Issue where image based messages always used increasing simulation time
### Added
- resetSimulationTimeOnStop to Camera Helper node. 

## [1.11.2] - 2023-02-21
### Fixed
- Camera and RTX lidar helper settings are updated on stop/play

## [1.11.1] - 2023-02-01
### Fixed
- Changed semanticId in PublishBbox2d and 3d from int to string.

## [1.11.0] - 2023-01-31
### Added
- Fabric support

## [1.10.5] - 2023-01-25
### Fixed
- remove un-needed cpp ogn files from extension

## [1.10.5] - 2023-01-21
### Fixed
- TF_Tree fix when multiple objects shared the same prim name using the isaac:nameOverride attribute

## [1.10.4] - 2023-01-20
### Fixed
- Tests use a fixed QOS profile to improve determinism
## [1.10.3] - 2023-01-09
### Fixed
- Crash when using an old context handle

## [1.10.2] - 2023-01-06
### Fixed
- onclick_fn warning when creating UI

## [1.10.1] - 2022-12-12

### Fixed
- Errors when switching between ROS2 and ROS2 humble bridges

## [1.10.0] - 2022-12-10

### Changed
- Switch publishing nodes to use replicator writer backend
## [1.9.0] - 2022-11-21

### Added
- rtx_lidar_helper Node 

## [1.8.0] - 2022-11-17

### Added
- node template for rtx_radar

### Changed
- changed node template name for rtx_lidar

## [1.7.0] - 2022-11-14
### Changed
- Deprecated viewport input for camera helper
- Added renderProductPath input for camera helper

## [1.6.3] - 2022-10-25
### Fixed
- RTX Lidar Transform Tree Publisher

## [1.6.2] - 2022-09-13
### Fixed
- Test failures
- Warning when setting semantic class input

## [1.6.1] - 2022-09-07
### Fixed
- Fixes for kit 103.5

## [1.6.0] - 2022-08-30

### Changed
- Remove direct legacy viewport calls
## [1.5.0] - 2022-08-15

### Added
- ROS2Context node has a useDomainIDEnvVar flag that can be set to true so that the ROS_DOMAIN_ID variable is used

## [1.4.1] - 2022-08-09

### Removed
- Unused carb settings
### Fixed
- Activating image publishers should not cause a crash anymore
- File watcher patterns for extension

## [1.4.0] - 2022-07-22

### Added
- omni.syntheticdata template to publish RTX lidar point cloud

## [1.3.0] - 2022-07-21

### Changed
- Removed articulation control from OgnROS2SubscribeJointState
- Added JointState message outputs to OgnROS2SubscribeJointState allowing users to connect outputs to articulation controller core_node

## [1.2.3] - 2022-07-15

### Changed
- OgnROS2PublishSemanticLabels to accept string data type
- Timestamp data now appended to JSON msg output

## [1.2.2] - 2022-07-13

### Changed
- Improved image publisher perf

## [1.2.1] - 2022-07-06

### Fixed
- Quaternion input descriptions

## [1.2.0] - 2022-06-21

### Added
- ROS2 IMU publisher node

## [1.1.2] - 2022-05-31

### Fixed
- Removed Teleport sample from "Isaac Examples" Menu

## [1.1.1] - 2022-05-26

### Fixed
- Crash when switching extension on/off and simulating

## [1.1.0] - 2022-05-20

### Added
- ROS2 examples in "Isaac Examples" Menu

## [1.0.0] - 2022-05-18

### Changed
- Fully switched to OG ROS2 bridge nodes

## [0.8.3] - 2022-05-18

### Changed
- Added 32SC1 image type option to OgnROS2PublishImage

### Fixed
- Corrected stereoOffset input in OgnROS2CameraHelper

## [0.8.2] - 2022-05-03

### Changed
- Output data types to vectord and quatd in ROS2 Odometry, Raw TF publisher nodes and Twist subscriber node
- Added dropdown menu and validation for encoding input in ROS2 image publisher node

## [0.8.1] - 2022-05-02

### Changed
- Output data type from float to pointf in ROS2 point cloud publisher node

## [0.8.0] - 2022-04-29

### Added
- ROS2 Image publisher node

## [0.7.0] - 2022-04-28

### Added
- ROS2 Camera Info publisher node

## [0.6.1] - 2022-04-27

### Changed
- ROS2 point cloud publisher node to read generic point cloud buffer
- ROS2 laser scan publisher node to read generic lidar data buffers

## [0.6.0] - 2022-04-22

### Added
- OG ROS2 Odometry publisher node
- OG ROS2 Twist subscriber node
- OG ROS2 Transform Tree publisher node
- OG ROS2 Raw Transform Tree publisher node
- OG ROS2 Joint State Publisher node
- OG ROS2 Joint State Subscriber node

### Fixed
- OG ROS2 pub/sub clock nodes now able to namespace topic names

## [0.5.0] - 2022-04-20

### Added
- OG ROS2 LaserScan publisher node
- OG ROS2 PointCloud2 publisher node for lidar
- Utility method, addTopicPrefix for namespacing ROS2 topics

## [0.4.0] - 2022-04-13

### Added
- ROS2 Context
- ROS2 pub/sub clock

## [0.3.0] - 2022-03-18

### Added
- Added ROS2 topic name validation

## [0.2.7] - 2022-03-16

### Changed
- Replaced find_nucleus_server() with get_assets_root_path()

## [0.2.6] - 2022-03-11

### Changed
- Removed Cyclone DDS to allow defualt FastRTPS DDS to run instead

## [0.2.5] - 2022-03-11

### Fixed
- Issue with lidar init on first frame

## [0.2.4] - 2022-02-25

### Fixed
- Issue with camera init on first frame

### Changed
- ROS2 Bridge to initialize rclcpp in onResume and shutdown rclcpp in onStop

## [0.2.3] - 2022-02-17

### Fixed
- Crash when changing a camera parameter when stopped

### Changed
- Switch depth to new eDistanceToPlane sensor

## [0.2.2] - 2022-02-11

### Fixed
- laserScan publisher in RosLidar to be able to synchronize with Lidar sensor after any live user changes to USD properties
- pointCloud publisher using seperate caching variables from laserScan to prevent accidental overwriting

## [0.2.1] - 2022-02-08

### Fixed
- TF Tree publisher parent frame to include filter for articulation objects, separately from rigid body.

## [0.2.0] - 2022-02-07

### Added
- odometryEnabled setting to toggle both Odometry and TF publishers in differential base components

## [0.1.1] - 2021-12-08

### Fixed
- odometry frame matches robot's starting frame, not the world frame. 
- horizontal and vertical aperture use camera prim values instead of computing vertical aperture
- lidar components publish point cloud data as PCL2 messages instead of PCL
- lidar PCL2 messages only contain points that hit
- lidar publisher publishes a full scan for point cloud data

### Added
- usePhysicsStepSimTime setting and use_physics_step_sim_time to use physics step events to update simulation time

## [0.1.0] - 2021-04-23

### Added
- Initial version of ROS2 Bridge
