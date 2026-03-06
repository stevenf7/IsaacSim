
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
    - **Import Scene**: When enabled, imports the MJCF simulation settings along with the model.
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

Multi-Physics Engine Support
============================
The MJCF importer supports the conversion of MJCF actuator/joint data to PhysX schemas for multi-physics engine support.
This allows you to use the same MJCF file with different physics engines.

The conversion is done automatically when the MJCF importer is used.
You can use the :ref:`isaac_gain_tuner` tutorial to tune the gains for your robot with the multi-physics engine.

.. list-table:: MJCF to PhysX attribute conversion
    :widths: 25 25 50
    :header-rows: 1
    :align: center

    * - MJCF Attribute
      - PhysX Attribute
      - Notes

    * - MJC Actuator: gainType (fixed)
      - UsdPhysics DriveAPI.gainType
      - If gainType is present and is "fixed", and bias type is "affine", the gainPrm array is used to set the stiffness and damping. Only "fixed" gain type is supported. See explanation in the warning below.

    * - MJC Actuator: biasType (affine)
      - UsdPhysics DriveAPI.biasType
      - If biasType is present and is "affine", and gain type is "fixed", the biasPrm array is used to set the damping. Only "affine" bias type is supported. See explanation in the warning below.

    * - MJC Actuator: gainprm ([kp, 0, 0, ...]) - position control
      - UsdPhysics DriveAPI.stiffness
      - if gainprm array is present and the first element is not 0, stiffness = gainprm[0]. Stiffness must be a positive value in USD Physics.

    * - MJC Actuator: gainprm ([kd, 0, 0, ...]) - velocity control
      - UsdPhysics DriveAPI.damping
      - if gainprm array is present and the first element is not 0, damping = gainprm[0]. Damping must be a positive value in USD Physics.

    * - MJC Actuator: biasprm ([0, -kp, -kd, ...]) - position control
      - UsdPhysics DriveAPI.damping, UsdPhysics DriveAPI.stiffness
      - if biasprm array is present and the second and third elements are not 0, damping = -biasprm[2], stiffness = -biasprm[1]. Stiffness and damping must be positive values in USD Physics.
    
    * - MJC Actuator: biasprm ([0, 0, -kd, ...]) - velocity control
      - UsdPhysics DriveAPI.damping
      - if biasprm array is present and the third element is not 0, damping = -biasprm[2], stiffness = 0. Damping must be a positive value in USD Physics.

    * - mjc:forceRange:max
      - UsdPhysics DriveAPI.maxForce
      - MJCF uses min/max while PhysX uses maxForce. PhysX does not support min force ranges, so converted behavior may differ if abs(min) != max.

    * - mjc:frictionloss
      - PhysxJointAPI.jointFriction
      - Applied to joint friction attribute

    * - mjc:armature
      - PhysxJointAPI.armature
      - Sets armature parameter

    * - mjc:ref
      - UsdPhysics DriveAPI.targetPosition
      - Initial joint target position

.. warning::

  USD Physics uses PD controller for position control and P controller for velocity control, which is different from MJCF's 
  general controller formulation F = gain * control + bias, so only fixed gain type and affine bias type are supported.
  If the gain type or bias type is not "fixed" or "affine", the physics drive stiffness and damping will not be created, 
  please check the MJCF actuator attributes and adjust the gain type and bias type accordingly.

.. note::

    **Mimic joints:**  
    The MJCF importer supports conversion of mimic (dependent) joints, allowing one joint's motion to follow another with scaling and offset. In MuJoCo/MJCF, mimic relationships use ``mimicJoint``, ``mimicCoef`` 
    to model a higher order relationship between teh follower and leader joint. In PhysX, this is limited to a first order relationship, where ``mimicCoef0`` is the offset and ``mimicCoef1`` is the scale.

    When importing, these are mapped to corresponding PhysX and Newton schemas:
    
    - The source joint will have a relationship targeting the mimic joint, with ``mimicCoef`` modelling the higher order relationship.
    - For PhysX, these values are applied via ``PhysxMimicJointAPI``, where the ``MimicJointRel`` points to the driven joint, and ``Gearing`` or ``Offset`` attributes are set.
    - For Newton, the mimic attributes are applied through the ``NewtonMimicAPI`` (via relationship and attributes).
    - Both schemas are applied automatically if mimic attributes are present.
    - Newton Mimic API is disabled in the PhysX layer, to avoid conflicts with the PhysX Mimic Joint API.

    See source code for precise logic and usage.

Articulation Root API
=====================
The MJCF importer will create ``UsdPhysics ArticulationRootAPI``, ``Newton ArticulationRootAPI`` and ``PhysxArticulationAPI`` on the root link of the MJCF file.
``Newton ArticulationRootAPI`` is disabled in the PhysX layer, to avoid conflicts with the ``PhysxArticulationRootAPI``.

References
==========

Refer to the :ref:`isaac_sim_app_reference_asset_structure` for more information about the asset structure.


.. _isaac_sim_mjcf_tutorials:

Tutorial
======================================
Review :ref:`isaac_sim_app_tutorial_advanced_import_mjcf`.
