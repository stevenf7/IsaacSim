
..
   Copyright (c) 2022-2026, NVIDIA CORPORATION. All rights reserved.
   NVIDIA CORPORATION and its licensors retain all intellectual property
   and proprietary rights in and to this software, related documentation
   and any modifications thereto. Any use, reproduction, disclosure or
   distribution of this software and related documentation without an express
   license agreement from NVIDIA CORPORATION is strictly prohibited.


.. _isaac_sim_motion_generation:

============================================
Motion Generation 
============================================

.. note::
   For new development, consider using the newer experimental motion generation API in :doc:`Motion Generation (Experimental) <../../motion_generation/index>`, which provides improved interfaces and additional features.

.. _isaac_sim_motion_generation_about:


The :ref:`isaac_sim_motion_generation` provides an API that you can use to control objects within |isaac-sim_short|.
The API is made up of abstract interfaces for adding motion control algorithms to |isaac-sim_short|.
The interfaces in the :ref:`isaac_sim_motion_generation` provide two basic utilities:

   * Simplify the integration of new robotics algorithms into |isaac-sim|.
   * Provide a standard structure with which to compare similar robotics algorithms.

For example, if you have a robot that has not previously been described to |isaac-sim_short|, you can use these APIs to define that robot and how it moves.

   * Simplify the integration of new robotics algorithms into |isaac-sim|.
   * Provide a standard structure with which to compare similar robotics algorithms.

For example, if you have a robot that has not previously been described to |isaac-sim_short|, you can use these APIs to define that robot and how it moves.

Three interfaces are  provided in the Motion Generation Extension:

* :doc:`motion_policy`
* :ref:`isaac_sim_path_planner`
* :doc:`kinematics_solver`


In |isaac-sim_short|, the robot is specified using a USD file that gets added to the stage.  However, we expect that robotics algorithms will have their
own way of specifying the robot's kinematic structure and custom parameters.  To avoid interfering with any particular robot description format, the interfaces
in the Motion Generation Extension include functions that facilitate the translation between the USD robot and a specific algorithm.  Specifically,
an algorithm can specify which joints in the robot it cares about, and the order in which it expects those joints to be listed.  The helper classes provided in this extension,
:ref:`isaac_sim_articulation_motion_policy`, :ref:`isaac_sim_path_planner_visualizer`, and :ref:`isaac_sim_articulation_kinematics_solver`, use the interface
functions to appropriately map robot joint states between the USD robot articulation and an interface implementation.


In |isaac-sim_short|, we use the word :doc:`Articulation <kit-physics:dev_guide/rigid_bodies_articulations/articulations>` to refer to the simulated robot represented through USD.
The word "Articulation" is used as a prefix in the
Motion Generation Extension to indicate utility classes that handle interfacing an algorithm with the simulated robot.

In addition, the **Motion Generation extension** includes a handful of special-purpose
controllers that do not  leverage `MotionPolicy` or `PathPlanner`.


.. toctree::
   :maxdepth: 1

   motion_gen_api.rst
   kinematics_solver.rst
   trajectory_interface.rst
   path_planner.rst
   lula_rrt.rst
   motion_policy.rst
   rmpflow.rst
   rmpflow_tuning_guide.rst
   


References
=====================

.. _isaac_sim_motion_generation_references:

.. Cheng, C.A., Mukadam, M., Issac, J., Birchfield, S., Fox, D., Boots, B., Ratliff, N.,
   "RMPflow: A computational graph for automatic motion policy generation" (2018),
   https://arxiv.org/abs/1811.07049

