# Changelog

## [1.7.1] - 2023-12-01
### Fixed
- Annotator unit test due to replicator update

## [1.7.0] - 2023-11-08
### Added
- On Physics Step Node

## [1.6.1] - 2023-09-21
### Changed
- Read file node will return False if file path does not exist or is invalid

## [1.6.0] - 2023-09-19
### Changed
- Add enabled flag to create render product node

## [1.5.0] - 2023-08-31
### Changed
- Added a default noop node to SDG pipeline helper nodes so that the graph is not deleted on stop
### Fixed
- ReadTimes node not passing execution state properly

## [1.4.3] - 2023-08-25
### Changed
- added stdout fail pattern for the expected no prim found edge case for the ogn test

## [1.4.2] - 2023-08-24
### Fixed
- Fixed camera info is empty bug in test_camera

## [1.4.1] - 2023-08-15
### Changed
- Changed omnigraph prim from bundle to target for OgnIsaacComputeOdometry, OgnIsaacArticulationController, OgnIsaacCreateRenderProduct, OgnIsaacSetCameraOnRenderProduct

## [1.4.0] - 2023-08-15
### Changed
- Use Replicator Annotator class for nodes that can provide data
- Point Cloud node returns width and height of data

## [1.3.2] - 2023-08-11
### Fixed
- Import error in OgnIsaacGetViewportRenderProduct

## [1.3.1] - 2023-08-09
### Fixed
- Added time code settings for test_physics_num_steps

## [1.3.1] - 2023-08-09
### Fixed
- Vertical Aperture used from reading the horizonal aperture usd property and multiplying it by resolution ratio to conform to the square pixels asumption in place. (DepthToPointCloud and IsaacReadCameraInfo nodes)

## [1.3.0] - 2023-08-03
### Changed
- RGBA and Depth to PCL nodes use raw ptrs instead of arrays to improve perf

## [1.2.0] - 2023-07-31
### Added
- Added tracking for the number of physics step

## [1.1.0] - 2023-07-06

### Removed
- unused writer and node template attachment systems

## [1.0.0] - 2023-06-13

### Added
- IsaacReadTimes node
- get_sim_time_at_time
- get_sim_time_monotonic_at_time
- get_system_time_at_time
- IsaacReadTimesAOV node template
- IsaacReadTimes node template

### Changed
- Update to kit 105.1, build system update
- IsaacArticulationController targetPrim now optional
- getSimulationTimeAtSwhFrame now getSimulationTimeAtTime with rational time
- getSimulationTimeMonotonicAtSwhFrame now getSimulationTimeMonotonicAtTime with rational time
- getSystemTimeAtSwhFrame now getSystemTimeAtTime with rational time
- [SENSOR NAME]IsaacSimulationGate nodes to [RENDERVAR]IsaacSimulationGate to match synthetic data standard
- deprecated get_sim_time_at_swh_frame
- deprecated get_sim_time_monotonic_at_swh_frame
- deprecated get_system_time_at_swh_frame

### Removed
- IsaacReadSystemTime node
- swhFrameTime input/output from IsaacConvertRGBAToRGB node

## [0.24.0] - 2023-05-31

### Added
- Support for custom distortion type/values on a camera  to read camera info node

## [0.23.2] - 2023-03-12

### Fixed
- Pressing pause should not reset classes derrived from BaseResetNode

## [0.23.1] - 2023-02-21

### Fixed
- Missing fisheye parameters for read camera info

## [0.23.0] - 2023-02-21

### Added
- BaseWriterNode for nodes that have to attach and detach writers

### Fixed
- RGBAToRGB Node should pass buffer size and SWH frame number

## [0.22.2] - 2023-02-14
### Fixed
- Core nodes should only subscribe to the type of stage event it needs

## [0.22.1] - 2023-01-25
### Fixed
- remove un-needed cpp ogn files from extension

## [0.22.0] - 2023-01-09
### Added
- interface for caching and retreiving handles

## [0.21.0] - 2022-12-10
### Changed
- IsaacSimulationGate step value can now be set to zero to stop execution
### Added
- function to handle writer activation requests to avoid race conditions from camera helpers. 

## [0.20.0] - 2022-12-05
### Added
- IsaacSetCameraOnRenderProduct Node
- render product support for ReadCameraInfo
- fisheye parameter support for ReadCameraInfo
- utility function to cache writer attach calls until the next frame
- ogn tests for IsaacCreateRenderProduct, IsaacReadCameraInfo
### Changed
- Deprecate viewport support in ReadCameraInfo
### Fixed
- Errors with SDG template registration
- Errors in default ogn tests

## [0.19.1] - 2022-12-01
### Fixed
- Articulation Controller Node skipping single array inputs

## [0.19.0] - 2022-11-09
### Added
- IsaacCreateRenderProduct node

## [0.18.0] - 2022-11-09
### Added
- IsaacGetViewportRenderProduct node

## [0.17.0] - 2022-10-04
### Changed
- CreateViewport node only creates one viewport
- CreateViewport takes a name as input, falls back onto viewportId as the name if name is not set

