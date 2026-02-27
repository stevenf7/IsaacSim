
..
   Copyright (c) 2022-2026, NVIDIA CORPORATION. All rights reserved.
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

.. image:: /images/isim_6.0_full_ext-isaacsim.asset.importer.mjcf-3.0.0_user_interface.png
    :align: center
    :alt: User interface for MJCF Importer

.. _isaac_sim_mjcf_configuration_options:

Import Options
^^^^^^^^^^^^^^^^^^^^^^

**USD Output**: Specifies where the generated USD file will be saved. By default, this is set to "Same as Imported Model(Default)",
  which saves the USD file in the same directory as the source MJCF file. Users can click the folder icon to select a different
  output location.

**Colliders**:
    - **Collision From Visuals**: When enabled, collision geometry is generated from the visual meshes in the MJCF file. This is useful
      when the MJCF file doesn't have explicit collision geometry defined. When this option is checked, the Collision Type dropdown
      becomes visible.

    - **Collision Type**: Select between:
        - **Convex Hull**: Creates a convex hull around the visual mesh.
        - **Convex Decomposition**: Decomposes the visual mesh into multiple convex pieces for more accurate collision detection.
        - **Bounding Sphere**: Uses a simple bounding sphere approximation.
        - **Bounding Cube**: Uses a simple bounding box approximation.

**General Options**:
    - **Allow Self-Collision**: When enabled, allows the robot model to collide with itself. This can be useful for certain simulation
      scenarios but may cause instability if collision meshes between links are self-intersecting.

    - **Merge Mesh**: When enabled, merges meshes where possible to optimize the model. This can reduce the number of prims in the
      resulting USD file and improve performance.

    - **Debug Mode**: When enabled, activates debug mode to preserve the intemediate files and asset transformer reports


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

..  note::
    See the :ref:`isaac_gain_tuner` tutorial to tune the gains for your robot.

References
==========

Refer to the :ref:`isaac_sim_app_reference_asset_structure` for more information about the asset structure.


.. _isaac_sim_mjcf_tutorials:

Tutorial
======================================
Review :ref:`isaac_sim_app_tutorial_advanced_import_mjcf`.
