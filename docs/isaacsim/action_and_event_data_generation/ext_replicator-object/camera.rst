..
   Copyright (c) 2022-2026, NVIDIA CORPORATION. All rights reserved.
   NVIDIA CORPORATION and its licensors retain all intellectual property
   and proprietary rights in and to this software, related documentation
   and any modifications thereto. Any use, reproduction, disclosure or
   distribution of this software and related documentation without an express
   license agreement from NVIDIA CORPORATION is strictly prohibited.



.. _Camera:

============================
Camera
============================

If a mutable has an attribute ``type`` of ``camera``, it's a camera. Typically, a basic pinhole camera model is used. 

Required attributes of a camera:

========================= ==============
Name                      Type
========================= ==============
camera_parameters         dict 
========================= ==============

``camera_parameters`` is a dictionary with the following six required keys:

========================= ==============
Name                      Type
========================= ==============
screen_width              int
screen_height             int
focal_length              numeric
horizontal_aperture       numeric
near_clip                 numeric
far_clip                  numeric
========================= ==============

Pinhole Model
^^^^^^^^^^^^^^^^^^^^^

3D objects are projected onto a 2D plane, like this:

.. image:: /images/ext_replicator-object/isim_5.0_replicator_ext-isaacsim.replicator.object-0.4.2_viewport_camera-1.png
    :width: 400

Looking from a top view, towards the negative Y-axis:

.. image:: /images/ext_replicator-object/isim_5.0_replicator_ext-isaacsim.replicator.object-0.4.2_viewport_camera-2.png
    :width: 400

In the picture, `f`, which is the distance from the camera to the projection plane, is ``focal_length``. `hA` is the distance from the left edge (upper end) to the right edge (lower end) and stands for ``horizontal_aperture``.

``near_clip`` and ``far_clip`` define two planes perpendicular to the line of vision between which you can observe things. 

Assumptions
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The following assumptions are made for the frame of reference and conversion from/to other common representations.

If no transform operator is applied on the camera, the Y-axis points upwards and X-axis points to the right. The camera looks towards negative direction of the Z-axis.

