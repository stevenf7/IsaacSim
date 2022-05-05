**********
CHANGELOG
**********

[0.1.5] - 2022-05-05
========================

Changed
-------
- Updated vec_env_mt to enable flatcache when self._world.get_physics_context()._use_flatcache is set to True
- Moved enable_flatcache call from vec_env_base to physics_context in omni.isaac.core

[0.1.4] - 2022-05-03
========================

Fixed
-------
- Fixed flag for world reset when simulation restarts.

[0.1.3] - 2022-05-02
========================

Fixed
-------
- Fixed RL restart in multi-threaded VecEnv when simulation is stopped from UI.

[0.1.2] - 2022-04-29
========================

Changed
-------
- Refactor base VecEnv class to support more general usage.

[0.1.1] - 2022-04-28
========================

Added
-----
- Enabled omni.physx.flatcache when running RL with GPU pipeline

Removed
-------
- Moved RL Base Task to examples repo

Fixed
-----
- Fixed variable naming in VecEnvMT


[0.1.0] - 2022-03-30
========================

Added
-------
- Added Initial Classes