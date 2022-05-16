**********
CHANGELOG
**********


[0.1.4] - 2022-05-16
========================

Changed
-------

- convert to default meters
- bugfixes around setting up world as singleton and accessing in extensions, including creating
  robot objects from extensions.
- includes a hack to handle world.reset bug where gains reset as well.
- add comments to tools.py and math.py



[0.1.3] - 2022-05-06
========================

Changed
-------

- converted all imports to full paths `import omni.isaac.cortex.<component>`. 
    - works uniformly between extensions and python app (loop runner); no need to augment the python path
    - fixes a bug where the `df_behavior_module.py` change was noticed by `df_behavior_watcher.py`, but it couldn't be loaded.
- updates READMEs (proofread and added some description).

[0.1.2] - 2022-05-04
========================

Changed
-------

- Change USD path convention from `/cortex/world/...`  to `/cortex/belief/...` to match the cortex terminology.  Also, there are aspects of the core API that automatically add `/World` so that was overloaded.
- Move behaviors to `standalone_examples/cortex`
    - separate into robot independent and robot specific (franka) scripts
    - fix robot independent behaviors to actually be robot independent, including generalized go_home to work with multiple robots 
    - add script for launching cortex, activating behaviors, and clearing the current behavior
    - Update readmes

[0.1.1] - 2022-05-02
========================

Changed
-------

- Add a --test flag to cortex_main.py to run a short bringup test. (Bringup, wait 2 secs, shutdown.)
- cortex_main.py loads without ROS now by default. Use --enable_ros to bring up cortex_{ros,sim}.
- Add support for UR10. Includes making USD path convensions generic, adding cortex:robot_type
  attribute to robot USD, and updating the loading tools and motion policy configs.
- Fix ctrl-c issue: ros was preventing ctrl-c out of cortex_main.py.

[0.1.0] - 2022-04-27
========================

Added
-------

- Initial version of Isaac Cortex
