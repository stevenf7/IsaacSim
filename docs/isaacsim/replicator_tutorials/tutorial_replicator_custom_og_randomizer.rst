..
   Copyright (c) 2024, NVIDIA CORPORATION. All rights reserved.
   NVIDIA CORPORATION and its licensors retain all intellectual property
   and proprietary rights in and to this software, related documentation
   and any modifications thereto. Any use, reproduction, disclosure or
   distribution of this software and related documentation without an express
   license agreement from NVIDIA CORPORATION is strictly prohibited.

.. _isaac_sim_app_tutorial_custom_og_randomizer:

.. _omnigraph-nodes: https://docs.omniverse.nvidia.com/kit/docs/omni.graph.docs/latest/dev/WritingNodes.html#omnigraph-nodes

======================================
Custom Replicator Randomization Nodes
======================================

This tutorial provides an example of how to create custom randomization nodes for the :doc:`omni.replicator<extensions:ext_replicator>` extension.

Learning Objectives
-------------------

The goal of this tutorial is to demonstrate how to create custom :doc:`OmniGraph <extensions:ext_omnigraph>` randomization nodes. These nodes can then be further integrated into the Synthetic Data Generation (SDG) pipeline graph of :doc:`Replicator <extensions:ext_replicator>`.

This tutorial will showcase how to:

* Create custom scene randomization Python scripts.
* Wrap the scripts as OmniGraph nodes and manually add them to an existing SDG pipeline graph.
* Encapsulate the OmniGraph nodes as **ReplicatorItems** to be automatically added to the SDG pipeline graph using Replicator's API.


Prerequisites
-------------

* Familiarity with USD / |isaac-sim_short| APIs for creating custom scene randomizers. See :ref:`isaac_sim_app_tutorial_replicator_isaac_randomizers` for more details.
* Familiarity with :doc:`omni.replicator <extensions:ext_replicator>` and its randomization API :doc:`replicator randomizers <extensions:ext_replicator/randomizer_details>`.
* Basic knowledge of :doc:`OmniGraph <extensions:ext_omnigraph>` and how to create `OmniGraph Nodes <omnigraph-nodes_>`_.
* Experience running simulations via the :ref:`Script Editor <script-editor>`.

Implementation
--------------

This tutorial will showcase how to create custom scene randomization Python scripts. These scripts will create prims in a new stage and randomize their rotation and locations: **in a sphere**, **on a sphere**, and **between two spheres**.

The following image shows the result after running the randomization in the Script Editor:

.. image:: /images/isim_4.5_replicator_tut_gui_custom_og_randomizer_python.jpg
    :width: 90%
    :align: center

