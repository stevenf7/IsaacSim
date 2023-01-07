# Changelog

## [1.2.2] - 2023-01-06
### Fixed
- onclick_fn warning when creating UI

## [1.2.1] - 2023-01-04
### Fixed
- clean-ups on on_shutdown

## [1.2.0] - 2022-12-09
### Fixed
- Empty strings are no loger saved to config files

### Added
- Refresh path strings to default


## [1.1.1] - 2022-12-06
### Fixed
- Menu toggle value when user closes the window

## [1.1.0] - 2022-11-30
### Added
- Support for loading custom writers

### Changed 
- renamed extension.py to synthetic_recorder_extension.py
- renamed extension class from Extension to SyntheticRecorderExtension

### Fixed
- Annotators blocking other annotators of writing data if their requirements are not met

## [1.0.0] - 2022-11-14
### Added
- version using Replicator OV API

## [0.1.2] - 2022-09-07
### Fixed
- Fixes for kit 103.5

## [0.1.1] - 2022-08-02

### Fixed

- Error message when there was no instance data to write

## [0.1.0] - 2021-08-11

### Added
- Initial version of Isaac Sim Synthetic Data Recorder Extension
- Records RGB, Depth, Semantic and Instance segmentation, 2D Tight and Loose bounding box
- Supports multi-viewport recording
