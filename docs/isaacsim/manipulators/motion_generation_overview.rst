
.. _isaac_sim_advanced_tutorials_motion_generation:


=================
Motion Generation
=================

.. note::
   For new development, consider using the newer :doc:`cuMotion Integration <../cumotion/index>`, which is built on the new experimental motion generation API and provides improved interfaces and additional features.

.. _isaac_sim_motion_generation_tutorials:

Lula is a high-performance motion generation library for robotic manipulation. RMPflow provides
real-time, reactive local policies to guide a robot manipulator to a task space target while
avoiding dynamic obstacles. A suite of Rapidly-exploring Random Tree (RRT) algorithms,
including RRT-Connect and JT-RRT, deliver global planning solutions in static environments.
Additionally, the trajectory generation tools in Lula provide time-optimal trajectories for
paths described as a series of c-space and task-space moves. Finally, Lula provides interfaces
to the performant forward and inverse kinematic solvers underpinning the higher-level motion
generation tools.

|isaac-sim| also interfaces with `cuRobo <https://curobo.org>`_, a high-performance, GPU-accelerated robotics motion
generation library that adds additional features to |isaac-sim| such as batched collision-free inverse kinematics,
collision-free motion planning, and reactive control in the presence of obstacles represented as meshes or Nvblox maps.
For more information, see the :ref:`cuRobo tutorial <isaac_sim_app_tutorial_cuRobo>`.

.. toctree::
    :maxdepth: 1
   
    concepts/index
    ./manipulators_robot_description_editor
    ./manipulators_rmpflow
    ./manipulators_lula_rrt
    ./manipulators_lula_kinematics
    ./manipulators_lula_trajectory_generator
    ./manipulators_configure_rmpflow_denso
    ./manipulators_curobo


Examples
========    

**Interactive Examples**

To locate the interactive examples, go to **Windows** > **Examples** > **Robotics Examples** and open the **Robotics Examples** tab if it's not already. Select one of the following examples from the browser, read the **Information** tab on the right hand side of the browser window for instructions on how to run it.

- Follow Target Example: **Manipulation > Follow Target**
- RoboFactory Example: **Multi-Robot > RoboFactory**
- RoboParty Example: **Multi-Robot > RoboParty**

.. Note:: Pressing **STOP**, then **PLAY** in this workflow might not reset the world properly. Use
          the **RESET** button instead.

**Standalone Examples**

To run a standalone example, navigate to your ``<isaac_sim_root_dir>``, then use ``./python.sh`` for Linux or ``python.bat`` for Windows to run the example scripts listed here. 

- Follow Target with RMPflow: ``standalone_examples/api/isaacsim.robot.manipulators/franka/follow_target_with_rmpflow.py``
- Follow Target with IK: ``standalone_examples/api/isaacsim.robot.manipulators/franka/follow_target_with_ik.py``
