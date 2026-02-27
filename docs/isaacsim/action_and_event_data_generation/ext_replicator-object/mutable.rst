..
   Copyright (c) 2022-2026, NVIDIA CORPORATION. All rights reserved.
   NVIDIA CORPORATION and its licensors retain all intellectual property
   and proprietary rights in and to this software, related documentation
   and any modifications thereto. Any use, reproduction, disclosure or
   distribution of this software and related documentation without an express
   license agreement from NVIDIA CORPORATION is strictly prohibited.



.. _mutable:

============================
Mutable
============================

If the pair is a dictionary with a key ``type``, it's a mutable. There are four types of mutables: 

* :ref:`Camera` where we are
* :ref:`Geometry` the things we want to observe
* :ref:`Light` how we observe things
* :ref:`Force` forces applied to rigid bodies

Each mutable consists of attributes. Each key-value pair of a mutable is an attribute. An attribute can be a :ref:`mutable attribute`, which mutates per frame. 

Available attributes of mutables are:

==================== ==================== ====================
Name                 Type                 Description
==================== ==================== ====================
type                 string               The type of the mutable, ``camera``, ``geometry``, ``light``, or ``force``.
count                int                  The number of identically defined mutables
tracked              bool                 If the mutable is tracked, its 2d/3D bounding boxes will be output, and it will have a corresponding highlighted color on the segmentation mask.
transform_operators  list                 The transformation of the object.
==================== ==================== ====================

**Transform operators**

Specially, to define its pose in space, the mutable can define a sequenced list of :ref:`transform operators<Transformation>`. A transform operator is also a key-value pair, in which the value can be a mutable attribute.

**Shader attributes**

In Omniverse, a shader has many attributes describing how a mesh is shaded. For example, ``diffuse_texture`` that points to the RGB image, and ``texture_rotate`` that specifies how its texture should be rotated. In ORO, you can control these attributes just like any other mutable attributes. For example, the following description randomizes the tint, and rotates and scales the texture:

.. code:: yaml 
  
  mesh:
    type: geometry
    subtype: mesh
    usd_path: https://omniverse-content-production.s3-us-west-2.amazonaws.com/Assets/ArchVis/Residential/Furniture/Desks/Desk_01.usd
    transform_operators:
    - rotateXYZ:
      - -90
      - 0
      - 0
    shader_attributes:
      texture_rotate:
        distribution_type: range
        start: -180
        end: 180
      diffuse_tint:
        distribution_type: range
        start:
        - 0
        - 0
        - 0
        end:
        - 2
        - 2
        - 2
      texture_scale:
        distribution_type: range
        start:
        - 0.2
        - 0.2
        end:
        - 0.7
        - 0.7

.. image:: /images/ext_replicator-object/isim_5.0_replicator_ext-isaacsim.replicator.object-0.4.2_viewport_shader-attributes-0.png
    :width: 400

.. image:: /images/ext_replicator-object/isim_5.0_replicator_ext-isaacsim.replicator.object-0.4.2_viewport_shader-attributes-1.png
    :width: 400

Specifically, you can do common computer vision operations, such as color mapping to a mesh that has an RGB image as diffuse texture, by doing:

.. code:: yaml 

  shader_attributes:
    diffuse_texture:
      distribution_type: texture
      operation: color_map

Available options are: ``color_map``, ``transform``, ``add_noise``, ``apply_blur``, ``color_shift``, ``invert_color``, ``sobel_edges``, and ``random_mutation``.

**Name, count, and index**

A mutable has a ``name``, which is the key in the key-value pair and potentially an index, if defined in group with a ``count`` attribute. For example:

.. code:: yaml 

  mesh:
    count: 2
    ...

During initialization stage, two mutables are initialized after the description is parsed. For example:
 
.. code:: yaml 

  mesh_0:
    count: 2
    index: 0
    name: mesh_0
    ...

  mesh_1:
    count: 2
    index: 1
    name: mesh_1
    ...

The ``count`` is still there so that you can access how many mutables are in the group. You can use these values to define macros. 