..
   Copyright (c) 2022-2026, NVIDIA CORPORATION. All rights reserved.
   NVIDIA CORPORATION and its licensors retain all intellectual property
   and proprietary rights in and to this software, related documentation
   and any modifications thereto. Any use, reproduction, disclosure or
   distribution of this software and related documentation without an express
   license agreement from NVIDIA CORPORATION is strictly prohibited.




.. _isaac_sim_app_tutorial_instanceable_assets:

===============================
Instanceable Assets
===============================

Reinforcement learning often requires training in large simulation scenes with multiple clones of the same robots. As we add more and more robots into the simulation environment, the memory consumption also increases for each additional set of robot and mesh assets added. To reduce memory consumption, we can take advantage of USD's `Scenegraph Instancing <https://graphics.pixar.com/usd/dev/api/_usd__page__scenegraph_instancing.html>`_ functionality to mark common meshes shared by different copies of the same robots as `instanceable`.

By doing so, each copy of the robot will reference a single copy of meshes, avoiding the need to create multiple copies of the same meshes in the scene, thus reducing memory usage in the overall simulation environment.

Learning Objectives
===================

In this tutorial, we will show how to create instanceable assets in Isaac Sim. We will

1. Explain requirements for making assets instanceable
2. Use the URDF and MJCF importers to create instanceable assets
3. Show utility methods to convert existing assets to instanceable assets

*10-15 Minute Tutorial*


Getting Started
===============

* Please refer to USD Documentation on `Scenegraph Instancing <https://graphics.pixar.com/usd/dev/api/_usd__page__scenegraph_instancing.html>`_ for more details on instancing.
* Please refer to :ref:`isaac_sim_app_tutorial_advanced_import_urdf` and :ref:`isaac_sim_app_tutorial_advanced_import_mjcf` for more details on importer functionalities.


Hierarchy Requirement for Instanceable Assets
=============================================

USD prohibits modifying properties of prims on descendants of instanced prims. Therefore, we generally only perform instancing on mesh prims for robot assets, since properties on meshes will not differ across different environments during simulation. However, the transforms of the meshes may be different during simulation when robots in each environment are being moved in varying ways. Thus, we have to define the topology of our robot hierarchy in a specific structure in the asset tree definition in order for the instanceable flag to take action.

To mark any mesh or primitive geometry prim in the asset as instanceable, the mesh prim requires a parent Xform prim to be present, which will be used to add a reference to a master USD file containing definition of the mesh prim.

For example, the following definition cannot be marked instanceable:

.. code-block:: none

    World
      |_ Robot
           |_ Collisions
                   |_ Sphere
                   |_ Box


Instead, it will have to be modified to:

.. code-block:: none

    World
      |_ Robot
           |_ Collisions
                   |_ Sphere_Xform
                   |      |_ Sphere
                   |_ Box_Xform
                          |_ Box


Any references that exist on the original `Sphere` and `Box` prims would have to be moved to `Sphere_Xform` and `Box_Xform` prims.


Using URDF and MJCF Importers
=============================

Isaac Sim provides two importers - URDF and MJCF - for converting robot assets to USD format to be used in Isaac Sim. Both importers support the option to import robot assets directly as instanceable assets. By selecting this option, imported assets will be split into two separate USD files that follow the above hierarchy definition. Any mesh data will be written to an USD stage to be referenced by the main USD stage, which contains the main robot definition.

To use the Instanceable option in the importers, first check the `Create Instanceable Asset` option. Then, specify a file path to indicate the location for saving the mesh data in the `Instanceable USD Path` textbox. This will default to `./instanceable_meshes.usd`, which will generate a file `instanceable_meshes.usd` that is saved to the current directory.

Once the asset is imported with these options enabled, you will see the robot definition in the stage - we will refer to this stage as the master stage. If we expand the robot hierarchy in the Stage, we will notice that the parent prims that have mesh descendants have been marked as Instanceable and they reference a prim in our `Instanceable USD Path` USD file. We are also no longer able to modify attributes of descendant meshes.

To add our instanced asset into a new stage, we will simply need to add our master USD file.


Modifying Existing Assets
=========================

Due to limitations of the topology requirement for making assets instanceable, it is not as straightforward to convert existing non-instanceable assets to become instanceable. Here, we will try to provide a few small utility methods to help make the process simpler.

All utilities should be copied into and run from the script editor, which can be opened from `Window > Script Editor`.

First, we need to make sure our existing asset follows the hierarchy constraint defined above, where all mesh prims have a parent XForm prim present that can be used to mark the prim as instanceable. To help with the process of creating new parent prims, we provide a utility method `create_parent_xforms()` below to automatically insert a new Xform prim as a parent of every mesh prim in the stage.


.. literalinclude:: ../snippets/isaac_lab_tutorials/tutorial_instanceable_assets/modifying_existing_assets.py
    :language: python

This method can be run on an existing non-instanced USD file for an asset from the script editor, where:

* `asset_usd_path` is the file path to the current existing USD asset
* `source_prim_path` is the USD prim path to the root prim of the asset
* `save_as_path` is a different file path to same the modified asset to. This can be left unspecified to overwrite the existing file.

.. literalinclude:: ../snippets/isaac_lab_tutorials/tutorial_instanceable_assets/save_as_path_str_usd_file_path_for_modified_usd_st.py
    :language: python

It is worth noting that any `USD Relationships <https://graphics.pixar.com/usd/dev/api/class_usd_relationship.html>`_ on the referenced meshes will be removed. This is because those USD Relationships originally have targets set to prims in the original prim that may no longer be valid and hence cannot be accessed from the new stage. Common examples of USD Relationships that could exist on the meshes are visual materials, physics materials, and filtered collision pairs. Therefore, it is recommended to set these USD Relationships on the meshes' parent Xforms instead of the meshes themselves.

The above method can also be run as part of an overall conversion process, which is defined in the utility below. This utility will first insert new parent prims if `create_xforms=True` is specified, and generate a new USD file that is used for referencing. It will then traverse through the asset tree and mark the parent prim of any mesh or primitive type prims as instanceable, along with inserting a reference to the mesh USD stage.

.. literalinclude:: ../snippets/isaac_lab_tutorials/tutorial_instanceable_assets/save_as_path_str_usd_file_path_for_modified_usd_st.py
    :language: python

Summary
=======

This tutorial covered the following topics:

1. Requirements for creating instanceable assets
2. Using the URDF and MJCF Importers to create instanceable assets
3. Making existing assets instanceable
