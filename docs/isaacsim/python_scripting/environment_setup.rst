..
   Copyright (c) 2022-2026, NVIDIA CORPORATION. All rights reserved.
   NVIDIA CORPORATION and its licensors retain all intellectual property
   and proprietary rights in and to this software, related documentation
   and any modifications thereto. Any use, reproduction, disclosure or
   distribution of this software and related documentation without an express
   license agreement from NVIDIA CORPORATION is strictly prohibited.





.. _isaac_environment_setup_how_to:

===============================
Scene Setup Snippets
===============================


Objects Creation and Manipulation
====================================

.. note:: The following scripts should only be run on the default new stage and only once. You can try these by creating a new stage via `File > New` and running  from `Window > Script Editor`

Rigid Object Creation
^^^^^^^^^^^^^^^^^^^^^
The following snippet adds a dynamic cube with given properties and a ground plane to the scene.

.. literalinclude:: ../snippets/python_scripting/environment_setup/rigid_object_creation.py
    :language: python

View Objects
^^^^^^^^^^^^^

`View` classes in this extension are collections of similar prims. View classes manipulate the underlying objects in a vectorized way.
Most View APIs require the world and the physics simulation to be initialized before they can be used.
This can be achieved by adding the view class to the `World`'s `scene` and resetting the world as follows

.. literalinclude:: ../snippets/python_scripting/environment_setup/view_objects.py
    :language: python

which works when running the script via the |isaac-sim_short| Python script. When using `Window > Script Editor`, to run the snippets you need to use the asynchronous version of ``reset`` as follows

.. literalinclude:: ../snippets/python_scripting/environment_setup/rigid_prim_is_now_initialized_and_can_be_used.py
    :language: python

See :ref:`isaac_sim_app_tutorial_intro_workflows` tutorial for more details about various workflows for developing in |isaac-sim_short|.

Create RigidPrim
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The following snippet adds three cubes to the scene and creates a `RigidPrim` (formerly `RigidPrimView`) to manipulate the batch.

.. literalinclude:: ../snippets/python_scripting/environment_setup/create_rigidprim.py
    :language: python

See the |link_RigidPrimView| for all the possible operations supported by ``RigidPrim``.

.. |link_RigidPrimView| raw:: html

    <a href="../py/source/extensions/isaacsim.core.prims/docs/index.html#isaacsim.core.prims.RigidPrim" target="_blank">API Documentation</a>


Create RigidContactView
^^^^^^^^^^^^^^^^^^^^^^^^

There are scenarios where you are interested in net contact forces on each body and contact forces between specific bodies. This can be achieved via the `RigidContactView` object managed by the `RigidPrim`

.. literalinclude:: ../snippets/python_scripting/environment_setup/create_rigidcontactview.py
    :language: python

More detailed information about the friction and contact forces can be obtained from the ``get_friction_data`` and ``get_contact_force_data`` respectively.
These APIs provide all the contact forces and contact points between pairs of the sensor prims and filter prims. ``get_contact_force_data`` API provides the contact distances and contact normal vectors as well.

In the example below, we add three boxes to the scene and apply a tangential force of magnitude 10 to each. Then we use the aforementioned APIs to receive all the contact information and sum across all the contact points to find the friction/normal forces between the boxes and the ground plane.


.. literalinclude:: ../snippets/python_scripting/environment_setup/contact_forces_between_the_top_and_the_bottom_boxe.py
    :language: python

See the |link_RigidContactView| for more information about ``RigidContactView``.

.. |link_RigidContactView| raw:: html

    <a href="../py/source/extensions/isaacsim.core.api/docs/index.html#isaacsim.core.api.RigidContactView" target="_blank">API Documentation</a>


.. _isaac_sim_python_snippet_set_mass_property:

Set Mass Properties for a Mesh
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
The snippet below shows how to set the mass of a physics object. Density can also be specified as an alternative

.. literalinclude:: ../snippets/python_scripting/environment_setup/set_mass_properties_for_a_mesh.py
    :language: python

Get Size of a Mesh
^^^^^^^^^^^^^^^^^^^^^^^
The snippet below shows how to get the size of a mesh.

.. literalinclude:: ../snippets/python_scripting/environment_setup/get_size_of_a_mesh.py
    :language: python

.. _apply-semantic-data-on-entire-stage:

Apply Semantic Data on Entire Stage
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The snippet below shows how to programmatically apply semantic data on objects by iterating the entire stage.

