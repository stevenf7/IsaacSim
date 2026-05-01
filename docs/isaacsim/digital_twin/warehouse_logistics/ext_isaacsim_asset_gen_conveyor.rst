..
   Copyright (c) 2022-2026, NVIDIA CORPORATION. All rights reserved.
   NVIDIA CORPORATION and its licensors retain all intellectual property
   and proprietary rights in and to this software, related documentation
   and any modifications thereto. Any use, reproduction, disclosure or
   distribution of this software and related documentation without an express
   license agreement from NVIDIA CORPORATION is strictly prohibited.


.. _isaac_conveyor:

===============================
Conveyor Belt Utility
===============================

.. _isaac_conveyor_about:

About
=====

The Conveyor Belt Utility extension turns rigid bodies into conveyors in |isaac-sim|.

.. note::

    For a more customizable approach to conveyor belt simulation, see :ref:`isaac_conveyor_custom_sim`.

.. _isaac_conveyor_usage:

Usage
=====

To enable the extension:

1. Select **Window > Extensions**.
2. Search for ``conveyor``.
3. Select ``isaacsim.asset.gen.conveyor.ui`` and click **Enable**. This enables both the extension and its UI.

To load the extension automatically on startup, click **Autoload** near the top of the ``isaacsim.asset.gen.conveyor.ui`` information pane in the extension manager.

To create a conveyor:

1. Select a rigid body or a mesh in the stage.
2. Choose **Create > Isaac Sim > Warehouse Items > Conveyor** to create an |omnigraph| node that drives conveyor speed and animation. The node exposes the following properties:

   - **conveyorPrim**: The target prim that receives the conveyor velocity. If the prim is not a rigid body, it is configured as one automatically with default collision models. Only a single prim is allowed per ``ConveyorNode``.
   - **Animate Direction**: Texture animation direction in the UV map.
   - **Animate Scale**: Ratio between conveyor velocity and texture animation speed.
   - **Animate Texture**: Enables texture animation.
   - **Curved**: Marks the conveyor as curved. When set, the node applies angular velocity instead of linear velocity. The angular velocity is applied along the **Direction** vector, which acts as the rotation axis. Scaling the **Direction** vector adjusts the velocity: values greater than 1 increase the effective curvature radius and values less than 1 decrease it. For example, ``(0, 0, 1)`` rotates about the Z axis.
   - **Direction**: Conveyor velocity direction in local coordinates.
   - **Enabled**: Enables or disables the conveyor.
   - **Velocity**: Conveyor velocity.

The generated |omnigraph| is preconfigured with a velocity variable that you can edit by selecting the |omnigraph| prim. To synchronize multiple conveyors in a scene, point each conveyor's read-variable node (``read_speed``) at the same |omnigraph| variable.

To emulate belt motion visually, apply a tiled texture and set the **Animate** properties so the texture translates along the same direction as the conveyor and at a matching speed.

Alternatively, define your own |omnigraph| and add ``ConveyorNode`` instances to it. This lets you manage multiple conveyors from a single graph.

For convenience, the |isaac-sim_short| assets package includes prebuilt conveyor pieces at ``Isaac/Props/Conveyors``.

When authoring conveyor behavior for these assets, select the ``Belt`` or ``Rollers`` prim. Those prims contain the meshes that define the conveyor surface.


Digital twin library conveyor system generator
==============================================

To support digital twin authoring, a conveyor system generator is available at **Tools > Conveyor Track Builder**. The utility ships with the Digital Twin asset pack for conveyors, and it also accepts custom datasets by pointing the configuration file at a different asset folder.

When the current selection is a component from the conveyor dataset, the builder attempts to connect the new piece to one of the existing conveyor endpoints defined by the configuration. Otherwise, it parents the new piece under the current selection.

.. image:: /images/isim_4.5_base_tut_viewport_conveyor_track_builder.png
    :align: center


The builder integrates loosely with the assets to keep system creation flexible while applying a minimal rule set. As a tradeoff, completed systems may require small manual cleanup, but the loose coupling lets you fully customize each track after it has been placed.

User interface
--------------

.. image:: /images/isaac_conveyor_ui.png
    :width: 40%
    :align: center

