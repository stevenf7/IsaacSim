

..
   Copyright (c) 2022-2026, NVIDIA CORPORATION. All rights reserved.
   NVIDIA CORPORATION and its licensors retain all intellectual property
   and proprietary rights in and to this software, related documentation
   and any modifications thereto. Any use, reproduction, disclosure or
   distribution of this software and related documentation without an express
   license agreement from NVIDIA CORPORATION is strictly prohibited.




.. _isaac_debug_draw:

===============================
Debug Drawing Extension API
===============================

.. _isaac_sim_debug_draw_about:

About
=================

This :ref:`isaac_debug_draw` API is used to coordinate groups of lines and points on the screen.
Use this API instead of Omniverse's built-in debug drawing API to have greater control over how the geometry is drawn.
The 3D geometry drawn by this remains persistent across frames and is only cleared when desired (unlike the built-in debug drawer).

.. _isaac_sim_debug_draw_api_doc:

API Documentation
=================

See the |link_ext| for complete usage information.

.. |link_ext| raw:: html

    <a href="../../py/docs/extsbuild/isaacsim.util.debug_draw/docs/index.html" target="_blank">API Documentation</a>

.. _isaac_sim_debug_draw_tutorials:

Tutorials & Examples
=====================

The following screenshots showcase how the different geometries are drawn:

Points
^^^^^^^^^^^

Drawing batches of points with different RGBA and radius values:

        .. literalinclude:: ../../snippets/utilities/debugging/ext_isaacsim_util_debug_draw/points.py
            :language: python

.. figure:: /images/isim_4.5_full_ext-isaacsim.util.debug_draw-2.0.0_viewport_points.png
    :align: center
    :alt: Draw Points

Lines
^^^^^^^^^^^

Drawing batches of lines with different RGBA and width values:

        .. literalinclude:: ../../snippets/utilities/debugging/ext_isaacsim_util_debug_draw/lines.py
            :language: python

.. figure:: /images/isim_4.5_full_ext-isaacsim.util.debug_draw-2.0.0_viewport_lines.png
    :align: center
    :alt: Draw Lines

Splines
^^^^^^^^^^^

Drawing splines as filled or dashed between a set of points:

        .. literalinclude:: ../../snippets/utilities/debugging/ext_isaacsim_util_debug_draw/splines.py
            :language: python

.. figure:: /images/isim_4.5_full_ext-isaacsim.util.debug_draw-2.0.0_viewport_splines.png
    :align: center
    :alt: Draw Splines
