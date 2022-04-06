**********
CHANGELOG
**********

[1.0.2] - 2022-04-01
========================

Changed
--------

- modified default RmpFlow configs have fewer updates per frame (10 was unnecessary) and to not ignore robot state updates by default
- updated golden values in tests as a direct result of config change

[1.0.1] - 2022-04-01
========================

Added
------

- test case for motion_generation extension: test for proper behavior when add/enable/disable/remove objects to RmpFlow

Fixed
------

- ground plane handling: enable/disable/remove ground_plane didn't work
- static obstacle handling: dictionary key error when enable/disable/remove static obstacles

[1.0.0] - 2022-03-25
========================

Changed
-------

- Restructured MotionGeneration extension to place emphasis on MotionPolicy over MotionGeneration.  The user is now expected to interact
  directly with a MotionPolicy for adding/editing obstacles, and setting targets.  MotionGeneration is a light utility class for interfacing the 
  simulated USD robot to the MotionPolicy (get USD robot state and appropriately map the joint indeces).  
- RmpFlowController -> MotionPolicyController: 
  The RmpFlowController wrapper that was used to interface Core examples with RmpFlow has been expanded to wrap any MotionPolicy
- omni.isaac.motion_generation/policy_configs -> omni.isaac.motion_generation/motion_policy_configs:
  changed folder containing config files for MotionPolicies to be named "motion_policy_configs" to leave room for future interfaces to have config directories
- Path to RmpFlow: omni.isaac.motion_generation.LulaMotionPolicies.RmpFlow -> omni.isaac.motion_generation.lula.motion_policies.RmpFlow

Added
-------

- interface_config_loader: a set of helper functions for checking what config files exist directly in the motion_generation extension and loading the configs
  as keyword arguments to the appropriate class e.g. RmpFlow(**loaded_config_dict)

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
