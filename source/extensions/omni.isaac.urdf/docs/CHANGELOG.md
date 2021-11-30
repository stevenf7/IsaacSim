**********
CHANGELOG
**********

[0.1.11] - 2021-11-29
========================

Changed
-------
- Use double precision for xform ops to match isaac sim defaults

[0.1.10] - 2021-11-04
========================

Changed
-----
- create physics scene is false for import config
- create physics scene will not create a scene if one exists
- set default prim is false for import config


[0.1.9] - 2021-10-25
========================

Added
-----
- Support to specify usd paths for urdf meshes. 

Changed
-----
- distance_scale sets the stage to the same units for consistency
- None drive mode still applies DriveAPI, but keeps the stiffness/damping at zero
- rootJoint prim is renamed to root_joint for consistency with other joint names. 

Fixed
-------
- warnings when setting attributes as double when they should have been float


[0.1.8] - 2021-10-18
========================

Added
-----
- Floating joints are ignored but place any child links at the correct location. 

Fixed
-------
- Crash when urdf contained a floating joint

[0.1.7] - 2021-09-23
========================

Added
-------
- Default position drive damping to UI

Fixed
-------
- Default config parameters are now respected

[0.1.6] - 2021-08-31
========================

Changed
-------
- Updated to New UI
- Spheres and Cubes are treated as shapes
- Cylinders are by default imported with custom geometry enabled
- Joint drives are default force instead of acceleration

Fixed
-------
- Meshes were not imported correctly, fixed subdivision scheme setting

Removed
--------
- Parsing URDF is not a separate step with its own UI


[0.1.5] - 2021-07-30
========================

Fixed
-------
- Zero joint velocity issue
- Artifact when dragging URDF file due to transform matrix


[0.1.4] - 2021-06-09
========================

Added
-------
- Fixed bugs with default density


[0.1.3] - 2021-05-26
========================

Added
-------
- Fixed bugs with import units
- Streamlined UI and fixed missing elements
- Fixed issues with creating new stage on import


[0.1.2] - 2020-12-11
========================

Added
-------
- Unit tests to extension
- Add test urdf files
- Fix unit issues with samples
- Fix unit conversion issue with import

[0.1.1] - 2020-12-03
========================

Added
-------
- Sample URDF files for carter, franka ur10 and kaya

[0.1.0] - 2020-12-03
========================

Added
-------
- Initial version of URDF importer extension