========== ================================== ====================================================================
Ref #      Option                             Description
========== ================================== ====================================================================
1          Conveyor Style                     Available conveyor styles: Roller, Belt, or Dual.
2          Track Type                         Available track types: Start, straight, T-split, Y-split, or end.
3          Curvature                          Track curvature: None, Half (typically 90 degrees), or Full (typically 180 degrees), to the left or right.
4          Elevation                          Track elevation, measured in levels relative to the entry point, either up or down.
5          Selected Track                     Shows the currently selected track, its endpoints, and a Delete button that removes the track from the system.
6          New Track                          Shows the piece queued for insertion. Lets you choose the input endpoint and the track variant, and, when applicable, mirror the piece.
7          Track Variants                     Shows additional variants matching the current filter selection.
8          Selected Endpoint                  Each option corresponds to one of the track's endpoints. Endpoints that are already in use are hidden unless all endpoints are connected.
9          Mirror                             Mirrors the selected piece along the primary belt direction.
========== ================================== ====================================================================

Dataset
-------

The dataset is a collection of USD files used to assemble conveyor systems. Each USD file must:

- Define a default prim. That prim and all of its children load when the asset is referenced.
- Use an identity transform on the default prim (translate and rotate components set to zero).
- Define each conveyor track as an ``Xform`` prim, with all visual and collision meshes parented under it.
- Place the track's entry point at the origin, aligned with the X axis, centered on the Y axis.
- Place anchor points at the end of the track at ``Z = 0``, centered on the Y axis. The X axis must be aligned with the base direction of the track.
- Assign individual materials per track. Meshes that share the same conveyor base prim may share materials.
- Live under a single base folder. Assets may still reference files outside that folder.

A JSON file accompanies the asset dataset. It provides the metadata required by the UI workflow and the parameters used to configure conveyor physics when the source assets do not already embed them.

    .. literalinclude:: ../../snippets/digital_twin/warehouse_logistics/ext_isaacsim_asset_gen_conveyor/dataset.json
        :language: json

.. note::
    Strict JSON does not allow comments. The snippet above includes inline comments only to explain each field. Remove the comments before using the file, otherwise the extension will fail to load it.
    For a complete reference, see the JSON file in the extension's ``data`` folder.


Changing the configuration and dataset source
---------------------------------------------

To replace the dataset and configuration file with your own:

1. Go to **Edit > Preferences > Conveyor Builder**.
2. Set the configuration file path and the **Conveyor Assets Location**. The assets must reside directly inside the folder listed in **Conveyor Assets Location**.

To restore the original settings, click **Reset To Default**.


Improving load time
-------------------

By default, the tool reads assets from the cloud-hosted assets folder and downloads each asset the first time it is used. This can introduce noticeable load times. To reduce them, download the assets locally and point the **Conveyor Assets Location** at the local folder.

Available tracks
^^^^^^^^^^^^^^^^

