..
   Copyright (c) 2022-2026, NVIDIA CORPORATION. All rights reserved.
   NVIDIA CORPORATION and its licensors retain all intellectual property
   and proprietary rights in and to this software, related documentation
   and any modifications thereto. Any use, reproduction, disclosure or
   distribution of this software and related documentation without an express
   license agreement from NVIDIA CORPORATION is strictly prohibited.

.. _isaac_sim_sensors_force:

==========================
Articulation Joint Sensors
==========================

Articulation sensors allow reading the active and passive components of the joint forces using the
`Articulation <../py/source/extensions/isaacsim.core.experimental.prims/docs/index.html#isaacsim.core.experimental.prims.Articulation>`_ class
from the ``isaacsim.core.experimental.prims`` extension.
See :ref:`isaac_robot_simulation_how_to` for more details about the Articulation class. Specifically,

- ``get_link_incoming_joint_force()`` returns the 6D force and torque (shape ``(N, L, 3)`` each) for each link's incoming joint.
  This provides the total spatial force at each joint and can be used to mimic force-torque sensors by reading forces from a fixed joint.
- ``get_dof_projected_joint_forces()`` returns the active component of the joint forces projected onto the motion direction for each DOF.
  This is useful for reading the measured effort at each actuated joint.

.. note::
    In an articulation tree, each link can have a single parent link.
    The joint forces reported by ``get_link_incoming_joint_force`` and ``get_dof_projected_joint_forces`` correspond to the forces,
    torques, or efforts exerted by the joint connecting the child link to the parent link.
    In short, the forces reported by these APIs denote the link incoming joint forces.

GUI
===

Script Editor
^^^^^^^^^^^^^

This section describes how to read articulation joint forces through the Script Editor, opened from **Window > Script Editor**.

.. literalinclude:: ../snippets/sensors/isaacsim_sensors_physics_articulation_force/articulation_joint_forces.py
    :language: python


API Documentation
=================

See the `isaacsim.core.experimental.prims API Documentation <../py/source/extensions/isaacsim.core.experimental.prims/docs/index.html>`_ for the full ``Articulation`` class reference.
