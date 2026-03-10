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
==================

The Conveyor Belt Utility Extension provides an utility to turn Rigid bodies into conveyors in |isaac-sim|.

.. _isaac_conveyor_usage:

Usage
==================

To use the extension:

1. Select **Window > Extensions**. 
2. Search for "conveyor".
3. Select ``isaacsim.asset.gen.conveyor.ui``, and click on **Enable**. This will enable both the extension and it's UI interface.

To auto-load this extension in the future, click on **Autoload** near the top of the ``isaacsim.asset.gen.conveyor.ui`` information pane of the extension manager.

To create a conveyor:

1. Select a rigid body or a mesh in the stage.
2. Go to the **Create > Isaac Sim > Warehouse Items > Conveyor**, to create a |omnigraph| node that will manage the conveyor speed and animation, with the following properties:

      - conveyorPrim: The target that will have the conveyor velocity applied. If it's not a Rigid body it will be automatically configured as one, with default collision models. Only a single prim is allowed per ConveyorNode.
      - Animate Direction: Texture animation direction in the UV map.
      - Animate Scale: ratio between conveyor velocity and texture animation.
      - Animate Texture: flag to enable texture animation.
      - Curved: Flag to indicate a curved conveyor belt. When true, applies angular velocity instead of linear velocity. The velocity is applied along the specified Direction as a rotation axis. The Direction axis can be scaled to adjust the velocity, with values greater than 1 increasing the curvature radius and values less than 1 decreasing it. For example, setting Direction to (0, 0, 1) will rotate about the Z axis, a common use case.
      - Direction: Conveyor velocity direction in local coordinates.
      - Enabled: Flag to enable/disable the conveyor system.
      - Velocity: Conveyor velocity.



This |omnigraph| comes preconfigured with a variable for the velocity, so it can be changed by selecting the |omnigraph| prim directly. If you have multiple conveyors on a scene, you can also synchronize all velocities by selecting a single |omnigraph|'s variable in the read variable node (`read_speed`). 

To emulate a conveyor animation, you can use a tiled texture, and set the **Animate** properties to have the texture translate in the same direction and velocity of the conveyor movement.

Alternatively, you can define your own |omnigraph| and manually add the Conveyor nodes to it, letting you have multiple conveyor nodes on the same |omnigraph|.

For convenience, multiple conveyor pieces are provided with the |isaac-sim_short| assets package are available standalone on the |isaac-sim_short| default assets package at `Isaac/Props/Conveyors`.

When authoring the Conveyor functionality for these assets, be sure to have the `Belt` or `Rollers` prim selected, as these are the prims that contains the meshes for the conveyor elements.


Digital Twin Library Conveyor System Generator
==============================================

To facilitate the creation of Digital Twins, a utility to generate conveyor systems is provided at **Tools > Conveyor Track Builder**. This utility ships with our Digital Twin assets pack for conveyors, but you can use your own dataset, provided that you change the configuration file.

If an item selected on the screen is a component of the conveyor dataset, it will try to connect to one of the conveyor endpoints, as defined by the configuration, otherwise it will use the selection as a parent for the insertion of the new piece.

.. image:: /images/isim_4.5_base_tut_viewport_conveyor_track_builder.png
    :align: center


The configurator is made with loose integration with the assets, allowing flexibility when creating the conveyor system, with a minimal set of rules to facilitate the creation. This may cause the need for some minimal post-processing after creating the system, being a compromise so it won't block you from fully customizing their track after it's modeled.

User Interface
---------------
.. image:: /images/isaac_conveyor_ui.png
    :width: 40%
    :align: center

========== ================================== ====================================================================
Ref #      Option                             Result
========== ================================== ====================================================================
1          Conveyor Style                     | Styles of Conveyor Available, Can be Roller, Belt, or Dual
2          Track Type                         | Track Types, Can be Start, T-style split, straight, Y-style split, end.
3          Curvature                          | Track Curvature, Can be None, Half (usually for 90 degrees), or Full (usually for 180 degrees turn), to the left or right.
4          Elevation                          | Track Elevation. Can be one-level or two-levels up from the entry point, either Up or Down.
5          Selected Track                     | Shows the current selected track on screen, its endpoints, and the Delete button to remove the current track from the system.
6          New Track                          | Shows the piece marked for addition on the system. Lets you choose the input point, the track variants available on the dataset, and in some cases, gives the option to use a mirror of the piece
7          Track Variants                     | Shows the additional variants for the filter selection
8          Selected Endpoint                  | Each option relates to one of the track endpoints. Endpoints already used will not show on the UI, unless all endpoints are already connected.
9          Mirror                             | Mirrors the selected piece on the primary belt direction
========== ================================== ====================================================================

Dataset
--------

The dataset is a collection of USD files used for the system creation. Each USD file must:

- Have a Default Prim defined. That prim and all its children is what will be loaded when your asset is loaded as a reference.
- Have the default prim with an empty transform (Translate and rotation components set to zero).
- Have each conveyor track defined as an Xform Prim, with all visual/collision meshes parented by this Prim.
- Have the entry point of the tracks at the Origin, with the track aligned with the X-axis, with the origin at the middle of the track on the Y axis.
- Have the anchor points defined at Height zero (Z = 0), at the end of the track, aligned to the middle of the track in the Y axis. The X axis must be aligned with the base direction of the Track.
- Have individual materials defined for each track. Meshes that are part of the same conveyor base Prim can share materials.
- Be contained on the same base folder. They can have references to assets outside this base folder.

Accompanying the assets dataset, there is a JSON file that contains the metadata needed to the UI workflow, and to configure the conveyor physics, if the original assets don't have the conveyor physics already embedded.

    .. literalinclude:: ../../snippets/digital_twin/warehouse_logistics/ext_isaacsim_asset_gen_conveyor/dataset.json
        :language: json

.. note::
    Strict JSON types do not have comments, the snippet above have them included to explain the data. If you copy it, remember to remove the comments otherwise it will fail the extension.
    For a full version of the JSON file, check the data folder in the extension.


Changing the Configuration and Dataset Source
----------------------------------------------

To change the dataset to be used, and the configuration file with your own:

1. Go to **Edit** > **Preferences** > **Conveyor Builder**. 
2. Choose the source path to be used in either. The assets must be in the direct folder listed in the Conveyor Assets Location.

If you want to restore the original settings, click **Reset To Default**. 


Improving Load Time
--------------------

By default, the tool uses the cloud-based assets folder. Because the tool only downloads the assets from the cloud the first time they are used, it can result in long wait times while the asset is loaded. To reduce this time, you can download the assets locally and update your assets location to the local path.

Available Tracks
^^^^^^^^^^^^^^^^^

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

