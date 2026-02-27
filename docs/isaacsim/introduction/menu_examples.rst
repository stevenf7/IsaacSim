
..
   Copyright (c) 2022-2026, NVIDIA CORPORATION. All rights reserved.
   NVIDIA CORPORATION and its licensors retain all intellectual property
   and proprietary rights in and to this software, related documentation
   and any modifications thereto. Any use, reproduction, disclosure or
   distribution of this software and related documentation without an express
   license agreement from NVIDIA CORPORATION is strictly prohibited.


.. _isaac_sim_examples:

======================================
Interactive Examples Reference Table
======================================


============================== ========================================
Menu Items                     Action
============================== ========================================
Sensors                        | Examples showing different ways of sensing the environment.
- LIDAR                        | See :ref:`isaacsim_sensors_physx_lidar_example` docs for more details.
- Custom Pattern Range Sensor  | See :ref:`isaacsim_sensors_physx_generic_example` docs for more details.
- IMU                          | See :ref:`isaacsim_sensors_physics_imu` docs for more details.
- Contact                      | See :ref:`isaacsim_sensors_physics_contact` docs for more details.
Input Devices                  | Examples using different HIDs.
- Kaya Gamepad                 | Connect to Gamepad using OmniGraph to control a Kaya robot.
- Omnigraph Keyboard           | Connect to Keyboard using OmniGraph.
Manipulation                   | Examples showing different manipulation tools in Isaac Sim.
- Follow Target                | Example showing a FrankaPanda robot arm following a target and avoid obstacles using RMPFlow controllers.
- Path Planning                | An extension version of the standalone example in :ref:`isaac_sim_app_tutorial_motion_generation_rrt` utilizing a FrankaPanda arm.
- Bin Filling                  | Example showing UR10 filling bins using suction grippers.
- Replay Follow Target         | Example of saving and replaying joint trajectories using a FrankaPanda arm.
- Surface Gripper              | See the :ref:`isaac_surface_grippers` docs for more details.
- Pick and Place               | See the :ref:`isaac_franka_pick_place` docs for more details.
- UR10 Follow Target           | Example showing a UR10 robot arm following a target using damped least square, pseudoinverse, transpose, and single value decomposition (SVD) inverse kinematics solvers.
Multi-Robot                    | Examples showing heterogeneous robot scenes.
- Robo Party                   | A demonstration of running multiple different robots (Kaya, FrankaPanda, UR10, Jetbot) with the same controller.
- Robo Factory                 | A demonstration of running multiple FrankaPanda robots with different controllers.
General                        | Examples showing general use cases.
- Hello World                  | Base Sample that can be used as template extension.
Policy                         | Examples showing deploying learned policies on robots.
- Quadruped                    | See the :ref:`isaac_sim_policy_example` for more details. Uses the Bostondynamics Spot.
- Humanoid                     | See the :ref:`isaac_sim_policy_example` for more details. Uses the Unitree H1.
- Franka                       | See the :ref:`isaac_sim_policy_example` for more details. Uses the Franka Panda robot.
Cortex                         | Examples of Cortex
- UR10 Palletizing             | See the :ref:`isaac_sim_app_tutorial_replicator_ur10_palletizing` docs for more details.
- Franka Cortex Examples       | See the :ref:`isaac_sim_app_tutorial_cortex_4_Franka_block_stacking` docs for more details.
Import Robots                  | Examples showing different ways of importing robots and assemblies.
- Carter URDF                  | Example of Carter robot imported from URDF.
- Franka URDF                  | Example of FrankaPanda robot imported from URDF.
- Kaya URDF                    | Example of Kaya robot imported from URDF.
- UR10 URDF                    | Example of UR10 robot imported from URDF.
Tutorials                      | Examples following the Quickstart Series
- Part I: Basics               | Following the steps found in :ref:`isaac_sim_app_intro_quickstart`.
- Part II: Robot               | Following the steps found in :ref:`isaac_sim_app_intro_quickstart_robot`.
============================== ========================================

