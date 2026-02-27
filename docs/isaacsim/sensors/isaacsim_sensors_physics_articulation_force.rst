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

Articulation sensors allow reading the active and passive components of the joint forces. To read articulation joint forces you can use `Articulation <../py/source/extensions/isaacsim.core.api/docs/index.html#isaacsim.core.prims.Articulation>`_ or `ArticulationView <../py/source/extensions/isaacsim.core.api/docs/index.html#isaacsim.core.prims.ArticulationView>`_ APIs.
See :ref:`isaac_robot_simulation_how_to` for more details about the Articulation and the ArticulationView classes. Specifically,

- `get_applied_joint_efforts <../py/source/extensions/isaacsim.core.api/docs/index.html#isaacsim.core.prims.ArticulationView.get_applied_joint_efforts>`_  API will return a tensor that specifies the efforts set by the user through the `set_joint_efforts <../py/source/extensions/isaacsim.core.api/docs/index.html#isaacsim.core.prims.ArticulationView.set_joint_efforts>`_.
- `get_measured_joint_forces <../py/source/extensions/isaacsim.core.api/docs/index.html#isaacsim.core.prims.ArticulationView.get_measured_joint_forces>`_  API will return a tensor that specifies 6-dimensional spatial forces per joints for all articulations (total overall joint forces). To mimic force-torque sensors, this API can be used to retrieve forces from a fixed joint.
- `get_measured_joint_efforts <../py/source/extensions/isaacsim.core.api/docs/index.html#isaacsim.core.prims.ArticulationView.get_measured_joint_efforts>`_  API will return a tensor which specifies the active components (the projection of the joint forces on the motion direction) of the joint forces for all the joints and articulations.

.. note::
    In an articulation tree, each link can have a single parent link.
    The joint forces reported by ``get_measured_joint_forces`` and ``get_measured_joint_efforts`` APIs correspond to the forces,
    torques, or efforts exerted by the joint connecting the child link to the parent link.
    In short, the forces reported by these API denote the link incoming joints forces.

GUI
===

Script Editor
^^^^^^^^^^^^^

This section describes how to add and customize the articulation sensor through the Script Editor, opened from **Window > Script Editor**.

.. literalinclude:: ../snippets/sensors/isaacsim_sensors_physics_articulation_force/script_editor.py
    :language: python