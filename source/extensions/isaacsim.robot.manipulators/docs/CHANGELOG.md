# Changelog

## [3.0.4] - 2025-01-26
### Changed
- Update test settings

## [3.0.3] - 2025-01-21
### Changed
- Update extension description and add extension specific test settings

## [3.0.2] - 2024-10-28
### Changed
- Remove test imports from runtime

## [3.0.1] - 2024-10-24
### Changed
- Updated dependencies and imports after renaming

## [3.0.0] - 2024-09-30
### Changed
- extension renamed to isaacsim.robot.manipulators (from omni.isaac.manipulators)

## [2.1.0] - 2024-05-24
### Added
- end_effector_prim_path argument added to the SingleManipulator alongside the end_effector_prim_name

## [2.0.0] - 2024-03-26
### Changed
- Extension factored into multiple components.  See isaacsim.robot.manipulators.ui

## [1.3.1] - 2024-03-21
### Changed
- enabled "add to existing graph" for all the shortcuts

## [1.3.0] - 2024-03-15
### Changed
- moved all python code into a python folder. deleted omni/isaac/manipulators

### Added
- Gripper Controller Node
- automatically populated omnigraph for gripper controller
- pointer to open up the python script that generates the omnigraph for the menu shortcut graphs

## [1.2.0] - 2024-02-07
### Added
- a menu item for the extension to allow for populating common controller omnigraphs
- automatically populated omnigraph for position and velocity controller of any articulation object

## [1.1.0] - 2022-11-24

### Added
- Add functionality to run only first x phases of the pick and place controller (instead of full 10)
- Change parameter name in controller initialization
- Add documentation

## [1.0.2] - 2022-11-22

### Fixed
- Fix typo in `suction_gripper.py` warning message


## [1.0.1] - 2022-08-03

### Fixed
- Bugfix `parallel_gripper.py` `apply_action` internally calling wrong function.

## [1.0.0] - 2022-07-26

### Added
- Added Manipulator class
