**********
CHANGELOG
**********

[0.1.2] - 2021-10-20
========================

Added
-------
- Added articulation gripper class
- Deleted PD in the namings under articulation controller
- Added base tasks for stacking, pick_place and follow_target
- Added an IK solver under utils

Changed
-------
- The behavior of .play() method under SimulationContext to always do 1 step with rendering for dc to function properly.


[0.1.1] - 2021-10-18
========================

Added
-------
- Added *_callback_exists methods under SimulationContext
- Added object_exists method under Scene

Changed
-------
- The behavior of .play() method under SimulationContext to always do 1 step with rendering for dc to function properly.

[0.1.0] - 2021-10-15
========================

Added
-------
- Added first version of core.