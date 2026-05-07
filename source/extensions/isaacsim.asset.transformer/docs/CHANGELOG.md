# Changelog

## [1.2.1] - 2026-05-05
### Fixed
- `make_explicit_relative` now normalizes backslash separators to forward slashes so USD asset paths, sublayer identifiers, and references emitted by the asset transformer are portable across platforms (e.g. avoids `./payloads\base.usda` on Windows).
- `AssetTransformerManager.run` writes the flattened `payloads/<base>.usd` path with forward slashes so the layer identifier and any downstream relative-path computation are platform-independent.

## [1.2.0] - 2026-04-09
### Changed
- Remove direct Omni / carb dependencies

## [1.1.0] - 2026-04-08
### Changed
- Improve Python API documentation (`config/python_api.md` and/or module docstrings).

## [1.0.3] - 2026-03-10
### Fixed
- Canonicalize quaternion orientations (real >= 0) on the flattened base layer so double-transform produces identical output

## [1.0.2] - 2026-03-02
### Fixed
- Ensure collected asset paths use explicit `./` or `../` relative prefixes

## [1.0.1] - 2026-02-13
### Fixed
- Tests failing due to misconfiguration of tests

## [1.0.0] - 2026-02-12
### Added
- First version of Asset Transformer manager.