.. list-table::

    * - .. figure:: /images/isaac_conveyor_ConveyorBelt_A01.usd.png
            :align: center
            :alt: Conveyor A01
            :width: 100%

      - .. figure:: /images/isaac_conveyor_ConveyorBelt_A02.usd.png
            :align: center
            :alt: Conveyor A02
            :width: 100%

      - .. figure:: /images/isaac_conveyor_ConveyorBelt_A03.usd.png
            :align: center
            :alt: Conveyor A03
            :width: 100%

    * - .. figure:: /images/isaac_conveyor_ConveyorBelt_A04.usd.png
            :align: center
            :alt: Conveyor A04
            :width: 100%

      - .. figure:: /images/isaac_conveyor_ConveyorBelt_A05.usd.png
            :align: center
            :alt: Conveyor A05
            :width: 100%

      - .. figure:: /images/isaac_conveyor_ConveyorBelt_A06.usd.png
            :align: center
            :alt: Conveyor A06
            :width: 100%

    * - .. figure:: /images/isaac_conveyor_ConveyorBelt_A07.usd.png
            :align: center
            :alt: Conveyor A07
            :width: 100%

      - .. figure:: /images/isaac_conveyor_ConveyorBelt_A08.usd.png
            :align: center
            :alt: Conveyor A08
            :width: 100%

      - .. figure:: /images/isaac_conveyor_ConveyorBelt_A09.usd.png
            :align: center
            :alt: Conveyor A09
            :width: 100%

    * - .. figure:: /images/isaac_conveyor_ConveyorBelt_A10.usd.png
            :align: center
            :alt: Conveyor A10
            :width: 100%

      - .. figure:: /images/isaac_conveyor_ConveyorBelt_A11.usd.png
            :align: center
            :alt: Conveyor A11
            :width: 100%

      - .. figure:: /images/isaac_conveyor_ConveyorBelt_A12.usd.png
            :align: center
            :alt: Conveyor A12
            :width: 100%

    * - .. figure:: /images/isaac_conveyor_ConveyorBelt_A13.usd.png
            :align: center
            :alt: Conveyor A13
            :width: 100%

      - .. figure:: /images/isaac_conveyor_ConveyorBelt_A14.usd.png
            :align: center
            :alt: Conveyor A14
            :width: 100%

      - .. figure:: /images/isaac_conveyor_ConveyorBelt_A15.usd.png
            :align: center
            :alt: Conveyor A15
            :width: 100%

    * - .. figure:: /images/isaac_conveyor_ConveyorBelt_A16.usd.png
            :align: center
            :alt: Conveyor A16
            :width: 100%

      - .. figure:: /images/isaac_conveyor_ConveyorBelt_A17.usd.png
            :align: center
            :alt: Conveyor A17
            :width: 100%

      - .. figure:: /images/isaac_conveyor_ConveyorBelt_A18.usd.png
            :align: center
            :alt: Conveyor A18
            :width: 100%
    * - .. figure:: /images/isaac_conveyor_ConveyorBelt_A19.usd.png
            :align: center
            :alt: Conveyor A19
            :width: 100%

      - .. figure:: /images/isaac_conveyor_ConveyorBelt_A20.usd.png
            :align: center
            :alt: Conveyor A20
            :width: 100%

      - .. figure:: /images/isaac_conveyor_ConveyorBelt_A21.usd.png
            :align: center
            :alt: Conveyor A21
            :width: 100%

    * - .. figure:: /images/isaac_conveyor_ConveyorBelt_A22.usd.png
            :align: center
            :alt: Conveyor A22
            :width: 100%

      - .. figure:: /images/isaac_conveyor_ConveyorBelt_A23.usd.png
            :align: center
            :alt: Conveyor A23
            :width: 100%

      - .. figure:: /images/isaac_conveyor_ConveyorBelt_A24.usd.png
            :align: center
            :alt: Conveyor A24
            :width: 100%
    * - .. figure:: /images/isaac_conveyor_ConveyorBelt_A25.usd.png
            :align: center
            :alt: Conveyor A25
            :width: 100%

      - .. figure:: /images/isaac_conveyor_ConveyorBelt_A26.usd.png
            :align: center
            :alt: Conveyor A26
            :width: 100%

      - .. figure:: /images/isaac_conveyor_ConveyorBelt_A27.usd.png
            :align: center
            :alt: Conveyor A27
            :width: 100%

    * - .. figure:: /images/isaac_conveyor_ConveyorBelt_A28.usd.png
            :align: center
            :alt: Conveyor A28
            :width: 100%

      - .. figure:: /images/isaac_conveyor_ConveyorBelt_A29.usd.png
            :align: center
            :alt: Conveyor A29
            :width: 100%

      - .. figure:: /images/isaac_conveyor_ConveyorBelt_A30.usd.png
            :align: center
            :alt: Conveyor A30
            :width: 100%
    * - .. figure:: /images/isaac_conveyor_ConveyorBelt_A31.usd.png
            :align: center
            :alt: Conveyor A31
            :width: 100%

      - .. figure:: /images/isaac_conveyor_ConveyorBelt_A32.usd.png
            :align: center
            :alt: Conveyor A32
            :width: 100%

      - .. figure:: /images/isaac_conveyor_ConveyorBelt_A33.usd.png
            :align: center
            :alt: Conveyor A33
            :width: 100%

    * - .. figure:: /images/isaac_conveyor_ConveyorBelt_A34.usd.png
            :align: center
            :alt: Conveyor A34
            :width: 100%

      - .. figure:: /images/isaac_conveyor_ConveyorBelt_A37.usd.png
            :align: center
            :alt: Conveyor A37
            :width: 100%

      - .. figure:: /images/isaac_conveyor_ConveyorBelt_A38.usd.png
            :align: center
            :alt: Conveyor A38
            :width: 100%
    * - .. figure:: /images/isaac_conveyor_ConveyorBelt_A39.usd.png
            :align: center
            :alt: Conveyor A39
            :width: 100%

      - .. figure:: /images/isaac_conveyor_ConveyorBelt_A40.usd.png
            :align: center
            :alt: Conveyor A40
            :width: 100%

      - .. figure:: /images/isaac_conveyor_ConveyorBelt_A41.usd.png
            :align: center
            :alt: Conveyor A41
            :width: 100%

    * - .. figure:: /images/isaac_conveyor_ConveyorBelt_A42.usd.png
            :align: center
            :alt: Conveyor A42
            :width: 100%

      - .. figure:: /images/isaac_conveyor_ConveyorBelt_A43.usd.png
            :align: center
            :alt: Conveyor A43
            :width: 100%

      - .. figure:: /images/isaac_conveyor_ConveyorBelt_A44.usd.png
            :align: center
            :alt: Conveyor A44
            :width: 100%
    * - .. figure:: /images/isaac_conveyor_ConveyorBelt_A45.usd.png
            :align: center
            :alt: Conveyor A45
            :width: 100%

      - .. figure:: /images/isaac_conveyor_ConveyorBelt_A46.usd.png
            :align: center
            :alt: Conveyor A46
            :width: 100%

      - .. figure:: /images/isaac_conveyor_ConveyorBelt_A47.usd.png
            :align: center
            :alt: Conveyor A47
            :width: 100%

    * - .. figure:: /images/isaac_conveyor_ConveyorBelt_A48.usd.png
            :align: center
            :alt: Conveyor A48
            :width: 100%

      - .. figure:: /images/isaac_conveyor_ConveyorBelt_A49.usd.png
            :align: center
            :alt: Conveyor A49
            :width: 100%
      -


