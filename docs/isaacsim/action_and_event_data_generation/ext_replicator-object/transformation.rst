..
   Copyright (c) 2022-2026, NVIDIA CORPORATION. All rights reserved.
   NVIDIA CORPORATION and its licensors retain all intellectual property
   and proprietary rights in and to this software, related documentation
   and any modifications thereto. Any use, reproduction, disclosure or
   distribution of this software and related documentation without an express
   license agreement from NVIDIA CORPORATION is strictly prohibited.


.. _Transformation:

============================
Transformation
============================

This page discusses how to move things around.

The position, orientation, and size of an object in the scene must be defined by a sequence of transform operators (also known as a scene graph). This sequence is ordered such that global transforms are towards the top, while local transforms are towards the bottom. If you are not familiar with what "global" and "local" means, here is an example:

Scene Graph Example
-------------------

Imagine that there is an observatory that has a movable base, a dome that can rotate around and a retractable scope that can rotate up and down. Inside the observatory sits a bird, Oro. You are sitting at the scope head, looking at Oro. And assume that Oro is frozen in space, so that if the observatory moves, it moves relative to Oro and you want to see Oro from different perspectives. The whole setting is:

.. image:: /images/ext_replicator-object/isim_5.0_replicator_ext-isaacsim.replicator.object-0.4.2_viewport_transformation-0.png
    :width: 400

The scope head points towards the positive direction of the Z-axis, so we are looking towards the negative direction of Z-axis. Because the scope is retractable, start at zero length, so that we are inside Oro's body. This is the starting pose, if no transform operators are defined at all.

Define these entities in your descriptions. A camera, with camera parameters defined as described in :ref:`Camera`; A :ref:`Dome light <Dome light>` so that you can see things; and Oro, which is a :ref:`Geometry`. The observatory is only conceptual, you don't need to see it. 

.. code:: yaml

  dome_light:
    type: light
    subtype: dome
    intensity: 1000

  default_camera:
    type: camera
    camera_parameters: $[/camera_parameters]

  penguin:
    type: geometry
    subtype: mesh
    usd_path: [PATH_TO_PENGUIN]

.. note:: If no camera is defined, no images are output, because nothing is there to see.

Extend the scope along the Z-axis using the ``translate`` operator, so that you are 1000 units way from Oro, and take a picture.

.. image:: /images/ext_replicator-object/isim_5.0_replicator_ext-isaacsim.replicator.object-0.4.2_viewport_transformation-1-1.webp
    :width: 400

.. code:: yaml

  default_camera:
    # ...
    transform_operators:
    - translate:
      - 0
      - 0
      - 1000

.. image:: /images/ext_replicator-object/isim_5.0_replicator_ext-isaacsim.replicator.object-0.4.2_viewport_transformation-1-2.png
    :width: 400
 

Then rotate the scope around the X-axis by 30 degrees. This applies a ``rotateX`` operator, before the original translate.

.. image:: /images/ext_replicator-object/isim_5.0_replicator_ext-isaacsim.replicator.object-0.4.2_viewport_transformation-2-1.webp
    :width: 400

.. code:: yaml

  transform_operators:
  - rotateX: -30
  - translate:
    - 0
    - 0
    - 1000

.. image:: /images/ext_replicator-object/isim_5.0_replicator_ext-isaacsim.replicator.object-0.4.2_viewport_transformation-2-2.png
    :width: 400

To go the other way around, rotate the muzzle itself, and translate it along the Z-axis. In this case the camera looks away from Oro, which is not the intention.

Rotate the turret, giving another operator ``rotateY``:

.. image:: /images/ext_replicator-object/isim_5.0_replicator_ext-isaacsim.replicator.object-0.4.2_viewport_transformation-3-1.webp
    :width: 400

.. code:: yaml

  transform_operators:
  - rotateY: 60
  - rotateX: -30
  - translate:
    - 0
    - 0
    - 1000

.. image:: /images/ext_replicator-object/isim_5.0_replicator_ext-isaacsim.replicator.object-0.4.2_viewport_transformation-3-2.png
    :width: 400

And eventually, drive the observatory forward, which is yet another translate, so that you don't always have Oro at the center of the screen. Because you are defining two translates, add a suffix ``translate_global``:

.. code:: yaml

  transform_operators:
  - translate_global:
    - 0
    - 0
    - 1000
  - rotateY: 60
  - rotateX: -30
  - translate:
    - 0
    - 0
    - 1000

.. image:: /images/ext_replicator-object/isim_5.0_replicator_ext-isaacsim.replicator.object-0.4.2_viewport_transformation-4.png
    :width: 400

.. note:: Duplicated names of transform operators are not allowed. Add ``_suffix`` to differentiate.


To randomize all transform operators with mutable attributes and generate five images:

.. code:: yaml

  transform_operators:
  - translate_global:
      distribution_type: range
      start:
      - -500
      - 0
      - -500
      end:
      - 500
      - 0
      - 500
  - rotateY:
      distribution_type: range
      start: -180
      end: 180
  - rotateX:
      distribution_type: range
      start: -60
      end: 60
  - translate:
      distribution_type: range
      start:
      - 0
      - 0
      - 800
      end:
      - 0
      - 0
      - 1200

