# Changelog

## [0.2.2] - 2026-06-09
### Fixed
- Fix linter errors and missing or incomplete docstrings, and update `python_api.md`.

## [0.2.1] - 2026-04-08
### Fixed
- Fix mypy type errors: add type annotations, fix `_run()` returning truthy tuple instead of `False` on error, fix namedtuple name mismatch

## [0.2.0] - 2025-12-17
### Changed
- Migrate extension implementation to core experimental API

## [0.1.13] - 2025-12-04
### Fixed
- Remove break in Clash Detection pipeline loop so clashes are stored

## [0.1.12] - 2025-11-20
### Changed
- Update test arguments

## [0.1.11] - 2025-10-27
### Changed
- Make omni.isaac.ml_archive an explicit test dependency

## [0.1.10] - 2025-05-10
### Changed
- Enable FSD in test settings

## [0.1.9] - 2025-04-09
### Changed
- Update all test args to be consistent
- Update Isaac Sim NVIDIA robot asset path

## [0.1.8] - 2025-04-04
### Changed
- Version bump to fix extension publishing issues

## [0.1.7] - 2025-03-26
### Changed
- Cleanup and standardize extension.toml, update code formatting for all code

## [0.1.6] - 2025-03-26
### Fixed
- API change for clash detection api adding setting_depth_epsilon

## [0.1.5] - 2025-03-11
### Changed
- Switch asset root for tests to internal nucleus

## [0.1.4] - 2025-01-26
### Changed
- Update test settings

## [0.1.3] - 2025-01-21
### Changed
- Update extension description and add extension specific test settings

## [0.1.2] - 2024-12-03
### Changed
- Only depend on omni.physx.clashdetection.core

## [0.1.1] - 2024-11-08
### Fixed
- Extension imports and dependencies due to renaming

## [0.1.0] - 2024-09-03
### Added
- Initial version of Isaac Sim Clash Detection extension
