**********
CHANGELOG
**********

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
