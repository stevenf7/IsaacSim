..
   Copyright (c) 2022-2026, NVIDIA CORPORATION. All rights reserved.
   NVIDIA CORPORATION and its licensors retain all intellectual property
   and proprietary rights in and to this software, related documentation
   and any modifications thereto. Any use, reproduction, disclosure or
   distribution of this software and related documentation without an express
   license agreement from NVIDIA CORPORATION is strictly prohibited.





.. _isaac_sim_robot_simulation_tips:

=============================
Robot Simulation Tips
=============================


Improve Simulation Performance
==================================
 
- You can speed up the simulation by reducing the number of objects in the scene, reducing the complexity of the objects in the scene, or reducing the number of simulation steps. For more information, see :ref:`isaac_sim_performance_optimization_handbook` for more details.

- Alternatively, you can reduce the number of sensors, or reduce the resolution of sensors in the scene. See :ref:`isaac_sim_benchmarks` for more performance benchmarks.

Simulation Time Stepping and Rendering Rate
============================================

- Adjust the physics step rate and the application's loop / timeline rate. The physics step rate is set independently on the Physics Scene (or via :py:meth:`isaacsim.core.simulation_manager.SimulationManager.setup_simulation`); lowering the application's render rate via :py:meth:`isaacsim.core.rendering_manager.RenderingManager.set_dt` does **not** automatically increase the number of physics substeps per frame. If you want more physics resolution, raise the Physics Scene's ``timeStepsPerSecond`` (equivalently ``SimulationManager.setup_simulation(dt=...)``); if you want fewer, lower it.

- For an end-to-end coherent rate change, call ``SimulationManager.setup_simulation(dt=...)`` and ``RenderingManager.set_dt(...)`` with the same ``dt`` so the three rate clocks stay aligned. See :ref:`isaac_sim_sensors_multitick_clock_relationships` for the relationship between the clocks.

 
Adjusting friction for wheeled robots 
========================================

- add and adjust friction parameters to both the wheels and the ground. See :ref:`isaacsim_gui_add_physics_material` for instructions.

- Coefficient of friction is the ratio between between the normal force and the friction force. Increasing the Coefficient of static or dynamic friciton to a higher value will increase the friction force for the same normal force. Coefficient of friction should not exceed 1.0 in most cases.

- modify the frictiion combine mode to adjust how friction is computed between two objects.


Gripper not picking up objects
=================================

- You can increase the friction parameters on both the fingers and object. See :ref:`isaacsim_gui_add_physics_material` for instructions.

- Use the Physics Authoring Toolbar (Tools > Physics Toolbar), especially the `Mass Distribution Tool <https://docs.omniverse.nvidia.com/kit/docs/omni_physics/latest/extensions/ux/source/omni.physx.supportui/docs/dev_guide/authoring_tools.html#mass-distribution-manipulator>`_ to make sure the weight of the object and weight of the arms are reasonable.

- The gripper is not following your commands accurately, consider increase the stiffness and damping gains in the controller.

Colliders
==========

- Colliders should only be applied to the parts of the robot that need to interact with the environment.

- Use simple shape colliders (box, sphere, capsule, convex hull) or convex hull whenever possible for better performance.

- Only use convex decomposition colliders when necessary, such as tips of end effectors, as they are more computationally expensive. Adjust the Error Percentage, Shrink Wrap, and ofset parameters in the advanced tab for better accuracy.

- Apply collision filters to avoid unnecessary collision checks between parts of the robot that should not collide with each other, such as the rubber pads on the finger and the finger itself. Overlapping colliders can cause instability in the simulation and cause the robot to "explode". Collision filters can be set via *Physics Collision Group*

- For dynamic collisions, use convex hull, convex decomposition, box, sphere, or SDF approximations only. Triangle mesh, and Mesh simplification only works for static objects.

Masses
========

- For accurate simulation, the mass, center of mass, diagonal inertia, principal axes of the rigid body should be set using the MassAPI, and match the real world masses as closely as possible.

- If it's not specified, the mass will be estimated based on the volume of the mesh, with dentisty set to 1000 kg/m^3 by default.
