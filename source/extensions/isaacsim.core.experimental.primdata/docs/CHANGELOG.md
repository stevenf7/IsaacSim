# Changelog

## [0.2.0] - 2026-04-03
### Added
- Bulk PhysX tensor reading for world transforms of physics prims (rigid bodies and articulation links) when engine is PhysX, significantly improving performance over per-prim Fabric queries

### Changed
- Non-physics prims (xforms, cameras) continue to use Fabric/USDRT computeWorldXformNoCache as fallback

## [0.1.1] - 2026-03-24
### Changed
- Replaced Readme.md with Overview.md

## [0.1.0] - 2026-03-20
### Added
- Added the new `isaacsim.core.experimental.primdata` extension scaffold.
- Added a native plugin target for hosting `IPrimDataReader` provider implementations.
