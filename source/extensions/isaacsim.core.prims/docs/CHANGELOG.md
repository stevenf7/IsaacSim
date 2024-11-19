# Changelog

## [0.3.2] - 2024-11-19
### Fixed
- XformPrim._set_xform_properties to take in consideration scale:unitsResolve attribute if authored.

## [0.3.1] - 2024-11-08
### Changed
- Changed Articulation.invalidate_physics_callback and RigidPrim.invalidate_physics_callback to weakref callbacks.

## [0.3.0] - 2024-11-05
### Added
- Added joint_names argument to all the joint related methods for ease of specifying which joints to manipulate/ query. 

## [0.2.0] - 2024-10-31
### Changed
- changed .initialize and .post_reset methods to be event triggered
- changed physX warmup and simulation context creation to be event trigerred

## [0.1.1] - 2024-10-24
### Changed
- Updated dependencies and imports after renaming


## [0.1.0] - 2024-10-18
### Added
- Initial release
