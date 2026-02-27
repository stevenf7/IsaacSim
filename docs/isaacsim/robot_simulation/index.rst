..
   Copyright (c) 2022-2026, NVIDIA CORPORATION. All rights reserved.
   NVIDIA CORPORATION and its licensors retain all intellectual property
   and proprietary rights in and to this software, related documentation
   and any modifications thereto. Any use, reproduction, disclosure or
   distribution of this software and related documentation without an express
   license agreement from NVIDIA CORPORATION is strictly prohibited.




.. _isaac_sim_robot_simulation:

============================
Robot Simulation 
============================

The `Robot Simulation` section provides information on tools that you will need to move a robot. The lowest level of control is joint control. For the next level up, we separated the controllers by the robot types, for they represent the three types of controllers we provide in |isaac-sim_short|:

- **Wheeled Robots**: use controllers that are based on universal formulas and require very few robot-specific parameters as inputs. 
- **Manipulators**: use controllers that are based on complex optimization, therefore the same robot performing the same task could use many variety of controllers, each with a different optimization method. They often require the robot models in the optimization process. 
- **Policy Controlled Robots**: uses controllers that are trained using reinforcement learning. They also has a much looser definition "controllers", for they can have task and path planners embedded as well.

Joint Level Control
---------------------------

.. toctree::
   :maxdepth: 1

   ./articulation_controller


Wheeled Robots
---------------------------

.. toctree::
   :maxdepth: 1

   ./mobile_robot_controllers


Manipulators
---------------------------


.. toctree::
   :maxdepth: 1

   ../manipulators/motion_generation_overview
   ./ext_isaacsim_robot_surface_gripper
   ./grasp_editor


Policy Controlled Robots
---------------------------
.. toctree::
   :maxdepth: 1

   ./ext_isaacsim_robot_policy_example


Tips and Deep Dives
============================


.. toctree::
   :maxdepth: 1

   ./robot_simulation_tips
   ./robot_simulation_core_concepts

