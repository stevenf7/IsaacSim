
..
   Copyright (c) 2022-2024, NVIDIA CORPORATION. All rights reserved.
   NVIDIA CORPORATION and its licensors retain all intellectual property
   and proprietary rights in and to this software, related documentation
   and any modifications thereto. Any use, reproduction, disclosure or
   distribution of this software and related documentation without an express
   license agreement from NVIDIA CORPORATION is strictly prohibited.






.. _Unified Robot Description Format (URDF): http://wiki.ros.org/urdf/XML/model
.. _MuJoCo Modeling XML File (MJCF): https://mujoco.readthedocs.io/en/latest/modeling.html

.. _isaac_sim_mjcf_importer:

===============================
MJCF Importer Extension
===============================

.. _isaac_sim_mjcf_importer_about:

.. note::
    Starting from the Isaac Sim 2023.1.0 release, the MJCF importer has been open-sourced.
    Source code and information for contributing can be found at `our Github repository <https://github.com/isaac-sim/IsaacSim/tree/main/source/extensions/isaacsim.asset.importer.mjcf>`_.
    As of Isaac sim 5.0, the former dedicated repository has been deprecated, and the code has been moved to the Isaac Sim repository.

The :ref:`isaac_sim_mjcf_importer` Extension is used to import MuJoCo representations of robots.
`MuJoCo Modeling XML File (MJCF)`_, is an XML format for representing a robot model in the MuJoCo simulator.

To access this extension, go to the top menu bar and click **File > Import**.

This extension is enabled by default. If it is ever disabled, it can be re-enabled from the :doc:`Extension Manager <extensions:ext_core/ext_extension-manager>`
by searching for ``isaacsim.asset.importer.mjcf``.

.. role:: bash(code)
   :language: bash
.. _isaac_sim_mjcf_conventions:


Conventions
^^^^^^^^^^^^^^^^^^^^^^


.. note:: Special characters in link or joint names are not supported and are replaced with an underscore. In the event that the name starts with an underscore due to the replacement, an `a` is pre-pended. It is recommended to make these name changes in the MJCF directly.

Refer to the :ref:`isaac_sim_conventions` documentation for a complete list of |isaac-sim| conventions.


.. _isaac_sim_mjcf_user_interface:

User Interface
=====================

.. image:: /images/isim_4.5_base_ext-isaacsim.asset.importer.mjcf-2.3.0_gui_0.png
    :align: center
    :alt: User interface for MJCF Importer

.. _isaac_sim_mjcf_configuration_options:

Import Options
^^^^^^^^^^^^^^^^^^^^^^

**Model**: Provides the Options to Import in Stage, or add as a referenced model. If Create in Stage is selected. Choose the options to Set as the default prim, and Clear Stage on Import. By default both are left unchecked.

**Links**: Choose: 

    * **Moveable base** (for example, a wheeled robot) the base link will be set to moveable.
    * **Static base** (for example, a 6DoF robotic arm) the base link will be fixed in place with a ``root_joint``.

The **Default Density** is used for links that do not have a mass specified in the URDF. If the density is set to ``0``, the physics engine will automatically compute the density with its default value.

**Colliders**:

    * **Visualize Collision Geometry**: When selected, the collision geometry will be visible in the viewport.
    * **Allow self-collision**: Enables self collision between adjacent links. It might cause instability if the collision meshes are intersecting at the joint.

    .. note:: 
        - It is recommended that you set Self Collision to false unless you are certain that links on the robot are not self colliding
        - You must have write access to the output directory used for import, it will default to the current open stage, change this as necessary.

.. _isaac_sim_mjcf_robot_properties:

Robot Properties
====================

There might be many properties you want to tune on your robot.
These properties can be spread across many different Schemas and APIs.

The general steps of getting and setting a parameter are:

1. Find which API the parameter is under. Most common ones can be found in the |pxr_usd_ext|.

2. Get the prim handle that the API is applied to. For example, Articulation and Drive APIs are applied to joints, and MassAPIs are applied to the rigid bodies.

3. Get the handle to the API. From there on, you can Get or Set the attributes associated with that API.

.. |pxr_usd_ext| raw:: html

    <a href="https://docs.omniverse.nvidia.com/kit/docs/kit-manual/104.0/api/pxr_index.html" target="_blank">Pixar USD API</a>

For example, if you want to set the wheel's drive velocity and the actuators' stiffness, you must find the DriveAPI:

.. literalinclude:: ../snippets/importer_exporter/ext_isaacsim_asset_importer_mjcf/robot_properties.py
    :language: python

Alternatively you can use the :ref:`isaac_sim_command_tool` to change a value in the UI and get the associated |omni| command that changes the property.


.. note::
    - The drive stiffness parameter should be set when using position control on a joint drive.
    - The drive damping parameter should be set when using velocity control on a joint drive.
    - A combination of setting stiffness and damping on a drive will result in both targets being applied, this can be useful in position control to reduce vibrations.


References
==========

Refer to the :ref:`isaac_sim_app_reference_asset_structure` for more information about the asset structure.


.. _isaac_sim_mjcf_tutorials:

Tutorial
======================================
Review :ref:`isaac_sim_app_tutorial_advanced_import_mjcf`.