.. image:: /images/ext_replicator-object/isim_5.0_replicator_ext-isaacsim.replicator.object-0.4.2_viewport_transformation-5-1.png
    :width: 400

.. image:: /images/ext_replicator-object/isim_5.0_replicator_ext-isaacsim.replicator.object-0.4.2_viewport_transformation-5-2.png
    :width: 400
    
.. image:: /images/ext_replicator-object/isim_5.0_replicator_ext-isaacsim.replicator.object-0.4.2_viewport_transformation-5-3.png
    :width: 400

.. image:: /images/ext_replicator-object/isim_5.0_replicator_ext-isaacsim.replicator.object-0.4.2_viewport_transformation-5-4.png
    :width: 400

.. image:: /images/ext_replicator-object/isim_5.0_replicator_ext-isaacsim.replicator.object-0.4.2_viewport_transformation-5-5.png
    :width: 400

Now you have different views of Oro. The AI model you are about to train will get a better understanding of Oro. 

Transform Operators 
--------------------

All available transform operators are:

**Translate operator**

==================================================================================== ====================
Operator Name                                                                        Required Format
==================================================================================== ====================
translate, rotateXYZ, rotateXZY, rotateYXZ, rotateYZX, rotateZXY, rotateZYX, scale   numeric, list of three elements
orient                                                                               numeric, list of four elements
rotateX, rotateY, rotateZ                                                            numeric
transform                                                                            numeric, list of lists of four by four elements
==================================================================================== ====================

Required format indicates the dimension and type of expected input. ``numeric`` means float or int, or a value evaluated to float or int by macro or mutable attribute. For example:

.. code:: yaml

  rotateXYZ:
  - $[../index]
  - 5
  - 10

is valid, while:

.. code:: yaml

  rotateXYZ:
  - True
  - abc

is not valid.

.. note:: 
  
  * ``orient`` is represented by a quaternion in `wxyz` order, in which `w` is the scalar part; all other rotate operators describe rotation in degrees.

  * The Euler angle sequence is represented from local to global from left to right. For example, rotateXYZ means Y is global rotation relative to X, and Z is global rotation relative to Y.

  * Scale operators appear at the bottom. It's not recommended to define a scale above a translate or rotate, unless this is intended.

Practical Example of Flexible xformOps
----------------------------------------

A translation applied globally to a rotation, is different than the other way around. In an ordinary setting, from global to local, you translate, rotate, and scale an object. In IRO, you can swap the order of linear transformations, because of the flexibility in USD xformOps. To scatter cubes on a section of a sphere using only combination of randomizations in translation and rotation in a different order:

.. code:: yaml

    isaacsim.replicator.object:
      version: 0.x.y
      num_frames: 3
      seed: 0
      output_path: PATH_TO_OUTPUT
      simulation_time: 1
      gravity: 981

      dome_light:
        intensity: 3000
        subtype: dome
        type: light

      size_coef:
        count: 400
        distribution_type: range
        start: 0.0
        end: 1.0
      size_min: 0.5
      size_max: 0.8
      basic_shape:
        count: 400
        type: geometry
        subtype: cube
        tracked: true
        physics: rigidbody
        color:
        - 0.0 + $[/size_coef_$[index]] * 1.0
        - 0.0 + $[/size_coef_$[index]] * 0.0
        - 1.0 + $[/size_coef_$[index]] * -1.0
        size: $[/size_min] + $[/size_coef_$[index]] * ($[/size_max] - $[/size_min])
        transform_operators:
        - rotateY:
            distribution_type: range
            start: -160
            end: 160
        - rotateX:
            distribution_type: range
            start: -60
            end: 0
        - translate:
            distribution_type: range
            start:
            - 0
            - 0
            - 0
            end:
            - 0
            - 0
            - 500
        - rotateXYZ:
            distribution_type: range
            start:
            - -180
            - -180
            - -180
            end:
            - 180
            - 180
            - 180
        - scale:
          - $[../size]
          - $[../size]
          - $[../size]

      plane:
        type: geometry
        subtype: plane
        tracked: true
        physics: collision
        color:
        - 0.5
        - 0.7
        - 0.7
        transform_operators:
        - scale:
          - 10
          - 10
          - 10

      screen_height: 2160
      screen_width: 3840
      focal_length: 14.228393962367306
      horizontal_aperture: 20.955
      camera_parameters:
        screen_width: $[/screen_width]
        screen_height: $[/screen_height]
        focal_length: $[/focal_length]
        horizontal_aperture: $[/horizontal_aperture]
        near_clip: 0.001
        far_clip: 100000
      default_camera:
        camera_parameters: $[/camera_parameters]
        transform_operators:
        - rotateY: 30
        - rotateX: -30
        - translate:
          - 0
          - 0
          - 5000
        type: camera
        
The created scene with :ref:`embedded interface<embedded_interface>`:

.. image:: /images/ext_replicator-object/isim_5.0_replicator_ext-isaacsim.replicator.object-0.4.2_viewport_transformation_flexible_xform_ops.png
    :width: 400

The visualization using the :ref:`distribution visualizer<distribution_visualizer>`:

.. image:: /images/ext_replicator-object/isim_5.0_replicator_ext-isaacsim.replicator.object-0.4.2_viewport_transformation_flexible_xform_ops_distribution.png
    :width: 400
