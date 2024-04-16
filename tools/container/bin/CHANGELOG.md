# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.5.0] - 2023-07-21
### Changed
- Modified python version to match python in carb (3.10.11)

## [0.4.1] - 2023-02-24
### Changed
- Modified `cache-generation` to first check if an existing packman package exists before generating.

## [0.4.0] - 2023-02-10
Introduces breaking change, project scripts have been moved to `docker/`!
### Added
- Added `cache-generation` directory with additional pipeline requirements.
### Changed
- Moved docker scripts (`build.sh`, `common.sh`, `publish.sh`, `republish.sh`) into `docker/` directory.

## [0.3.0] - 2021-08-25
### Added
- Added `republish.sh` to wrap the republish.py script from toolchain.
### Changed
- Removed environment loading since it is not supported by the toolchain.

## [0.2.0] - 2021-03-16
Introduces breaking change to support child pipelines.
### Changed
- Build script no longer loops over all `image_configs`, instead builds the image corresponding to the environment variable: `$BUILD`.

## [0.1.0] - 2021-12-16
### Added
- Project setup:
  - Gitlab CI, Readme, Version
  - Documentation
  - Bin scripts
