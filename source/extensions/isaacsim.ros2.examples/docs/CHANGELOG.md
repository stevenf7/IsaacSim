# Changelog

## [1.2.0] - 2026-04-01
### Changed
- Removed deprecated `isaacsim.core.api` and `isaacsim.core.utils` dependencies
- Migrated to `isaacsim.core.experimental.utils`, `isaacsim.core.rendering_manager`, and `isaacsim.core.simulation_manager`
- Replaced `set_camera_view` with `ViewportManager.set_camera_view`
- Replaced `PhysicsContext` with `PhysicsScene` from `isaacsim.core.simulation_manager`

## [1.1.0] - 2026-03-17
### Changed
- Updated documentation with AI agent.

## [1.0.1] - 2026-01-30
### Changed
- Update waypoint follower action graph to use ReadPrimLocalTransform node

## [1.0.0] - 2025-10-29
### Added
- Initial release of `isaacsim.ros2.examples` extension
- Migrated ROS 2 sample code from `isaacsim.ros2.bridge` extension
