# Changelog

## [1.0.5] - 2026-03-21
### Fixed
- Fixed test setUp to call `super().setUp()`, ensuring menus are rebuilt before UI tests run so `File/Import` navigation succeeds on first test invocation

## [1.0.4] - 2026-03-09
### Fixed
- Hardened subprocess calls to avoid shell=True with string concatenation

## [1.0.3] - 2026-03-05
### Changed
- Linting

## [1.0.2] - 2026-03-05
### Fixed
- Fixed incorrect type annotation for SearchWidget

## [1.0.1] - 2026-02-26
### Changed
- Remove extension api doc

## [1.0.0] - 2026-02-01
### Changed
- URDF importer 3.x user interface

## [0.1.0] - 2026-01-10
### Added
- Initial release of the URDF Importer UI extension
- Decoupled UI components from the core URDF importer extension
- URDF Importer window with file picker and configuration options
- Asset Importer delegate for URDF files
- Joint configuration widgets (stiffness, natural frequency modes)
- Collider and link configuration options
