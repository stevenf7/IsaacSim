..
   Copyright (c) 2022-2026, NVIDIA CORPORATION. All rights reserved.
   NVIDIA CORPORATION and its licensors retain all intellectual property
   and proprietary rights in and to this software, related documentation
   and any modifications thereto. Any use, reproduction, disclosure or
   distribution of this software and related documentation without an express
   license agreement from NVIDIA CORPORATION is strictly prohibited.




.. _Geometry:

============================
Geometry
============================

If a mutable has attribute ``type`` of ``geometry``, it's a geometry. A geometry is a substance in space.

Available attributes of ``geometry``:

+--------------+--------------+--------------------------------------------------------------------------------------------------------------+
| Name         | Type         | Description                                                                                                  |
+==============+==============+==============================================================================================================+
| subtype      | string       | refer to Basic shapes, Deformed shape, Room, Compound, Pyramid, and Mesh loaded from USD                     |
+--------------+--------------+--------------------------------------------------------------------------------------------------------------+
| physics      | string       | ``collision`` or ``rigidbody``                                                                               |
+--------------+--------------+--------------------------------------------------------------------------------------------------------------+
| is_instance  | bool         | whether the geometry is instanced - default to true; required to be false for shader attribute randomization |
+--------------+--------------+--------------------------------------------------------------------------------------------------------------+

If ``physics`` is set to ``rigidbody``, the object is a dynamic object that responds to physics. If it's set to ``collision``, the object is a static object that dynamic objects interact with. For example, a wall can have ``collision`` and a ping-pong ball bouncing off of it has ``rigidbody``.

**Physics Properties Randomization**

When ``physics`` is set to ``rigidbody`` or ``collision``, you can randomize various physics properties to create more diverse simulations. The following properties can be randomized using :ref:`distribution types<mutable attribute>`:

+---------------------------+-------------+--------------------------------------------------------------------------------------------------------------+
| Property                  | Type        | Description                                                                                                  |
+===========================+=============+==============================================================================================================+
| friction                  | numeric     | Friction coefficient (both static and dynamic). Defaults to the global friction setting if not specified.    |
+---------------------------+-------------+--------------------------------------------------------------------------------------------------------------+
| linear_damping            | numeric     | Linear damping coefficient for rigidbody objects. Defaults to the global linear_damping setting.             |
+---------------------------+-------------+--------------------------------------------------------------------------------------------------------------+
| angular_damping           | numeric     | Angular damping coefficient for rigidbody objects. Defaults to the global angular_damping setting.           |
+---------------------------+-------------+--------------------------------------------------------------------------------------------------------------+
| concave                   | bool        | Whether to use convex decomposition for collision detection. Defaults to ``False`` (uses convex hull).       |
+---------------------------+-------------+--------------------------------------------------------------------------------------------------------------+
| initial_velocity          | list        | Initial linear velocity as [x, y, z]. Each component can be randomized using distribution types.             |
+---------------------------+-------------+--------------------------------------------------------------------------------------------------------------+
| initial_angular_velocity  | list        | Initial angular velocity as [x, y, z]. Each component can be randomized using distribution types.            |
+---------------------------+-------------+--------------------------------------------------------------------------------------------------------------+

Example of randomizing physics properties:

.. code:: yaml

   box:
     type: geometry
     subtype: cube
     physics: rigidbody
     friction:
       distribution_type: range
       start: 0.1
       end: 0.9
     linear_damping:
       distribution_type: range
       start: 0
       end: 5
     initial_velocity:
     - 0.0
     - distribution_type: range
       start: 50.0
       end: 100.0
     - 0.0

**Basic shapes**

If ``subtype`` is one of ``cone``, ``cube``, ``cylinder``, ``disk``, ``torus``, ``plane``, or ``sphere`` it defines the corresponding basic geometry.

**Compound geometry**

If ``subtype`` is ``compound``, it defines a compound geometry composed of multiple parts forming a single rigid body. Each part can be a basic shape (cube, sphere, cylinder, capsule, or cone). The compound geometry is useful for creating complex objects like rockets or multi-part assemblies.

Attributes of compound geometry:

+-----------------------+-------------+---------------------------------------------+
| Name                  | Type        | Description                                 |
+=======================+=============+=============================================+
| parts                 | dict        | Dictionary of part definitions. Each part   |
|                       |             | has a ``subtype`` (cube, sphere, cylinder,  |
|                       |             | capsule, or cone) and optional attributes   |
|                       |             | like ``color``, ``transform_operators``,    |
|                       |             | and size parameters (e.g., ``radius``,      |
|                       |             | ``height``, ``size``).                      |
+-----------------------+-------------+---------------------------------------------+

Example of compound geometry:

.. code:: yaml

   rocket:
     type: geometry
     subtype: compound
     physics: rigidbody
     parts:
       main_capsule:
         subtype: capsule
         radius: 10.0
         height: 25.0
         color: [0.8, 0.1, 0.1]
         transform_operators:
         - translate: [0, 0, 30.0]
       side_booster:
         subtype: capsule
         radius: 5.0
         height: 10.0
         color: [0.8, 0.1, 0.1]
         transform_operators:
         - translate: [30.0, 0, 20.0]

