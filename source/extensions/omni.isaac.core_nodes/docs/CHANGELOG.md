# Changelog

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
