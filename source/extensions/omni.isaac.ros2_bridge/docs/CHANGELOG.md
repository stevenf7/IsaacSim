# Changelog

## [1.4.1] - 2022-08-09

### Fixed
- Activating image publishers should not cause a crash anymore

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
