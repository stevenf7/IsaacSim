# Changelog

## [1.0.2] - 2024-11-06
### Fixed
- Fixed stacking bounding box drop area calculation for scaled assets
- Fixed get world rotation util function to use Gf.Transform to get the rotation in case of transforms with scale/shear
- Check for previous colliders/rigid bodies for assets before simulation

### Changed
- Set exposed variables default values

## [1.0.1] - 2024-10-31
### Fixed
- Fixed 'remove_empty_scopes' to check if the prim is valid before searching for Scope or GenericPrim types

## [1.0.0] - 2024-09-29
### Added
- Added initial behavior script based randomizers