## [0.16.1] - 2022-10-03
### Fixed
- Fixes for kit 104.0

## [0.16.0] - 2022-09-29
### Added
- linearAcceleration, angularAcceleration to IsaacComputeOdometry

## [0.15.0] - 2022-09-28
### Added
- python bindings and tests for timing related APIs

## [0.14.3] - 2022-09-12
### Added
- unit test for create viewport node

### Fixed
- CreateViewport node uses legacy viewport ID which used to be the viewport index, the index is now converted to ID

## [0.14.2] - 2022-09-07
### Fixed
- Fixes for kit 103.5

## [0.14.1] - 2022-09-02

### Fixed
- bug with hiding /Render prim when it didn't exist

## [0.14.0] - 2022-08-31

### Changed
- Use omni.kit.viewport.utility instead of legacy viewport APIs

## [0.13.0] - 2022-08-09

### Added
- utility function to cache node activations until the next frame. This solves an issue where activating node templates from other nodes would cause a race condition

### Fixed
- IsaacSetViewportResolution node forces window aperture to reset if the resolution is changed. 

## [0.12.2] - 2022-07-22

### Fixed
- In OgnIsaacArticulationController, added validity check for joint_indicies list to prevent unnecessary warning message

### Added
- Additional unit test for Articulation Controller node for cases where no joint names or indices were given

## [0.12.1] - 2022-07-21

### Fixed
- In OgnIsaacArticulationController, added validity check for joint_indicies list to prevent unnecessary warning message

## [0.12.0] - 2022-07-20

### Changed
- IsaacComputeOdometry takes either an articulation root or a valid rigid body prim for the chassisPrim input

## [0.11.4] - 2022-07-06

### Fixed
- Quaternion input descriptions

## [0.11.3] - 2022-07-05

### Fixed
- Kit 104 build error

## [0.11.2] - 2022-07-03

### Fixed
- Extension will still load if replicator templates fail to register. This prevents dependent extensions from also failing to load due to a replicator.core failure

## [0.11.1] - 2022-06-30

### Added
- Unit test for Articulation Controller node

## [0.11.0] - 2022-06-22

### Added
- Added node to read file contents from path

## [0.10.0] - 2022-06-08

### Added
- Added node to read OS environment variables

## [0.9.0] - 2022-05-31

### Changed
- Added node to set viewport resolution
- Articulation controller only initializes on start

## [0.8.2] - 2022-05-19

### Changed
- Added "step" input to OgnIsaacSimulationGate

## [0.8.1] - 2022-05-18

### Added
- Utility function to set target prims on OG nodes

## [0.8.0] - 2022-05-16

### Added
- Register nodes used in SDG pipeline

## [0.7.0] - 2022-05-14

### Added
- ReadSystemTime node
- SimulationGate node

## [0.6.3] - 2022-05-11

### Changed
- Articulation Handle is refreshed at every compute

## [0.6.2] - 2022-05-11

### Changed
- Joint indices now is part of ArticulationAction type in ArticulationControllerNode

## [0.6.1] - 2022-05-06

### Changed
- De-bundled ArticulationControllerNode

### Fixed
- Crash when stepping physics without playing timeline

## [0.6.0] - 2022-05-05

### Changed
- Moved ReadSImulationTime to core nodes category

### Added
- OgnIsaacScaleToFromStageUnit

### Fixed
- Node unit tests

## [0.5.2] - 2022-05-04

### Changed
- OgnIsaacGenerate32FC1 to cpp
- OgnIsaacGenerateRGBA and OgnIsaacConvertRGBAToRGB to use token type for encoding input/ouput
- Added execOut to OgnIsaacConvertRGBAToRGB

## [0.5.1] - 2022-05-03

### Changed
- Output data types to vectord and quatd in Isaac Compute Odometry node
- Articulation controller node takes bundles

## [0.5.0] - 2022-05-02

### Added
- OgnIsaacConvertDepthToPointCloud

## [0.4.1] - 2022-04-29

### Fixed
- Fixed bug with validating encoding input in OgnIsaacConvertRGBAToRGB

## [0.4.0] - 2022-04-26

### Added
- OgnIsaacGenerate32FC1
- OgnIsaacCreateViewport
- OgnIsaacReadCameraInfo
- OgnIsaacArticulationController

### Changed
- Cleanup UI node names

### Fixed
- fixed issue with swh frame not working when simulation was stopped.

## [0.3.0] - 2022-04-25

### Changed
- renamed OgnIsaacRGBAToRGB to OgnIsaacConvertRGBAToRGB
- renamed OgnIsaacTestGenerateRGBA to OgnIsaacGenerateRGBA
- using a global clock for simulation time
- added ability to get simulation time from swhFrameNumber

## [0.2.1] - 2022-04-22

### Changed
- Renamed odometry node to OgnIsaacComputeOdometry

## [0.2.0] - 2022-04-18

### Added
- RGBA to RGB and RGBA generator nodes

## [0.1.1] - 2022-04-01

### Fixed
- Added missing omni.graph dependency for tests

## [0.1.0] - 2022-03-28

### Added
- Added first version of core omnigraph nodes.
