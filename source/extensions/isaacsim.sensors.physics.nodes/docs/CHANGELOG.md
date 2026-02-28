# Changelog
## [1.1.0] - 2026-02-27
### Changed
- Migrate nodes to use C++ core experimental prims APIs

## [1.0.1] - 2026-02-10
### Changed
- IMU and Contact sensor creation commands renamed to include Experimental in their name to avoid name collision with deprecated sensor commands

## [1.0.0] - 2026-02-01
### Changed
- Moved nodes from isaacsim.sensors.physics extension to this extension
- Updated to use interfaces from isaacsim.sensors.experimental.physics extension
- Updated contact and IMU examples to use the new sensor command APIs and legacy Python interfaces
