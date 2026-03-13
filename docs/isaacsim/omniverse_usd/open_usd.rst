
.. meta::
  :title: OpenUSD Fundamentals
  :keywords: lang=en A quick introduction on USD for Roboticists


.. _openUSD_Fundamentals:

======================
OpenUSD Fundamentals
======================

The language used in |isaac-sim_short| to describe the robot and its environment is the `Universal Scene Description (USD) <https://openusd.org/release/index.html>`_.


Why USD?
=========

USD enables seamless interchange of 3D content among diverse content creation apps with its rich, extensible language. With concepts of layering and variants, it's a powerful tool that enables live collaboration on the same asset and scene. And when properly used, it permits working on assets without overwriting and erasing someone else's work.

USD provides a text-based format for direct editing (*.usda). For higher performance and space optimization, there is a binary-encoded format (*.usd). All aspects of USD can be accessed through coding in C++ or Python.

APIs are available for you to set up a scene or tune a robot directly in USD, but, typically it is not necessary to use them.


Hello World
==============

Let's start by creating a basic USD file from code:


.. literalinclude:: ../snippets/omniverse_usd/open_usd/hello_world.py
    :language: python

Replacing :code:`/path/to/` with the desired save folder. You can execute this code in the script editor (**Window > Script Editor**) in |isaac-sim_short|, and it yields the following USD file:

.. code-block:: USD

    #usda 1.0

    def Xform "hello"
    {
        def Sphere "world"
        {
        }
    }

This example contains a couple of powerful things we can take away from it:

* **Type**: Elements in USD (called *Prims*) have a defined type. In the case of :code:`hello`, it is of type :code:`Xform`, a type used everywhere, and it defines elements that contain a transform in the world. :code:`World` is of type *Sphere*, which represents a primitive geometry.
* **Composition**: Prims can have *nested prims*. These nested prims are, for all effects, fully defined elements, with their own attributes.
* **Introspection**: If uncommented, the line :code:`generic_spherePrim = stage.DefinePrim('/hello/world_generic', 'Sphere')` would yield a sphere just like the :code:`/hello/world`. Prim types can be defined directly through their schema name.
* **Namespaces**: Both *Xform* and *Sphere* are part of the standard pxr namespace *UsdGeom*, a set of types that represent geometry elements in the scene.


You can open this USD file in |isaac-sim_short| in the script editor window with:

.. literalinclude:: ../snippets/omniverse_usd/open_usd/usda_10.py
    :language: python

.. image:: /images/isim_4.0_full_ref_gui_usd_0.png
    :width: 900

Inspecting and Authoring Properties
------------------------------------

With a basic scene, you can start making modifications to the elements. Start by opening and getting the elements from the scene:

.. literalinclude:: ../snippets/omniverse_usd/open_usd/inspecting_and_authoring_properties.py
    :language: python

The output for the code above is:

.. code-block:: bash

    ['proxyPrim', 'purpose', 'visibility', 'xformOpOrder']
    ['doubleSided', 'extent', 'orientation', 'primvars:displayColor' 'primvars:displayOpacity', 'proxyPrim', 'purpose', 'radius', 'visibility', 'xformOpOrder']

USD offers polymorphism. If you review both lists you can see the common attributes. By having a common :code:`XFormable` ancestor, Xforms and Spheres share a subset of properties, while sphere contains some unique elements that only make sense for its specialization (for example, *radius*).

To update these attributes, you can append the following to the code above:

.. literalinclude:: ../snippets/omniverse_usd/open_usd/inspecting_and_authoring_properties_1.py
    :language: python

Because the stage was still open from the previous sample, you'll see the sphere reducing from radius 1.0 to 0.5, but it also prints these values in the console.

.. image:: /images/isim_4.0_full_ref_gui_usd_1.png
    :width: 900

To move the sphere to a new position use :code:`xformOpOrder`, which is common to :code:`Xform` and :code:`Sphere`. Many different transforms can be applied to a prim, each from potentially different layers. The :code:`xformOpOrder` tracks and manages the different transforms, it is like a list of :code:`Xform` operations, applied in the order specified from first to last.

Our sphere doesn't have its own, so to create a new one:

.. literalinclude:: ../snippets/omniverse_usd/open_usd/inspecting_and_authoring_properties_2.py
    :language: python

Notice that the sphere has jumped to a new position along the X-axis. Alternatively, you could apply the translation to the parent :code:`xform` instead.

.. literalinclude:: ../snippets/omniverse_usd/open_usd/inspecting_and_authoring_properties_3.py
    :language: python

Verify that you see the sphere jump to a new location, which is the composition of both the parent and child transforms.

A consequence of the universal nature of USD is that when you fetch a prim by path, it is always of type :code:`prim` and needs to be cast appropriately before performing operations with or on it.