.. _isaac_conveyor_custom_sim:

Custom conveyor belt simulation
===============================

As an alternative to the built-in physics simulation, you can compute the friction forces between conveyor belt surfaces and the rigid bodies they transport with custom logic. This approach gives you direct control over the friction model and makes it easier to handle cases where a rigid body contacts multiple conveyor belts running at different speeds.

The conveyor belt standalone example demonstrates one such implementation. It is located in ``standalone_examples/conveyor_belt``. To run the sample, use the |isaac-sim| Python launcher (``python.sh`` on Linux or ``python.bat`` on Windows). The entry point is ``cb_app.py``::

    ./python.sh ./standalone_examples/conveyor_belt/cb_app.py

The sample registers transported rigid bodies and conveyor belt sections up front. Two helper classes manage the registration: ``BodyManager`` and ``ConveyorBeltManager``. Once all rigid bodies and conveyor belt sections are registered, these classes allocate the data buffers required for the custom force computation. The registration sequence is shown in ``cb_scene.py``, which builds the conveyor belt circuit and the transported rigid bodies.

Register a rigid body to be transported by the conveyor belts as follows::

    body_manager.add_body(
        "/World/body0",
        body_material0_index
    )

The method takes the rigid body's USD prim path and a material index. Material indices come from another helper class, ``MaterialPairManager``. Because the sample computes friction forces itself, the physics materials used by the built-in simulation must use a friction coefficient of zero. Otherwise, the built-in friction forces would compound with the custom forces. The sample sidesteps this by defining its own material system and assigning friction coefficients to material pairs::

    body_material0_index = material_pair_manager.add_transported_body_material_index()

    conveyor_belt_material0_index = material_pair_manager.add_conveyor_belt_material_index()

    material_pair_manager.set_material_pair_friction(body_material0_index, conveyor_belt_material0_index, 0.9)

Belt motion is described by velocity fields. The sample implements two field types:

- A constant velocity field for straight conveyor belt sections.
- A pivot-point velocity field for curved (turning) conveyor belt sections.

The helper class ``VelocityFieldActuator`` creates these fields. Given a velocity field, register a conveyor belt section as follows::

    target_velocity = wp.vec3(0.0, 0.5, 0.0)

    velocity_field_id = velocity_field_actuator.add_constant_velocity_field(
        target_velocity,
    )

    surface_normal = wp.vec3(0.0, 0.0, 1.0)

    conveyor_belt_manager.add_conveyor_belt(
        "/World/conveyor_belt0",
        VELOCITY_FIELD_TYPE_CONSTANT_VELOCITY,
        velocity_field_id,
        surface_normal,
        conveyor_belt_contact_processing_threshold,
        conveyor_belt_material0_index,
    )

This call requires the USD path of the geometry prim representing the conveyor belt section, the velocity field type, and the velocity field ID. As with rigid body registration, a material index is required. See the sample source for details on the remaining parameters.

After all rigid bodies and conveyor belt sections are registered, the helper classes allocate the buffers used to compute the friction forces. The full set of registered prims is also used to construct an ``isaacsim.core.prims.RigidPrim`` view. This view exposes the rigid body simulation state and, in particular, the detailed contact information needed to derive the custom friction forces. The sample uses |warp| to implement the force computation, which keeps most of the data on the GPU.

For a deeper walkthrough, including a per-file summary, advantages, disadvantages, current limitations, and proposed extensions, see ``standalone_examples/conveyor_belt/README.md``.