.. tab-set::

    .. tab-item:: Code Explanation

        The following functions take as input the radius (or radii) of the spheres and generate a random 3D point on the surface of a sphere, within a sphere, and between two spheres. These points will determine the prim locations.

        .. raw:: html

            <details open>
            <summary>Randomization Functions</summary>

        .. code-block:: python

            # Generate a random 3D point on the surface of a sphere of a given radius.
            def random_point_on_sphere(radius):
                # Generate a random direction by spherical coordinates (phi, theta)
                phi = random.uniform(0, 2 * math.pi)
                # Sample costheta to ensure uniform distribution of points on the sphere (surface is proportional to sin(theta))
                costheta = random.uniform(-1, 1)
                theta = math.acos(costheta)

                # Convert from spherical to Cartesian coordinates
                x = radius * math.sin(theta) * math.cos(phi)
                y = radius * math.sin(theta) * math.sin(phi)
                z = radius * math.cos(theta)

                return x, y, z


            # Generate a random 3D point within a sphere of a given radius, ensuring a uniform distribution throughout the volume.
            def random_point_in_sphere(radius):
                # Generate a random direction by spherical coordinates (phi, theta)
                phi = random.uniform(0, 2 * math.pi)
                # Sample costheta to ensure uniform distribution of points on the sphere (surface is proportional to sin(theta))
                costheta = random.uniform(-1, 1)
                theta = math.acos(costheta)

                # Scale the radius uniformly within the sphere, applying the cube root to a random value
                # to account for volume's cubic growth with radius (r^3), ensuring spatial uniformity.
                r = radius * (random.random() ** (1 / 3))

                # Convert from spherical to Cartesian coordinates
                x = r * math.sin(theta) * math.cos(phi)
                y = r * math.sin(theta) * math.sin(phi)
                z = r * math.cos(theta)

                return x, y, z


            # Generate a random 3D point between two spheres, ensuring a uniform distribution throughout the volume.
            def random_point_between_spheres(radius1, radius2):
                # Ensure radius1 < radius2
                if radius1 > radius2:
                    radius1, radius2 = radius2, radius1

                # Generate a random direction by spherical coordinates (phi, theta)
                phi = random.uniform(0, 2 * math.pi)
                # Sample costheta to ensure uniform distribution of points on the sphere (surface is proportional to sin(theta))
                costheta = random.uniform(-1, 1)
                theta = math.acos(costheta)

                # Uniformly distribute points between two spheres by weighting the radius to match volume growth (r^3),
                # ensuring spatial uniformity by taking the cube root of a value between the radii cubed.
                r = (random.uniform(radius1**3, radius2**3)) ** (1 / 3.0)

                # Convert from spherical to Cartesian coordinates
                x = r * math.sin(theta) * math.cos(phi)
                y = r * math.sin(theta) * math.sin(phi)
                z = r * math.cos(theta)

                return x, y, z

        .. raw:: html

            </details>

        The following snippet creates prims in a new stage and randomizes their rotation and locations using the previously defined functions.

        .. raw:: html

            <details open>
            <summary>Spawning and Randomizing Prims</summary>

        .. code-block:: python

            stage = omni.usd.get_context().get_stage()
            prim_count = 500
            prim_scale = 0.1
            rad_in = 0.5
            rad_on = 1.5
            rad_bet1 = 2.5
            rad_bet2 = 3.5

            # Create the default prims
            on_sphere_prims = [stage.DefinePrim(f"/World/sphere_{i}", "Sphere") for i in range(prim_count)]
            in_sphere_prims = [stage.DefinePrim(f"/World/cube_{i}", "Cube") for i in range(prim_count)]
            between_spheres_prims = [stage.DefinePrim(f"/World/cylinder_{i}", "Cylinder") for i in range(prim_count)]

            # Add xformOps and scale to the prims
            for prim in chain(on_sphere_prims, in_sphere_prims, between_spheres_prims):
                if not prim.HasAttribute("xformOp:translate"):
                    UsdGeom.Xformable(prim).AddTranslateOp()
                if not prim.HasAttribute("xformOp:scale"):
                    UsdGeom.Xformable(prim).AddScaleOp()
                if not prim.HasAttribute("xformOp:rotateXYZ"):
                    UsdGeom.Xformable(prim).AddRotateXYZOp()
                prim.GetAttribute("xformOp:scale").Set((prim_scale, prim_scale, prim_scale))

            # Randomize the prims
            for _ in range(10):
                for in_sphere_prim in in_sphere_prims:
                    rand_rot = (random.uniform(0, 360), random.uniform(0, 360), random.uniform(0, 360))
                    in_sphere_prim.GetAttribute("xformOp:rotateXYZ").Set(rand_rot)
                    rand_loc = random_point_in_sphere(rad_in)
                    in_sphere_prim.GetAttribute("xformOp:translate").Set(rand_loc)

                for on_sphere_prim in on_sphere_prims:
                    rand_rot = (random.uniform(0, 360), random.uniform(0, 360), random.uniform(0, 360))
                    on_sphere_prim.GetAttribute("xformOp:rotateXYZ").Set(rand_rot)
                    rand_loc = random_point_on_sphere(rad_on)
                    on_sphere_prim.GetAttribute("xformOp:translate").Set(rand_loc)

                for between_spheres_prim in between_spheres_prims:
                    rand_rot = (random.uniform(0, 360), random.uniform(0, 360), random.uniform(0, 360))
                    between_spheres_prim.GetAttribute("xformOp:rotateXYZ").Set(rand_rot)
                    rand_loc = random_point_between_spheres(rad_bet1, rad_bet2)
                    between_spheres_prim.GetAttribute("xformOp:translate").Set(rand_loc)

        .. raw:: html

            </details>

    .. tab-item:: Script Editor

        Snippet to run in the Script Editor:

        .. raw:: html

            <details closed>
            <summary>Full Script Editor Script</summary>

        .. literalinclude:: ../snippets/replicator_tutorials/tutorial_replicator_custom_og_randomizer/custom_og_randomizer_script_editor.py
            :language: python
            :lines: 16-

        .. raw:: html

            </details>

As a next step, custom `OmniGraph Nodes <omnigraph-nodes_>`_ are created for the randomization functions. The node descriptions and implementations can be found in the following code snippets:

