# Changelog
## [0.2.2] - 2026-04-03
### Fixed
- instance_segmentation tests correctly cross-check dictionary values without assuming fixed IDs for prims

## [0.2.1] - 2026-03-24
### Fixed
- Fix test crash (SIGSEGV) caused by getter/setter tests unnecessarily attaching annotators that corrupt native rendering pipeline state on failure
- Add try/finally to parametrize decorators to ensure cleanup runs after test assertion failures

## [0.2.0] - 2026-03-05
### Changed
- Added Overview.md, python_api.md and updated docstrings

## [0.1.1] - 2026-02-27
### Changed
- Fix test issues when coverage is enabled

## [0.1.0] - 2026-02-25
### Added
- Initial release
