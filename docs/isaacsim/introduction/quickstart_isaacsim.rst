..
   Copyright (c) 2022-2026, NVIDIA CORPORATION. All rights reserved.
   NVIDIA CORPORATION and its licensors retain all intellectual property
   and proprietary rights in and to this software, related documentation
   and any modifications thereto. Any use, reproduction, disclosure or
   distribution of this software and related documentation without an express
   license agreement from NVIDIA CORPORATION is strictly prohibited.


.. _isaac_sim_app_intro_quickstart:


==========================================
|isaac-sim_short| Basic Usage Tutorial
==========================================

This tutorial covers the basics of |isaac-sim_short|, including navigating the GUI, adding objects to the stage, looking up basic properties of objects, and running simulations.

In this tutorial, you will go from a blank stage to a moving robot using your choice of three different workflows. The purpose of including the three different workflows is to illustrate that |isaac-sim_short| can be used in different ways depending on your needs.

You can review the scripts in both workflows to see how they differ. Comparing and contrasting can help you understand how to perform the exact same tasks:

* The **extension script** can be found in **Window > Examples > Robotics Examples**, then click on **Open Script** on the right upper corner of the browser. 

* The **standalone script** can be found in the ``<isaac-sim-root-dir>/standalone_examples/tutorials/`` folder. 

You can try the "hot-reloading" feature out by editing any of the scripts in the Extension examples. Save the file and see the changes reflected immediately without shutting down the simulator.

For a description of workflow concepts, see :ref:`Workflows <isaac_sim_app_tutorial_intro_workflows>`.





Tutorial
=======================

There are three tabs for this tutorial, all three perform the same actions and reach the same outcome. Go through the full page under the same tab to learn about each workflow. Toggle between tabs to compare the different workflows or to perform the tutorial steps for your environment. 

* GUI 
* Extensions
* Standalone Python



