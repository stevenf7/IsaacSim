# Changelog

## [0.1.13] - 2022-08-31

### Changed
- Update paths to 2022.2

## [0.1.12] - 2022-08-03

### Fixed
- Switch to new gripper API
- Bugfix: behavior modules don't load if the file doesn't exist on startup.

## [0.1.11] - 2022-06-01

### Fixed

- prevent cortex launch from ROS-sourced env (inc. removing spamming prints from cortex_sim when launched into belief-only mode with ROS enabled)

## [0.1.10] - 2022-05-27

### Changed
- update the readme files
- remove <close_gripper> printout
- ensure obstacles enabled when building block stacking behavior

## [0.1.9] - 2022-05-26

### Changed
- Example behaviors now set their control mode (position-only or full pose commands) on construction. Prevents user error.
- Bugfix: go_home was passing in full c-space config for posture config preventing other scripts from passing only active joints. Expose active joints through motion commander and correct error.
- Add franka/nullspace.py demo of nullspace behavior using the `posture_config` motion command parameter.

## [0.1.8] - 2022-05-26

### Changed

- Cleanup tests to make them presentable. Keeps only `test_motion_commander.py` and `test_df.py`
- Switch `cortex_main.py` to have `--usd_env` be relative and add `--assets_root` flag which will default to using the built in tool to find the standard assets path.
- Add some standalone examples referenced by the tutorials. Some "simple examples" showing basic concepts, and some small but more complete demos showing programming paradigms.
- Some utilities used by examples: make_rotation_matrix(), tick_action()
- Automatically add monitors from context object (prevent users from forgetting; makes examples more concise); backward compatible.
- bugfix: motion commander wasn't handling position-only targets correctly.
- bugfix: cortex_ros was suppressing gripper pubs

## [0.1.7] - 2022-05-23

### Changed

- Bugfix [OM-51613] Cortex script help issues
- Bugfix [OM-51762] Fix transient error in cortex_ros when ROS messaging is still initializing
- Bugfix in SmoothedCommand: wasn't projecting onto a valid rotation after blending matrices.
- Include spliting out proj_R out from proj_T in math_util.py
- Remove unused alpha_diminish member from SmoothedCommand
- Comment code

## [0.1.6] - 2022-05-18

### Changed

- Switch from lula_ros to cortex_control (renamed internal library to match the ros_workspace deployment).

## [0.1.5] - 2022-05-17

### Changed

- Replaced find_nucleus_server() with get_assets_root_path()

## [0.1.4] - 2022-05-16

### Changed

- convert to default meters
- bugfixes around setting up world as singleton and accessing in extensions, including creating robot objects from extensions.
- includes a hack to handle world.reset bug where gains reset as well.
- add comments to tools.py and math.py
- updated READMEs to point to .../Isaac/Samples/Cortex/...
- fix ur10 default config setting
- generalize hiding of object property prims

## [0.1.3] - 2022-05-06

### Changed

- converted all imports to full paths `import omni.isaac.cortex.<component>`. 
    - works uniformly between extensions and python app (loop runner); no need to augment the python path
    - fixes a bug where the `df_behavior_module.py` change was noticed by `df_behavior_watcher.py`, but it couldn't be loaded.
- updates READMEs (proofread and added some description).

## [0.1.2] - 2022-05-04

### Changed

- Change USD path convention from `/cortex/world/...`  to `/cortex/belief/...` to match the cortex terminology.  Also, there are aspects of the core API that automatically add `/World` so that was overloaded.
- Move behaviors to `standalone_examples/cortex`
    - separate into robot independent and robot specific (franka) scripts
    - fix robot independent behaviors to actually be robot independent, including generalized go_home to work with multiple robots 
    - add script for launching cortex, activating behaviors, and clearing the current behavior
    - Update readmes

## [0.1.1] - 2022-05-02

### Changed

- Add a --test flag to cortex_main.py to run a short bringup test. (Bringup, wait 2 secs, shutdown.)
- cortex_main.py loads without ROS now by default. Use --enable_ros to bring up cortex_{ros,sim}.
- Add support for UR10. Includes making USD path convensions generic, adding cortex:robot_type attribute to robot USD, and updating the loading tools and motion policy configs.
- Fix ctrl-c issue: ros was preventing ctrl-c out of cortex_main.py.

## [0.1.0] - 2022-04-27

### Added

- Initial version of Isaac Cortex
