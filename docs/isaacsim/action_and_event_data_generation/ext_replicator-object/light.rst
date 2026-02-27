..
   Copyright (c) 2022-2026, NVIDIA CORPORATION. All rights reserved.
   NVIDIA CORPORATION and its licensors retain all intellectual property
   and proprietary rights in and to this software, related documentation
   and any modifications thereto. Any use, reproduction, disclosure or
   distribution of this software and related documentation without an express
   license agreement from NVIDIA CORPORATION is strictly prohibited.



.. _Light:

============================
Light
============================

If a mutable has attribute ``type`` of ``light``, it's a light. There are directional lights and dome lights. A light has an ``intensity`` attribute. Specifically, a dome light has a ``texture_path`` attribute.

Aside from ordinary attributes of mutables, additional available attributes of lights are:

============================ ====================
Name                         Type 
============================ ====================
intensity                    numeric
color                        numeric, dimension three list
============================ ====================

.. _Direct light:

**Direct light**

In the default pose, a direct light shines towards negative Z-direction.

.. _Dome light:

**Dome light**

A dome light has light beams coming from all directions.

Additionally, available attributes of dome light are:

============================ ====================
Name                         Type 
============================ ====================
texture_path                 | string
============================ ====================

``texture_path`` is a path to a spherical image that is a skybox. It has a color value in all directions, so that when the camera is rotated, you can observe different parts of the image.