.. tab-set::
   .. tab-item:: GUI

      .. rubric:: Launch

      1. Launch |isaac-sim_short| from installation root folder.

         .. tab-set::
            .. tab-item:: Linux

               .. code-block:: bash

                     cd ~/isaacsim
                     ./isaac-sim.sh

            .. tab-item:: Windows

               .. code-block:: bat

                     cd C:\isaacsim
                     isaac-sim.bat

         After the simulator is fully loaded, create a new scene:
      
      2. From the top Menu Bar, click **File > New**. The first time you launch |isaac-sim_short|, it may take a five - ten minutes to complete.


      .. rubric::  Add a Ground Plane

      Add a ground plane to the scene:
      
      1. From the top Menu Bar, click **Create > Physics > Ground Plane**.

      .. rubric::  Add a Light Source

      You can add a light source to the scene to illuminate the objects in the scene. If you have a light source in the scene, but no object to reflect the light, the scene will still be dark.

      Add a Distant Light source to the scene:
      
      1. From the top Menu Bar, click **Create > Lights > Distant Light**.



      .. rubric::  Add a Visual Cube

      A "visual" cube is a cube with no physics properties attached, for example, no mass, no collision. This cube will not fall under gravity or collide with other objects. 


      Add a cube to the scene:
      
      1. From the top Menu Bar, click **Create > Shape > Cube**.

      2. From the far left side of the UI locate the arrow icon and press **Play**.  The cube does not do anything when simulation is running.


      .. image:: /images/isim_4.5_base_tut_gui_add_cube.webp
         :align: center



      .. rubric::  Move, Rotate, and Scale the Cube

      Use the various gizmos on the left hand side toolbar to manipulate the cube.

      #. Press "W" or click on the Move Gizmo to drag and move the cube. You can move it in only one axis by clicking on the arrows and drag, in two axes by clicking on the colored squares and drag, or in all three axes by clicking on the dot in the center of the gizmo and drag.
      #. Press "E" or click on the Rotate Gizmo to rotate the cube.
      #. Press "R" or click on the Scale Gizmo to scale the cube. You can scale it in one dimension by clicking on the the arrows and drag, two dimensions by clicking on the colored squares and drag, or in all three dimensions by clicking on the circle in the center of the gizmo and drag.
      #. Press "esc" to deselect the cube.

      For "Move" and "Rotate", you can  indicate if you are maneuvering in local or world coordinates. Click and hold on the gizmos to see the options.

      You can make more precise modifications to the cube through its  **Property** panel by typing in the exact numbers in the corresponding boxes. Click on the blue square next to the boxes to reset the values to default.


      .. image:: /images/isim_4.5_base_tut_gui_move_cube.webp
         :align: center


      .. rubric::  Add Physics and Collision Properties

      Common physics properties are mass and inertia matrix, which are the properties that allow the object to fall under gravity. Collision Properties are the properties that allow the object to collide with other objects.

      Physics and collision properties can be added separately, so you can have an object that collides with other objects but does not fall under gravity, or falls under gravity but does not collide with other objects. But in many cases, they are added together.

      To add physics and collision properties to the cube:

      1. Find the object ("/World/Cube") on the stage tree and highlight it.
      2. From the **Property** panel on the bottom right of the Workspace, click on the **Add** button and select **Physics** on the dropdown menu. This will show a list of properties that can be added to the object.
      #. Select **Rigid Body with Colliders Preset** to add both physics and collision meshes to the object.
      #. Press the **Play** button to see the cube fall under gravity and collide with the ground plane.

      .. image:: /images/isim_4.5_base_tut_gui_physics_property.webp
         :align: center

      




   .. tab-item:: Extension


      .. rubric:: Launch

      We will demonstrate the property of an Extension workflow using an existing Extension module called the "Script Editor". The Script Editor allows the users to interact with the stage using Python. You will see that we will be mostly using the same Python APIs as in the Standalone Python workflow. The difference between the two workflows will become clear when we start to interact with the simulation timeline, especially in the :ref:`next tutorial <isaac_sim_app_intro_quickstart_robot>`.

      Launch a fresh instance of |isaac-sim_short|, go the top Menu Bar and click **Window > Script Editor**.
      The code snippets in this tab are sections from one runnable script and should be executed in order.


      .. rubric::  Add a Ground Plane

      To add a ground plane using the interactive Python, copy paste the following snippet in the Script Editor and run it by clicking the **Run** button on the bottom.


      .. literalinclude:: ../snippets/introduction/quickstart_isaacsim/extension_workflow.py
          :language: python
          :start-after: # -- Add a ground plane --
          :end-before: # -- End add a ground plane --

      .. rubric::  Add a Light Source

      You can add a light source to the scene to illuminate the objects in the scene. If you have a light source in the scene, but no object to reflect the light, the scene will still be dark.

      1. Open a new tab in the Script Editor (**Tab > Add Tab**). 
      2. Add a light source by copy-pasting the following snippet in the Script Editor and running it.


      .. literalinclude:: ../snippets/introduction/quickstart_isaacsim/extension_workflow.py
          :language: python
          :start-after: # -- Add a light source --
          :end-before: # -- End add a light source --

      .. rubric::  Add a Visual Cube

      A "visual" cube is a cube with no physics properties attached. No mass, no collision. This cube will not fall under gravity or collide with other objects. You can press **Play** to see that the cube does not do anything when the simulation is running.



      1. Open a new tab in the Script Editor (**Tab > Add Tab**). 
      2. Add two cubes by copy-pasting the following snippet in the Script Editor and run it. We'll keep one as visual-only, and add physics and collision properties to the other for comparison.

      .. literalinclude:: ../snippets/introduction/quickstart_isaacsim/extension_workflow.py
          :language: python
          :start-after: # -- Add visual cubes with the Core API --
          :end-before: # -- End add visual cubes with the Core API --

      Isaac Sim Core API are wrappers for raw USD and physics engine APIs. You can add a visual cube (without physics and color properties) using raw USD API. Notice that the raw USD API is more verbose, but gives you more control over each property.

      .. literalinclude:: ../snippets/introduction/quickstart_isaacsim/extension_workflow.py
          :language: python
          :start-after: # -- Add a visual cube with the raw USD API --
          :end-before: # -- End add a visual cube with the raw USD API --

      .. rubric::  Add Physics and Collision Properties

      Common physics properties are mass and inertia matrix, which are the properties that allow the object to fall under gravity. Collision Properties are the properties that allow the object to collide with other objects.

      Physics and collision properties can be added separately, so that you can have an object that collides with other objects but does not fall under gravity, or falls under gravity but does not collide with other objects. But in many cases, they are added together.

      With the core APIs, you can add a new cube with physics and collision by creating a cube and then applying rigid body and collision APIs.

      .. literalinclude:: ../snippets/introduction/quickstart_isaacsim/extension_workflow.py
          :language: python
          :start-after: # -- Add physics and collision to a new cube --
          :end-before: # -- End add physics and collision to a new cube --

      Alternatively, if you want to modify an existing object to have physics and collision properties, you can use the following snippet.

      .. literalinclude:: ../snippets/introduction/quickstart_isaacsim/extension_workflow.py
          :language: python
          :start-after: # -- Add physics and collision to an existing cube --
          :end-before: # -- End add physics and collision to an existing cube --

      Click the **Play** button to see the cubes fall under gravity and collide with the ground plane.

      .. rubric::  Move, Rotate, and Scale the Cube

      Moving an object using core API:

      .. literalinclude:: ../snippets/introduction/quickstart_isaacsim/extension_workflow.py
          :language: python
          :start-after: # -- Move an object with the Core API --
          :end-before: # -- End move an object with the Core API --

      Moving an object using raw USD API:

      .. literalinclude:: ../snippets/introduction/quickstart_isaacsim/extension_workflow.py
          :language: python
          :start-after: # -- Move an object with the raw USD API --
          :end-before: # -- End move an object with the raw USD API --

   .. tab-item:: Standalone Python

      .. rubric:: Launch

      The script that runs Part I, :ref:`isaac_sim_app_intro_quickstart`, is located in  ``standalone_examples/tutorials/getting_started/getting_started.py``.

      To run the script, open a terminal, navigate to the root of the Isaac Sim installation, and run the following command:

      .. tab-set::
         .. tab-item:: Linux

            .. code-block:: bash

               ./python.sh standalone_examples/tutorials/getting_started/getting_started.py

         .. tab-item:: Windows

            .. code-block:: bash

               python.bat standalone_examples\tutorials\getting_started\getting_started.py



      .. rubric:: Code Explained


      **Add a Ground Plane**


      The lines inside ``getting_started.py`` that are relevant to adding a ground plane to the scene are below. 

      .. literalinclude:: ../snippets/introduction/quickstart_isaacsim/ground_plane_standalone.py
          :language: python

      **Add a Light Source**

      You can add a light source to the scene to illuminate the objects in the scene. If you have a light source in the scene, but no object to reflect the light, the scene will still be dark.

      The lines inside ``getting_started.py`` that add a Distant Light are:

      .. literalinclude:: ../snippets/introduction/quickstart_isaacsim/light_source.py
          :language: python

      **Add a Visual Cube**

      A "visual" cube is a cube with no physics properties attached. No mass, no collision. This cube will not fall under gravity or collide with other objects. You can press **Play** to see that the cube does not do anything when the simulation is running.

      The lines inside ``getting_started.py`` that add a visual cube to the scene are:

      .. literalinclude:: ../snippets/introduction/quickstart_isaacsim/single_visual_cube.py
          :language: python

      **Add Physics and Collision Properties**

      Common physics properties are mass and inertia matrix, which are the properties that allow the object to fall under gravity. Collision properties are the properties that allow the object to collide with other objects.

      Physics and collision properties can be added separately, so you can have an object that collides with other objects but does not fall under gravity, or falls under gravity but does not collide with other objects. But in many cases, they are added together.

      With the experimental APIs, you spawn a cube with ``Cube``, then apply rigid body and collision by wrapping the prim with ``RigidPrim`` and ``GeomPrim``. The script creates a cube at ``/dynamic_cube`` and then applies physics and collision to it:


      .. literalinclude:: ../snippets/introduction/quickstart_isaacsim/cube_with_physics_and_collision.py
          :language: python


      .. rubric::  Move, Rotate, and Scale the Cube



      The snippet below shows the lines that moved the objects in the scene using the core API.

      .. literalinclude:: ../snippets/introduction/quickstart_isaacsim/moving_an_object_using_core_api_standalone.py
          :language: python
          :start-after: # -- End test setup --

Save your work. 

You can now proceed to :ref:`the next tutorial <isaac_sim_app_intro_quickstart_robot>`.
