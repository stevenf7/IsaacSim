..
   Copyright (c) 2022-2026, NVIDIA CORPORATION. All rights reserved.
   NVIDIA CORPORATION and its licensors retain all intellectual property
   and proprietary rights in and to this software, related documentation
   and any modifications thereto. Any use, reproduction, disclosure or
   distribution of this software and related documentation without an express
   license agreement from NVIDIA CORPORATION is strictly prohibited.


.. _mutable attribute:

============================
Mutable Attribute
============================

A value in the description file is a mutable attribute if it is a dictionary that has a key ``distribution_type``, or a string that contains :ref:`macros<Macro>` (``$[...]``). A mutable attribute does not have to be part of a mutable; you can have standalone mutable attributes.

You can define mutable attributes with ``distribution_type`` as ``folder``, ``set``, ``range``, ``frustum``, and  ``harmonized``.

**Folder**

A ``folder`` mutable attribute uniformly samples a file from the specified folder with the specified suffix. To define a ``folder`` type, there are two additional required keys, ``suffix`` and ``value``.

.. code:: yaml 

  distractor:
    type: geometry
    subtype: mesh
    usd_path:
      distribution_type: folder
      suffix: usd
      value: $[/resources_root]/distractors

In this example, a geometry named ``distractor``, which is a mesh loaded from a USD file, is defined. And the USD file is randomly selected from all files in ``$[/resources_root]/distractors`` that has a ``.usd`` extension.

.. note:: Some example description files have :ref:`placeholders<Placeholders>`.

**Set**

A ``set`` attribute randomly selects a value from a set. 

.. code:: yaml 

  dome_light:
    type: light
    subtype: dome
    texture_path:
      distribution_type: set
      values:
      - $[/skies]/adams_place_bridge_4k.hdr
      - $[/skies]/autoshop_01_4k.hdr

In this example, a dome light is defined with a texture of either ``$[/skies]/adams_place_bridge_4k.hdr`` or ``$[/skies]/autoshop_01_4k.hdr``, selected randomly.

**Range**

A ``range`` attribute specifies the range of randomization for a numeric value.

.. code:: yaml 

  dome_light:
    type: light
    subtype: dome
    intensity:
      distribution_type: range
      start: 1000
      end: 3000

Here the dome light defined has an intensity as a random number within ``[1000, 3000]``.

**Camera frustum**

A ``camera_frustum`` attribute is specially used for sampling a value for the translate operator (Refer to :ref:`Transformation`). It samples a position in a view frustum defined by ``camera_parameters``, which is the same as in :ref:`Camera`.

.. code:: yaml 

  main_object:
    ...
    transform_operators:
    - translate:
        distribution_type: camera_frustum
        camera_parameters: $[/camera_parameters]
        distance_min: 200
        distance_max: 600
        screen_space_range: 0.5

``distance_min`` and ``distance_max`` are the minimum and maximum distance from the view point. ``screen_space_range`` is the range in screen space on which to scatter objects. For example, if you set it to ``0.5``, the objects are only scattered in the space projected to the area specified within the dotted lines:

.. image:: /images/ext_replicator-object/isim_5.0_replicator_ext-isaacsim.replicator.object-0.4.2_viewport_mutable-attribute-2.png
    :width: 400

Camera frustum doesn't scatter objects uniformly along the line of vision. It's scattered more often in the near field and the far field, such that the probability density of projected area is constant. For example, below is a uniformly sampled in (a) while sampling more in the near field in (b). In (b), the projected areas are more evenly spaced compared to (a).

.. image:: /images/ext_replicator-object/isim_5.0_replicator_ext-isaacsim.replicator.object-0.4.2_viewport_mutable-attribute-1.png
    :width: 400

For the same object, it's more likely to be sampled near ``distance_min`` than ``distance_max`` such that a position that gives a projection ten pixels wide has the same possibility to be sampled with a position that gives a projection twenty pixels wide. 

Such a distance is given by:

.. math::

    distance = \frac{distanceMin \cdot distanceMax}{distanceMin + (distanceMax - distanceMin) \cdot randomUnit}

in which :math:`randomUnit` is uniformly sampled within ``[0,1]``.

**Harmonized**

A ``harmonized`` attribute defines an attribute that retrieves its value from a :ref:`harmonizer` after :ref:`harmonization<simulation workflow>`. More details can be found in the :ref:`harmonization example<harmonization_example>`.