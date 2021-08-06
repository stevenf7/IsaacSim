**********
CHANGELOG
**********

[0.1.6] - 2021-08-04
========================

Changed
-------

- DriveMode is now either DRIVE_FORCE or DRIVE_ACCELERATION, default is acceleration
- Position/Velocity drive is not specified via DriveMode
- All API calls verify if simulating, return otherwise
- set_dof_properties will not enable or change drive limits
- set_dof_state takes StateFlags to apply specific states
- get_dof_state takes StateFlags to set which states to get

Added
-----

- State variables can be printed
- ArticulationProperties to control articulation settings
- RigidBodyProperties can control iteration counts and contact impulse settings
- get_articulation_properties
- set_articulation_properties
- get_articulation_dof_position_targets
- get_articulation_dof_velocity_targets
- get_articulation_dof_masses
- set_rigid_body_properties
- get_dof_properties
- unit tests for most articulation, rigid body, dof and joint apis
- utilities for common scene setup and testing

Removed
-------

- get_articulation_dof_state_derivatives
- DriveModes DRIVE_NONE, DRIVE_POS, DRIVE_VEL

Fixed
-----

- apply_body_force now applies a force at a point
- set_dof_properties does not break position/velocity drives
- dof efforts report correct forces/torques due to gravity
- when changing state of a dof or a root link, unrelated state values are not applied anymore
- set_dof_state applies efforts now
- get_dof_properties works correctly now

Known Issues
------------

- dof efforts do not contain forces from external interactions, this will be added in the future using articulation sensors

[0.1.5] - 2021-07-23
========================

Added
-------
- Split samples from extension

[0.1.4] - 2021-07-14
========================

Added
-------
- now works when running without editor/timeline and only physx events. 
- fixed crash with setting dof properties

[0.1.3] - 2021-05-24
========================

Added
-------
- force and torque sensors

[0.1.2] - 2021-02-17
========================

Added
-------
- update to python 3.7
- update to omni.kit.uiapp

[0.1.1] - 2020-12-11
========================

Added
-------
- Add unit tests to extension


[0.1.0] - 2020-12-03
========================

Added
-------
- Initial version of Isaac Sim Dynamic Control Extension
