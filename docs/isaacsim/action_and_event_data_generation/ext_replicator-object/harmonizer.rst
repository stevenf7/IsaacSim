..
   Copyright (c) 2022-2026, NVIDIA CORPORATION. All rights reserved.
   NVIDIA CORPORATION and its licensors retain all intellectual property
   and proprietary rights in and to this software, related documentation
   and any modifications thereto. Any use, reproduction, disclosure or
   distribution of this software and related documentation without an express
   license agreement from NVIDIA CORPORATION is strictly prohibited.



.. _harmonizer:

============================
Harmonizer
============================

A harmonizer defines the relationship among randomized :ref:`mutable attributes<mutable attribute>`.

If the key-value pair in the description file has a key of ``harmonizer_type``, it defines a harmonizer. A harmonizer constrains how a mutable attribute randomizes.

**Permutation harmonizer**

If ``harmonizer_type`` is ``permutate``, it is a permutation harmonizer. When you :ref:`free randomize<simulation workflow>` a ``harmonized`` mutable attribute, you can specify a ``pitch`` as the input to the permutation harmonizer. Then the permutation harmonizer shuffles these inputs and sends back the value to the harmonized attribute, which in turn can be used in a transform operator in the :ref:`harmonized randomize stage<simulation workflow>`.

For example, to define three OROs, facing in three directions:

.. code:: yaml 

  oro:
    count: 3
    type: geometry
    subtype: mesh
    usd_path: [PATH_TO_ORO]
    transform_operators:
    - translate:
      - ($[../index] % $[../count] - 1) * 600
      - 0
      - 0
    - rotateY: ($[../index] - 1) * 60

These three OROs have X-axis position ``-600, 0, 600``; and they are rotated around Y-axis by ``-60, 0, 60`` degrees.

.. image:: /images/ext_replicator-object/isim_5.0_replicator_ext-isaacsim.replicator.object-0.4.2_viewport_harmonizer-6.png
    :width: 400
    
To shuffle the positions of these OROs, so that the ORO that rotates ``-60`` degrees can appear to the right:

Define a mutable attribute ``permutated_index`` as ``harmonized``. During the free randomize stage, it submits its index as its ``pitch`` to the harmonizer ``permutate_H``, which is a permutation harmonizer.

.. code:: yaml 

  oro:
    ...
    permutated_index:
      distribution_type: harmonized
      harmonizer_name: permutate_H
      pitch: $[index]
  permutate_H:
    harmonizer_type: permutate

During the harmonize stage, ``permutate_H`` shuffles the received pitches from all relevant harmonized mutable attributes and resonates them back to each of them.

During the harmonized randomize stage, ``permutated_index`` gets the shuffled value back. You can use it in transform operators, like using an index.

.. code:: yaml 

  oro:
    ...
    transform_operators:
    - translate:
      - ($[permutated_index] % $[../count] - 1) * 600
      - 0
      - 0
    - rotateY: ($[../index] - 1) * 60

.. image:: /images/ext_replicator-object/isim_5.0_replicator_ext-isaacsim.replicator.object-0.4.2_viewport_harmonizer-7.png
    :width: 400

.. image:: /images/ext_replicator-object/isim_5.0_replicator_ext-isaacsim.replicator.object-0.4.2_viewport_harmonizer-8.png
    :width: 400

This feature can be used with any values within scope. 

**Bin pack harmonizer**

If ``harmonizer_type`` is ``bin_pack``, it is a bin pack harmonizer that packs objects into a cuboid space according to their axis-aligned bounding boxes. You can define a cuboid with custom dimensions like this:

.. code:: yaml 

  bin_pack_H:
    harmonizer_type: bin_pack
    bin_size:
    - 480
    - 260
    - 700

You can define many OROs, and pack them into this cuboid:

.. code:: yaml 

  oro:
    count: 200
    physics: rigidbody
    type: geometry
    subtype: mesh
    tracked: true
    transform_operators:
    - translate:
      - 0
      - 300
      - 0
    - transform:
        distribution_type: harmonized
        harmonizer_name: bin_pack_H
        pitch: local_aabb
    - scale:
      - 30
      - 30
      - 30
    usd_path: PATH_TO_ORO

For example, with many OROs densely packed together:

.. image:: /images/ext_replicator-object/isim_5.0_replicator_ext-isaacsim.replicator.object-0.4.2_viewport_harmonizer-bin-pack.png
    :width: 400

In this example, ``200`` OROs are spawned during initialization.

Here are some of the examples of randomized scenes generated using the bin pack harmonizer:


.. image:: /images/ext_replicator-object/isim_5.0_replicator_ext-isaacsim.replicator.object-0.4.2_viewport_gallery_0.png
   :align: center


.. image:: /images/ext_replicator-object/isim_5.0_replicator_ext-isaacsim.replicator.object-0.4.2_viewport_gallery_1.png
   :align: center


.. image:: /images/ext_replicator-object/isim_5.0_replicator_ext-isaacsim.replicator.object-0.4.2_viewport_gallery_2.png
   :align: center


.. image:: /images/ext_replicator-object/isim_5.0_replicator_ext-isaacsim.replicator.object-0.4.2_viewport_gallery_3.png
   :align: center


More insights can be found in the :ref:`harmonization example<harmonization_example>`.