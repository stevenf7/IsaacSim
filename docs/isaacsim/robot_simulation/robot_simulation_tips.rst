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

- adjust the rendering and physics stepping in simulation. If your system is GPU limited, decrease the rending rate could allow more physics stepping to happen per frame, so although it may appear less smooth with a lower frame rate, the physics simulation may be more accurate and more simulation time would have elapsed per frame.

- These parameters can be set using the Simulation Manager and the Rendering Manager, assessbile via Python


.. _isaac_sim_animated_usd_fixed_step_alternatives:

Alternatives to Animated USD with a Fixed Manual Step Size
----------------------------------------------------------

The full Isaac Sim experience (``isaacsim.exp.full.kit``) enables Fixed Time Stepping by default so that ``SimulationApp`` and other scripted workflows step the timeline deterministically. Under Fixed Time Stepping, the timeline advances by a fixed ``dt`` per loop tick rather than by wall-clock time, so USD scenes that drive motion through time-sampled (``timeSample``) keyframes will appear to play back slower than real time whenever the renderer cannot sustain the target rate. The same content plays smoothly in USD Composer or in the Isaac Sim Base experience (``isaacsim.exp.base.kit``), both of which default to Variable stepping.

If you are authoring or simulating a scene where moving parts are driven by USD keyframes, prefer one of the following over leaving the content as an animated USD that relies on the default fixed manual step:

- **Drive the transforms procedurally each simulation tick.** Replace the time-sampled attributes on the moving prims with a per-step callback. The current API is ``SimulationManager.register_callback(fn, event=SimulationEvent.PHYSICS_POST_STEP)`` from ``isaacsim.core.simulation_manager`` (see :doc:`extensions:isaacsim_core_simulation_manager`); ``add_physics_callback`` on ``SimulationContext`` / ``World`` from the deprecated ``isaacsim.core.api`` namespace works equivalently for existing code. An OmniGraph triggered by the ``OnPhysicsStep`` node is the visual-scripting equivalent. Compute the pose from your own time variable — wall-clock ``dt`` for smooth GUI playback, simulation ``dt`` for determinism. This is the recommended pattern for scripted scenarios: it keeps determinism for ``SimulationApp`` and stays correct under any time-stepping mode.

- **Author the motion as articulated joints or rigid-body kinematics** rather than as keyframed transforms. Joint targets and kinematic bodies are advanced by the physics step, so the motion stays synchronized with simulation time regardless of render rate. This is also the right choice when other simulated objects need to interact with the moving parts.

- **Tune the loop rate to match the authored animation's sample rate.** If you must keep the content as a keyframed USD and you are running interactively, set the main loop rate so that one fixed ``dt`` corresponds to one keyframe interval (for example, ``--/app/runLoops/main/rateLimitFrequency=60`` for a 60 FPS authored animation), and reduce scene cost (LODs, lighting, viewport resolution) until the renderer can hit that rate. While the renderer falls behind, timeline time will continue to lag wall-clock.

- **Switch the GUI to Variable stepping for review and authoring.** For animation review or content-authoring sessions where determinism is not required, launch with the flags listed in :ref:`isaac_sim_troubleshooting_animation_playback_slow` to opt the experience into Variable stepping. Do not use these flags for ``SimulationApp`` jobs that depend on a fixed per-step ``dt``.

 
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
