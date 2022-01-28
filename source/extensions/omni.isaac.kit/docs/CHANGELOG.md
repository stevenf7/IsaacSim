**********
CHANGELOG
**********


[0.1.4] - 2022-01-27
========================

Added
-----
- memory_report to launch config. The delta memory usage is printed when the app closes.
- automatically add allow-root if running as root user

[0.1.3] - 2021-12-21
========================

Changed
-------
- Simulation App starts in cm instead of m to be consistent with the rest of isaac sim. 

[0.1.2] - 2021-12-07
========================
Added
-----
- reset_render_settings API to reset render settings after loading a stage. 
- fix docstring for antialiasing

[0.1.1] - 2021-11-30
========================

Changed
-------
- Remove omni.isaac.core and omni.physx dependency
- Changed shutdown print statements to make them consistent with startup

[0.1.0] - 2021-11-30
========================

Changed
-------
- Tagged Initial version of SimulationApp