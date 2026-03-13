..
   Copyright (c) 2022-2026, NVIDIA CORPORATION. All rights reserved.
   NVIDIA CORPORATION and its licensors retain all intellectual property
   and proprietary rights in and to this software, related documentation
   and any modifications thereto. Any use, reproduction, disclosure or
   distribution of this software and related documentation without an express
   license agreement from NVIDIA CORPORATION is strictly prohibited.


.. _isaac_sim_app_util_snippets:

==========================================
Util Snippets
==========================================


Simple Async Task
-----------------
.. literalinclude:: ../snippets/python_scripting/util_snippets/simple_async_task.py
    :language: python

Get Camera Parameters
-----------------------

The below script show how to get the camera parameters associated with a viewport.

.. literalinclude:: ../snippets/python_scripting/util_snippets/get_camera_parameters.py
    :language: python

Rendering
-------------

There are three primary APIs you should use when making frequent updates to large amounts of geometry: ``UsdGeom.Points``,
``UsdGeom.PointInstancer``, and ``DebugDraw``. The different advantages and limitations of each of these methods are explained
below, and can help guide you on which method to use.

UsdGeom.Points
###############
Use the ``UsdGeom.Points`` API when the geometry needs to interact with the renderer.
The ``UsdGeom.Points`` API is the most efficient method to render large amounts of point geometry.

    .. literalinclude:: ../snippets/python_scripting/util_snippets/usdgeompoints.py
        :language: python

.. figure:: /images/isim_4.5_full_ref_viewport_util_snippet_points.png
    :align: center
    :alt: Output when using UsdGeom.Points

UsdGeom.PointInstancer
#######################

Use the ``UsdGeom.PointInstancer`` API when the geometry needs to interact with the physics scene.
The ``UsdGeom.PointInstancer`` API lets you efficiently replicate an instance of a prim — with all of its USD properties —
and update all instances with a list of positions, colors, and sizes.

See the `PointInstancer Reference <https://openusd.org/release/api/class_usd_geom_point_instancer.html>`_ for more information regarding the PointInstancer API.

Below are code snippets for how to create and update geometry with ``UsdGeom.PointInstancer``:

    .. literalinclude:: ../snippets/python_scripting/util_snippets/usdgeompointinstancer.py
        :language: python

.. figure:: /images/isim_4.5_full_ref_viewport_util_snippet_point_instancer.png
    :align: center
    :alt: Output when using UsdGeom.PointInstancer

DebugDraw
##########

The :ref:`isaac_debug_draw` API is useful for purely visualizing geometry in the Viewport. Geometry drawn with the ``debug_draw_interface``
cannot be rendered and does not interact with the physics scene. However, it is the most performance-efficient method of visualizing geometry.

 See the `API documentation <../py/docs/extsbuild/isaacsim.util.debug_draw/docs/index.html>`__ for complete usage information.

Below are code snippets for how to create and update geometry visualed with ``DebugDraw``:

    .. literalinclude:: ../snippets/python_scripting/util_snippets/debugdraw.py
        :language: python

.. figure:: /images/isim_4.5_full_ref_viewport_util_snippet_debug_draw.png
    :align: center
    :alt: Output when using isaacsim.util.debug_draw

Rendering Frame Delay
##############################

The default rendering pipeline in the app experiences have upto 3 frames in flight to be rendered, which results in higher FPS since the simulation is not blocked until the latest state is rendered completely.

For applications that need the rendered data to correspond to the latest simulation state with no delay, the following experience file should be used ``apps/omni.isaac.sim.zero_delay.python.kit``. Below is an example of how to use the experience file in a standlone workflow.

.. literalinclude:: ../snippets/python_scripting/util_snippets/rendering_frame_delay.py
    :language: python

Alternatively, if you would like to use the specific settings instead, you can set them with `extra_args` as well:

.. literalinclude:: ../snippets/python_scripting/util_snippets/rendering_frame_delay_1.py
    :language: python