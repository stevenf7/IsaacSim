# Changelog
## [0.3.3] - 2026-05-07
### Changed
- Gate USD `SELECTION_CHANGED` subscription and `ObjectsChanged` listener on effective visibility. Background tabs and hidden windows no longer pay per-click or per-stage-tick handler cost.
- Resolve the active robot via `usdrt.Usd.Stage.GetPrimsWithAppliedAPIName("IsaacRobotAPI")` against Fabric, replacing the per-selection USD `prim.HasAPI` ancestor walk.
- Scope hierarchy generation and change tracking to the selected robot.
- Pin the active robot scope across selection changes, eliminating the per-click flash.
- Selecting a child robot in nested-robot setups now shows only the child, matching the new "single active robot" policy.
- `SelectionWatch._on_selection_changed` early-returns when the resolved tree-view item set is unchanged.

### Fixed
- Inspector no longer crashes with `AttributeError: '_StageModel__usdrt_stage'` when filtering the tree after a view-mode switch.

## [0.3.2] - 2026-05-01
### Changed
- Robot Inspector UI tests now open the window through the menu and use shared menu UI retry helpers for more robust CI behavior.

## [0.3.1] - 2026-03-06
### Changed
- Robot Inspector performance and stability improvements.
- Schema UI tests: tearDown now waits for stage assets to finish loading before cleanup to reduce flakiness.

## [0.3.0] - 2026-03-04
### Changed
- Added Overview.md, python_api.md and updated docstrings

## [0.2.0] - 2026-02-23
### Added
- Robot masking: deactivate, bypass, and anchor controls for joints and links via stage columns
- Masking state management with session-scoped USD masking layer
- Robot Inspector window replacing Robot Hierarchy with component inspection and masking UI
- Change robot hierarchy based on different view modes (Flat, Tree, Mujoco-style)
- Custom stage column delegates for deactivate, bypass, and anchor toggles
- Automatic masking layer cleanup on stage open/close

### Changed
- Renamed "Robot Hierarchy" window to "Robot Inspector"

## [0.1.0] - 2026-02-12
### Added
- Initial version