.. literalinclude:: ../snippets/python_scripting/environment_setup/apply_semantic_data_on_entire_stage.py
    :language: python

Convert Asset to USD
^^^^^^^^^^^^^^^^^^^^^^^

The below script will convert a non-USD asset like OBJ/STL/FBX to USD. This is meant to be used inside the :ref:`Script Editor <script-editor>`. For running it as a :ref:`Standalone Application <standalone-application>`, Check :ref:`isaac_sim_python_environment`.

.. literalinclude:: ../snippets/python_scripting/environment_setup/convert_asset_to_usd.py
    :language: python

The details about the optional import options in lines 13-23 can be found :doc:`here <extensions:ext_asset-converter>`.


Physics How-Tos
====================================

.. _isaac_sim_python_snippet_create_physics_scene:

Create A Physics Scene
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. literalinclude:: ../snippets/python_scripting/environment_setup/create_a_physics_scene.py
    :language: python

The following can be added to set specific settings, in this case use CPU physics and the TGS solver

.. literalinclude:: ../snippets/python_scripting/environment_setup/set_gravity_vector.py
    :language: python
    :start-after: # -- End test setup --

Adding a ground plane to a stage can be done via the following code:
It creates a Z up plane with a size of 100 cm at a Z coordinate of -100

.. literalinclude:: ../snippets/python_scripting/environment_setup/set_gravity_vector_1.py
    :language: python

.. _isaac_sim_python_snippet_enable_physics_collision:

Enable Physics And Collision For a Mesh
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
The script below assumes there is a physics scene in the stage.

.. literalinclude:: ../snippets/python_scripting/environment_setup/enable_physics_and_collision_for_a_mesh.py
    :language: python

If a tighter collision approximation is desired use convexDecomposition

.. literalinclude:: ../snippets/python_scripting/environment_setup/if_a_tighter_collision_approximation_is_desired_us.py
    :language: python

To verify that collision meshes have been successfully enabled, click the "eye" icon > "Show By Type" >
"Physics Mesh" > "All". This will show the collision meshes as pink outlines on the objects.



Traverse a stage and assign collision meshes to children
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.. literalinclude:: ../snippets/python_scripting/environment_setup/traverse_a_stage_and_assign_collision_meshes_to_ch.py
    :language: python

Do Overlap Test
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

These snippets detect and report when objects overlap with a specified cubic/spherical region.
The following is assumed: the stage contains a physics scene, all objects have collision meshes enabled,
and the play button has been clicked.

The parameters: extent, origin and rotation (or origin and radius) define the cubic/spherical region to check overlap against.
The output of the physX query is the number of objects that overlaps with this cubic/spherical region.

.. literalinclude:: ../snippets/python_scripting/environment_setup/do_overlap_test.py
    :language: python

Do Raycast Test
^^^^^^^^^^^^^^^^^^^^^^^^

This snippet detects the closest object that intersects with a specified ray.
The following is assumed: the stage contains a physics scene, all objects have collision meshes enabled,
and the play button has been clicked.

The parameters: origin, rayDir and distance define a ray along which a ray hit might be detected.
The output of the query can be used to access the object's reference, and its distance from the raycast origin.

.. literalinclude:: ../snippets/python_scripting/environment_setup/do_raycast_test.py
    :language: python

USD How-Tos
====================================

Creating, Modifying, Assigning Materials
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. literalinclude:: ../snippets/python_scripting/environment_setup/creating_modifying_assigning_materials.py
    :language: python

Assigning a texture to a material that supports it can be done as follows:

.. literalinclude:: ../snippets/python_scripting/environment_setup/bind_the_material_to_the_prim.py
    :language: python

Adding a transform matrix to a prim
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. literalinclude:: ../snippets/python_scripting/environment_setup/adding_a_transform_matrix_to_a_prim.py
    :language: python
    :start-after: # -- End test setup --

Align two USD prims
^^^^^^^^^^^^^^^^^^^^^^^^

.. literalinclude:: ../snippets/python_scripting/environment_setup/align_two_usd_prims.py
    :language: python

Get World Transform At Current Timestamp For Selected Prims
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.. literalinclude:: ../snippets/python_scripting/environment_setup/get_world_transform_at_current_timestamp_for_selec.py
    :language: python

Save current stage to USD
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

This can be useful if generating a stage in Python and you want to store it to reload later to debugging

.. literalinclude:: ../snippets/python_scripting/environment_setup/save_current_stage_to_usd.py
    :language: python