**********
CHANGELOG
**********

[0.1.4] - 2021-10-29
========================

Added
------
- FixedCube class
- Calculate_metrics, is_done and async step functions to World
- More stepping examples to time_stepping.py
- Unit tests for time stepping

Changed
--------
- Made BaseTask methods non abstract
- Renamed set_physics_dt to set_simulation_dt for simulation context
- physics_dt and rendering_dt separated
- editor_callback change to render_callback
- Moved PhysicsScene to physics_scene.py

[0.1.3] - 2021-10-21
========================

Changed
--------
- Renamed view_ports.py to viewports.py
- renamed nucleus_utils.py to nucleus.py

Added
------
- disable_extension omni.isaac.core.utils.extensions
- lookat_to_quat to omni.isaac.core.utils.rotations
- get_intrinsics_matrix, backproject_depth, project_depth_to_worldspace to omni.isaac.core.utils.viewports
- set_up_z_axis to omni.isaac.core.utils.stage.set_stage_up_axis

[0.1.2] - 2021-10-20
========================

Added
-------
- Added articulation gripper class
- Deleted PD in the namings under articulation controller
- Added base tasks for stacking, pick_place and follow_target
- Added an IK solver under utils


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