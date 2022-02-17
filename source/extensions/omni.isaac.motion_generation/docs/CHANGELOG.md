**********
CHANGELOG
**********

[0.2.1] - 2022-02-15
========================

- Updated internal RMPflow implementation to allow for visualizing Lula collision spheres as prims on the stage

[0.2.0] - 2022-02-10
========================

Changed
-------

- Updated MotionGeneration to use Core API to query prim position and control the robot

[0.1.5] - 2022-02-10
========================

Fixed
-------

- Undefined joint in dofbot USD referenced by RMPflow config 

[0.1.4] - 2022-01-20
========================

Added
-------

- moved kinematics.py from omni.isaac.core.utils to this extension

[0.1.3] - 2021-12-13
========================

Changed
-------

- Removed deprecated fields from the Lula robot description files and RMPflow
  configuration files for the DOFBOT and Franka robots.  This also corrects
  an oversight in the Franka robot description file that had resulted in a
  lack of collision spheres (and thus obstacle avoidance) for panda_link6.

[0.1.2] - 2021-12-02
========================

Changed
-------

- event_velocities to events_dt in PickPlaceController
- Added new phase of wait in PickPlaceController

[0.1.1] - 2021-08-04
========================

Added
-------

- Added a simple wheel base pose controller.

[0.1.0] - 2021-08-04
========================

Added
-------

- Initial version of Isaac Sim Motion Generation Extension