**Pyramid geometry**

If ``subtype`` is ``pyramid``, it defines a pyramid structure composed of multiple boxes arranged in a regular pyramid pattern. The pyramid creates a stable structure where row i (0 to pyramid_size-1) has (pyramid_size - i) boxes. Box sizes and colors can be randomized per box, but positions are regular/ordered for physics stability.

Attributes of pyramid geometry:

+-----------------------+-------------+---------------------------------------------+
| Name                  | Type        | Description                                 |
+=======================+=============+=============================================+
| pyramid_size          | numeric     | Number of rows in the pyramid. Total boxes  |
|                       |             | = pyramid_size * (pyramid_size + 1) / 2.    |
|                       |             | Can be randomized using distribution types. |
+-----------------------+-------------+---------------------------------------------+
| y_position            | numeric     | Y position (height) of the pyramid base.    |
+-----------------------+-------------+---------------------------------------------+
| offset                | numeric     | Spacing offset between boxes. Default: 1.0  |
+-----------------------+-------------+---------------------------------------------+
| box_size              | numeric     | Size of each box. Can be a constant value   |
|                       |             | or a distribution (range) for per-box       |
|                       |             | randomization.                              |
+-----------------------+-------------+---------------------------------------------+
| color                 | list        | Color of boxes. Can be randomized per box.  |
+-----------------------+-------------+---------------------------------------------+

Example of pyramid geometry:

.. code:: yaml

   box_pyramid:
     type: geometry
     subtype: pyramid
     physics: rigidbody
     tracked: true
     pyramid_size:
       distribution_type: range
       start: 5
       end: 15
     y_position: -0.24377
     offset: 1.0
     box_size:
       distribution_type: range
       start: 7
       end: 17
     color:
     - distribution_type: range
       start: 0.3
       end: 1.0
     - distribution_type: range
       start: 0.3
       end: 1.0
     - distribution_type: range
       start: 0.3
       end: 1.0

**Deformed shape**

Physics simulation for bottles is not supported.

If ``subtype`` is ``bottle``, it defines a bottle shape, which is a parameterized deformed geometry controlled by the following parameters:

+-----------------------+-------------+--------------------------------------------+
| Name                  | Type        | Description                                |
+=======================+=============+============================================+
| base_effector         | string      | vertical position of the base effector     |
+-----------------------+-------------+--------------------------------------------+
| neck_effector         | string      | vertical position of the neck effector     |
+-----------------------+-------------+--------------------------------------------+
| horizontal_effector   | string      | horizontal position of the body effector   |
+-----------------------+-------------+--------------------------------------------+
| vertical_effector     | string      | vertical position of the body effector     |
+-----------------------+-------------+--------------------------------------------+

This image illustrates how the shape of the bottle is controlled by these four effectors.

.. image:: /images/ext_replicator-object/isim_5.0_replicator_ext-isaacsim.replicator.object-0.4.2_viewport_geometry-bottle.png
    :width: 400

.. note:: We currently don't yet have collision detection for deformed shapes; they don't have physics.

**Room geometry**

If ``subtype`` is ``room``, it defines a room geometry with optional table and walls created using RoomHelper from PhysX demos. This is useful for creating enclosed environments for physics simulations.

Attributes of room geometry:

+-----------------------+-------------+--------------------------------------------+
| Name                  | Type        | Description                                |
+=======================+=============+============================================+
| table_width           | numeric     | Width of the table. Default: 500.0         |
+-----------------------+-------------+--------------------------------------------+
| table_depth           | numeric     | Depth of the table. Default: 500.0         |
+-----------------------+-------------+--------------------------------------------+
| has_table             | bool        | Whether to create a table. Default: True   |
+-----------------------+-------------+--------------------------------------------+
| has_walls             | bool        | Whether to create walls. Default: True     |
+-----------------------+-------------+--------------------------------------------+
| zoom                  | numeric     | Zoom factor for room size. Default: 0.5    |
+-----------------------+-------------+--------------------------------------------+
| table_rotation        | numeric     | Rotation of the table in degrees. Can be   |
|                       |             | randomized using distribution types.       |
+-----------------------+-------------+--------------------------------------------+
| floor_color           | list        | Color of the floor as [r, g, b]. Can be    |
|                       |             | randomized using distribution types.       |
+-----------------------+-------------+--------------------------------------------+

Example of room geometry:

.. code:: yaml

   demo_room:
     type: geometry
     subtype: room
     table_width: 500.0
     table_depth: 500.0
     has_table: true
     has_walls: true
     zoom: 0.5
     table_rotation:
       distribution_type: range
       start: 0
       end: 360
     floor_color:
     - 0.5
     - 0.75
     - 1.0

**Mesh loaded from USD**

If ``subtype`` is ``mesh``, it defines a mesh loaded from USD.

Additional attribute of mesh:

+-----------------------+-------------+--------------------------------------------+
| Name                  | Type        | Description                                |
+=======================+=============+============================================+
| usd_path              | string      | The path to the USD                        |
+-----------------------+-------------+--------------------------------------------+
