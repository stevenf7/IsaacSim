**********
CHANGELOG
**********

[0.1.12] - 2021-12-14
========================

Changed
------
- Added feature to detect and update downloaded Isaac Sim assets on Nucleus (OM-41819)


[0.1.11] - 2021-12-08
========================

Changed
------
- recompute_extents now takes an argument to include children in recomputation


[0.1.10] - 2021-12-01
========================

Added
------
- isaac.nucleus.default setting moved from omni.isaac.utils

Fixed
-----
- XformPrim now checks if orient is in single or double precision before setting

Changed
-----
- gf_quatf_to_np_array and gf_quatd_to_np_array to gf_quat_to_np_array
- control_index to time_step_index in pre_step in BaseTask

[0.1.9] - 2021-11-29
========================

Added
------
- get_memory_stats to return a dictionary with memory usage statistics

[0.1.8] - 2021-11-08
========================

Added
------
- Propagated scale and visible args to different objects inheriting from XFormPrim object.
- is_simulating to SimulationContext

Changed
-------
- Split add_ground_plane to add_default_ground_plane and add_ground_plane.
- Changed initialize_handles to initialize.

[0.1.7] - 2021-11-06
========================

Added
------
- Added seperate functions to set different physics scene settings.
- Added error handling in PhysicsContext.
- Added doc strings to PhysicsContext.
- create_bbox_cache, compute_aabb, compute_combined_aabb

Changed
-------
- moving offset logic to base task to move the task assets accordingly
- changed name of PhysicsScene to PhysicsContext
- renamed mesh.py to bounds.py

[0.1.6] - 2021-11-04
========================

Added
------
- OmniPBR visual material
- Added get_physics_scene in SimulationContext
- clear in world
- get_extension_path_from_name
- is_prim_no_delete

Changed
-------
- default visual materials and physics materials prim paths 
- prim_type is default to Xform for create_prim
- type changed to prim_type for add_reference_to_stage
- get_prim_at_descendent_path -> get_first_matching_child_prim
- get_prims_path_at_descendent_tree -> get_all_matching_child_prims
- check_ancestral -> is_prim_ancestral

Fixed
-----
- default pose was resetting using local pose
- local pose in Rigid Body was missing an argument
- clear in Scene

Removed
-------
- set_extension_enabled

[0.1.5] - 2021-11-01
========================

Added
------
- Renamed Cube objects to Cuboids
- Generalized Cubes to Cuboids instead
- Added support for OmniGlass get_applied_visual material
- Changed parent_prim_path to prim_path in OmniGlass
- Unit tests for time stepping
- Switched visual_material_path to visual_material when passed to the different objects

[0.1.4] - 2021-10-29
========================

Added
------
- FixedCuboid class
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