To create and bind a material to the prim to change its color, first create it:

.. literalinclude:: ../snippets/omniverse_usd/open_usd/inspecting_and_authoring_properties_4.py
    :language: python

Material color shading is complicated. After creating the prim and appropriate attributes, you must link those attributes and properties together to form a ``shader graph`` that is processed to produce the desired material effect.  After it's created, the material can then be bound to the prim, thus changing its apparent color in the viewport.

.. literalinclude:: ../snippets/omniverse_usd/open_usd/connect_up_the_shader_graph.py
    :language: python

.. image:: /images/isim_4.0_full_ref_gui_usd_2.png
    :width: 900

If you save the stage and examine the USDA file, you can see the material.

.. code-block:: USD

    #usda 1.0

    def Material "material"
    {
        token outputs:mdl:displacement.connect = </hello/material/Shader.outputs:out>
        token outputs:mdl:surface.connect = </hello/material/Shader.outputs:out>
        token outputs:mdl:volume.connect = </hello/material/Shader.outputs:out>

        def Shader "Shader"
        {
            uniform token info:implementationSource = "sourceAsset"
            uniform asset info:mdl:sourceAsset = @OmniPBR.mdl@
            uniform token info:mdl:sourceAsset:subIdentifier = "OmniPBR"
            color3f inputs:diffuse_color_constant = (1, 0, 0) (
                customData = {
                    float3 default = (0.2, 0.2, 0.2)
                }
                displayGroup = "Albedo"
                displayName = "Albedo Color"
                doc = "This is the albedo base color"
                hidden = false
                renderType = "color"
            )
            color3f inputs:emissive_color = (1, 0, 0) (
                customData = {
                    float3 default = (1, 0.1, 0.1)
                }
                displayGroup = "Emissive"
                displayName = "Emissive Color"
                doc = "The emission color"
                hidden = false
                renderType = "color"
            )
            token outputs:out
        }
    }

and specifically, the ``diffuse_color_constant`` attribute type.  To directly modify this attribute to change the color of our sphere:

.. literalinclude:: ../snippets/omniverse_usd/open_usd/usda_10_1.py
    :language: python

Of course, this level of direct manipulation of USD can become tedious. For situations like this, there are a set of predefined commands through the kit API, which dramatically simplifies working with USD in code.  For example, you could have done the following instead:

.. literalinclude:: ../snippets/omniverse_usd/open_usd/usda_10_2.py
    :language: python

Further Reading
==================

For a complete tutorial on USD, see the `openUSD tutorials <https://openusd.org/release/tut_usd_tutorials.html>`_. With a few tweaks, as shown on the basic examples above, these tutorials can be run from the Script editor or in the :ref:`Isaac Python shell <isaac_sim_python_environment>`.

For more in-depth content, see `guided learning <https://docs.omniverse.nvidia.com/usd/latest/learn-openusd/guided-learning.html#openusd-guided-learning>`_ content or the `independent learning <https://docs.omniverse.nvidia.com/usd/latest/learn-openusd/independent-learning.html>`_.


Units in USD
=============

By default, |isaac-sim_short| USD uses the following default units:

============== ==============
Unit           Default
============== ==============
Distance       meters (m)
Time           seconds (s)
Mass           Kilogram (kg)
Angle          Degrees
============== ==============

For more |isaac-sim_short| conventions, see :ref:`isaac_sim_conventions`.


There are cases when assets coming from different apps follow a different standard. By default, |isaac-sim_short| has enabled the :doc:`Metrics Assembler <extensions:ext_metrics_assembler>`, which automatically converts the asset scale for the distance unit, mass unit, and Up Axis.

For more details about how USD handles units, see `Units in USD <https://docs.omniverse.nvidia.com/usd/latest/learn-openusd/independent/units.html>`_.


Useful USD Snippets
=====================

Here are some useful snippets that can be useful when dealing with USD in code. These snippets assume that :code:`stage` and :code:`prim`: are respectively pxr.UsdStage and pxr.UsdPrim types, and if any additional type is used, the necessary imports are included in the snippet.

Traversing Stage or Prim
--------------------------

.. literalinclude:: ../snippets/omniverse_usd/open_usd/traversing_stage_or_prim.py
    :language: python

Working with Multiple Layers
-----------------------------


.. literalinclude:: ../snippets/omniverse_usd/open_usd/working_with_multiple_layers.py
    :language: python

Converting Transform Pose in Position, Orient, Scale
----------------------------------------------------------------

.. note:: You can use this to create a `set_pose` method that receives a transform and applies to the prim.


.. literalinclude:: ../snippets/omniverse_usd/open_usd/converting_transform_pose_in_position_orient_scale.py
    :language: python