.. tab-set::

    .. tab-item:: Node Descriptions

        .. raw:: html

            <details open>
            <summary>OgnSampleInSphere.ogn</summary>

        .. literalinclude:: ../../../source/extensions/isaacsim.replicator.examples/python/nodes/OgnSampleInSphere.ogn
            :language: json

        .. raw:: html

            </details>

        .. raw:: html

            <details open>
            <summary>OgnSampleOnSphere.ogn</summary>

        .. literalinclude:: ../../../source/extensions/isaacsim.replicator.examples/python/nodes/OgnSampleOnSphere.ogn
            :language: json

        .. raw:: html

            </details>

        .. raw:: html

            <details open>
            <summary>OgnSampleBetweenSpheres.ogn</summary>

        .. literalinclude:: ../../../source/extensions/isaacsim.replicator.examples/python/nodes/OgnSampleBetweenSpheres.ogn
            :language: json

        .. raw:: html

            </details> 

    .. tab-item:: Node Implementations

        .. raw:: html

            <details open>
            <summary>OgnSampleInSphere.py</summary>

        .. literalinclude:: ../../../source/extensions/isaacsim.replicator.examples/python/nodes/OgnSampleInSphere.py
            :language: python

        .. raw:: html

            </details>

        .. raw:: html

            <details open>
            <summary>OgnSampleOnSphere.py</summary>

        .. literalinclude:: ../../../source/extensions/isaacsim.replicator.examples/python/nodes/OgnSampleOnSphere.py
            :language: python

        .. raw:: html

            </details>

            <details open>
            <summary>OgnSampleBetweenSpheres.py</summary>

        .. literalinclude:: ../../../source/extensions/isaacsim.replicator.examples/python/nodes/OgnSampleBetweenSpheres.py
            :language: python

        .. raw:: html

            </details> 

After this step, the randomizers will be available as nodes in the graph editor. For this tutorial the nodes are already added to the built-in ``isaacsim.replicator.examples`` extension and are available by default. Other custom nodes created through the OmniGraph tutorial will be accessible through the ``omni.new.extension`` extension (if the default tutorial-provided extension name was used). An example of accessing the nodes in an action graph is depicted below:

.. note::

    .. image:: /images/isim_4.5_replicator_tut_gui_custom_og_randomizer_extension.jpg
        :width: 80%
        :align: center
    
    If the custom nodes are not available, the newly created extension needs to be enabled. This can be done by navigating to **Window > Extensions > THIRD PARTY > ``omni.new.extension`` > ENABLED**:

.. image:: /images/isim_4.5_replicator_tut_gui_custom_og_randomizer_action_graph.jpg
    :width: 90%
    :align: center


After the OmniGraph randomization nodes are created, they can be manually added to a pre-existing SDG pipeline graph. To create a basic SDG graph, the following snippet can be used in the Script Editor to randomize the rotations of the created cubes every frame.

.. raw:: html

    <details open>
    <summary>Basic SDG Pipeline</summary>

.. code-block:: python

    import omni.replicator.core as rep

    cube = rep.create.cube(count=50, scale=0.1)
    with rep.trigger.on_frame():
        with cube:
            rep.randomizer.rotation()

.. raw:: html

    </details>

After the snippet is executed in the Script Editor, the generated graph can be opened at ``/Replicator/SDGPipeline`` and the custom nodes can be added to the graph. The following image shows the result after the custom nodes are added to the SDG pipeline graph together with the resulting randomization (from the UI using ``Tools`` > ``Replicator`` > ``Preview`` or ``Step``):

.. image:: /images/isim_4.5_replicator_tut_gui_custom_og_randomizer_pipeline.jpg
    :width: 90%
    :align: center

To avoid manually adding the custom nodes to the SDG pipeline graph, the Replicator API can be used to automatically insert the nodes into the graph. For this purpose, the nodes need to be encapsulated as **ReplicatorItems** using the ``@ReplicatorWrapper`` decorator. The following code snippet demonstrates how **ReplicatorItems** can be created for the custom nodes:

.. raw:: html

    <details open>
    <summary>ReplicatorWrapper</summary>

.. literalinclude:: ../snippets/replicator_tutorials/tutorial_replicator_custom_og_randomizer/replicator_wrapper.py
    :language: python

.. raw:: html

    </details>

.. note::

    For this tutorial the ``create_node`` function uses ``"isaacsim.replicator.examples.OgnSampleInSphere"`` as the node path, this path needs to be replaced in case the custom nodes are not part of the built-in ``isaacsim.replicator.examples`` extension.

After the snippet is executed in the Script Editor, the custom nodes will be automatically added to the SDG pipeline graph. To trigger the randomization, ``Tools`` > ``Replicator`` > ``Preview`` (or ``Step``) can be called from the UI. The following image shows the generated graph and the resulting randomization:

.. image:: /images/isim_4.5_replicator_tut_gui_custom_og_randomizer_replicator.jpg
    :width: 90%
    :align: center

