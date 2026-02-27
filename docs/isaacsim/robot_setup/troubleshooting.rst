..
   Copyright (c) 2022-2026, NVIDIA CORPORATION. All rights reserved.
   NVIDIA CORPORATION and its licensors retain all intellectual property
   and proprietary rights in and to this software, related documentation
   and any modifications thereto. Any use, reproduction, disclosure or
   distribution of this software and related documentation without an express
   license agreement from NVIDIA CORPORATION is strictly prohibited.

.. _isaac_sim_robot_troubleshooting:


===========================
Robot Setup Troubleshooting
===========================

This page consolidates troubleshooting information for robot setup and simulation in Isaac Sim.

Reparenting Assets
==========================================

You can change how reparenting behaves under **Edit > Preferences**, and on the **Stage Panel**, scroll down to authoring. The checkbox **Keep Prim world Transform when reparenting**, lets you decide when reparenting if the objects remain in place or if they get moved to the parent's frame of reference. You can use this to your advantage to apply offsets or change the parent's origin without impacting the children elements.

Robot Rigging Issues
====================

If your robot "explodes" during simulation or after some movements, check if any of the collision meshes are colliding with each other. 

Common rigging issues and their solutions:

1. Colliding collision geometries - Ensure that collision geometries do not intersect or overlap, especially at joint pivot points
2. Joint limit violations - Verify that joint limits are set appropriately and not being exceeded during simulation
3. Incorrect joint ordering - Make sure that joint orderings in articulation chains are correct
4. Physics instabilities - Adjust physics timestep or solver iteration counts if experiencing vibrations or instabilities

Physics Inspector "failed to find internal joint" errors for robots with mimic joints does not affect the functionality of the mimic joints and can be ignored:

.. code-block:: bash

    [Error] [omni.physx.plugin] Usd Physics: failed to find internal joint object for PhysxMimicJointAPI at /Franka/panda_hand/panda_finger_joint2. Please ensure that the prim is a supported joint type and is part of an articulation.

Robot Controller Issues
=======================

1. Gains produced by the gain turner may not perfectly track the robot's commanded movements (for example, as seen in the Cobotta Pro robot). Manual tuning of gains may be necessary for optimal performance.

2. Some grippers with parallel mechanism (that is, Robotiq 2F-85 and 2F-C2) have links that do not move with rest of the gripper. This is a known issue and may require manual adjustment of the gripper joints.

3. When working with differential drive robots, make sure that wheel friction is appropriate. Too little friction can result in wheel slippage, while too much friction can cause erratic movement.

Robot Import Issues
===================

USD to URDF Exporter issues:

- The Collider meshes may be improperly included in the visuals. They can be manually removed from the URDF file.
- The Body and Joints are authored in the URDF file in alphabetical order. They can be manually reordered in the URDF file.
- Depending on the robot structure, some body names may be overridden due to the merging of different frames. Review the output and verify that it's accurate.
- The URDF exporter adds joint effort and velocity limits as `inf` when unbounded. This may make the URDF not import correctly if the URDF parser does not support `inf` values in Float.

When importing a URDF:

1. If more than one asset in URDF contains the same material name, only one material is created regardless if the parameters in the material are different. For example, if two meshes have materials with the name "material", one is blue and the other is red, both meshes will be either red or blue. This also applies for textured materials.

2. MJCF importer does not show the built-in bookmark in the file picker dialog. The bookmark is still available in the content pane and can be copy-pasted into the file picker dialog.

Closed Loop Structure Issues
============================

For robots with closed-loop kinematic chains:

1. Make sure that the constraints are properly defined and initialized
2. Check that all joints in the closed loop have appropriate drive settings
3. Consider simulating the closed loop as separate articulations with constraints rather than with a single complex closed-loop structure
4. Adjust solver settings for better convergence if experiencing stability issues 

Robot Importing tips
=======================

1. Sometimes the robot may have non-zero target positions. When the target position does not match the initial position, the robot will move to the target position on the first frame. To prevent this, either set the target position to zero or set the initial position to the target position.
2. Max forces may be high or low in the URDF, set them to a more reasonable value in the USD.
3. If the stiffness and damping values are too high, the robot may oscillate. If it's too low, the robot may not move to the desired position. Use the gain tuner to test the stiffness and damping.
4. If the robot have overlapping collision meshes, use a filtered pair to ignore collisions between specific meshes.

Common Issues
===============

.. list-table::
    :widths: 30 70
    :header-rows: 1

    * - Observation
      - Solution
    * - Robot meshes are penetrating each other after importing
      - Verify the source file (MJCF or URDF) have the correct transforms for the meshes. Adjust the transforms in the source file or in the USD after importing.
    * - Robot joints are not moving at all
      - Check the joint limits and ensure they are set correctly. Adjust the limits in the source file or in the USD after importing. Verify that the joint gains are non zero. If you have mimic joints, make sure the gear ratio and direction are set correctly. One suggestion is to disable all the joints first, and then add them back one by one to isolate the issue.
    * - Robot joints are moving in the wrong direction
      - Check the joint axis and ensure they are set correctly. Adjust the joint axis in the source file or in the USD after importing. For mimic joints, verify that the direction is set correctly.
    * - Robot shakes uncontrollably starting from the first frame
      - Usually, conflicting collisions can generate adnormal amount of force which cause the robot to behave incorrectly. Check for self overlapping collision geometries. Uncheck self collision enabled in Articulation Root if self collision is not needed. If self collision is required, apply contact filter to specific pairs of colliders that should not collide.
    * - Robot shakes uncontrollably after some movements
      - This usually happens when the robot gains are too high and generating adnormal amount of torque. Try increasing the physics substeps and solver iteration counts in the Physics Settings window. You can also try reducing the robot's maximum velocity and force limits to prevent extreme movements.
    * - Robot experiences physX transform errors
      - This usually happens when the robot is under extreme forces or torques similar to the previous scenario and it can be induced by conflicting joint transformations. First disable all the joints and see if the issue persists. If the issue is resolved, re-enable the joints one by one to isolate the problematic joints. Check for conflicting joint limits or positions.
    * - The robot is penetrating the ground or other objects on the first frame
      - Check the initial position of the robot and ensure it is above the ground plane and not intersecting with any meshes. Verify that the collision geometries are correctly defined and not intersecting with other objects at the start of the simulation.
    * - The robot is penetrating the ground or other objects during simulation
      - Adjust the physics timestep and solver iteration counts to improve stability, modify the contact offset of the colliders to ensure proper collision detection, and verify that the robot's mass and inertia properties are realistic.
    * - The simulation performacne is slow at run time
      - Reduce the number of collision meshes and simplify their geometry by using simliar colliders, and adjust the physics timestep and solver settings for better performance.
    * - The robot joints are not following the commanded positions accurately
      - Tune the joint gains using the :ref:`isaac_gain_tuner`, ensure that the maximum velocity and force limits are set appropriately, and verify that there are no conflicting forces acting on the robot. 