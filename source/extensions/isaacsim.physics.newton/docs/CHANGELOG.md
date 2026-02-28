# Changelog

## [0.4.0] - 2026-02-27
### Changed
- Pinned mujoco-warp to 3.5.0.2 for compatibility with newton[sim] 1.0.0rc1

## [0.3.0] - 2026-02-27
### Removed
- Removed omni.warp extension dependency; only omni.warp.core is required

### Changed
- Upgraded Newton to 1.0.0rc1 with updated solver and USD schema handling

## [0.2.0] - 2026-02-24
### Changed
- Moved newton prebundle to isaacsim.pip.newton extension

## [0.1.2] - 2026-02-20
- Fixed broken newton usecases after upgrading the newton/mujoco packages

## [0.1.1] - 2026-02-06

### Added
- Capability check

### Removed
- Data handling from the physics umbrella

## [0.1.0] - 2025-12-23

### Added
- Initial release of isaacsim.physics.newton extension
- Integration with Newton physics engine
- Support for XPBD and MJC integrators
- Stage update node for physics simulation

