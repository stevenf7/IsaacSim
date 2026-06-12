
.. _isaac_sim_app_tutorial_intro_environment_setup:

=============================
Tutorial 1: Stage Setup
=============================

|isaac-sim_short| is built on `NVIDIA Omniverse <https://docs.omniverse.nvidia.com/>`_ using tools provided in :doc:`Omniverse Kit <dev-guide:index>`. |kit| comes with a default UI that
allows you to edit a USD stage with ease. In this tutorial, you learn the basic steps for setting up an environment, adding and editing simple objects and their properties on a USD stage, 
rigging rigid bodies with joints and articulations, and adding cameras and sensors. 
The goal is to build your basic skills in navigating |isaac-sim_short|, becoming familiar with frequently used terms, and using the GUI to build an environment and set up your robots.

Learning Objectives
=======================

This tutorial teaches you to build a physics-enabled virtual world using the tools provided in the |isaac-sim_short| GUI, including:

- Setup global stage properties
- Setup global physics properties
- Add ground plane
- Add lighting

.. - Rendering properties

Prerequisites
=======================


To start with a clean |isaac-sim_short| stage, go to the File menu and click on **New**. 
The stage provided has a default :code:`World` :term:`Xform<XForm>`, and a :code:`defaultLight`. Both can be found on the stage tree on the right of the viewport.



Setting up Stage Properties
==============================

Before anything is added onto the stage, verify that the current stage property setup matches the your expected conventions. 

#. Go to **Edit > Preferences** to open up the Preference panel. 
#. Browse the many types of settings inside |kit| grouped into categories in the column on the left of the panel. 
#. Select **Stage** from the left column and review the properties such as:

   - The axis that determines *Up*. The default in |isaac-sim_short| is Z. If your asset is created in a program with a different up-axis, it causes your assets to be imported rotated.
   - Stage units. |isaac-sim_short| versions prior to 2022.1 have stage units in centimeters, but the default is now meters. However, the default units for |kit| is still in centimeters. Keep that in mind if you see USD units that are seemingly off by 100x.
   - Default rotation order. The default is set to execute rotation in Z, then Y, and last X.


.. figure:: /images/isim_4.5_base_ref_gui_preferences.png
    :align: center


Creating the Physics Scene
============================

To add a **Physics Scene** to simulate real world physics, including gravity and physics time steps:

#. Go to the Menu Bar and click **Create > Physics > Physics Scene**. 
#. Validate that a **PhysicsScene** is added to the stage tree. 
#. Click on it to examine its properties. 
   You can see that gravity is set to the magnitude of ``Earth Gravity``, or ``9.8`` meters per second squared. Remember that the default unit of length is meters.
#. Unless you are simulating hundreds of rigid bodies and robots, it is more efficient to use CPU physics
    - Open Physics Scene's **Property** tab
    - Uncheck **Enable GPU dynamics** 
    - Set the **Broadphase** type to **MBP**.

.. figure:: /images/isim_5.0_base_ref_gui_physics_properties.png
    :align: center

Adding a Ground Plane
============================

The ground plane prevents any physics-enabled objects from falling below it. 
The ground plane's collision property extends indefinitely even though the plane is only visible up to 25 meters in each direction. 

To add a ground plane to the virtual environment:

#. Go to the top Menu Bar and click **Create > Physics > Ground Plane**. 
#. Turn on the grid by clicking on |eyecon| and selecting **Grid** to make the ground plane easier to see.

Lighting
====================

Every new :ref:`isaac_sim_glossary_stage` is pre-populated with a :code:`defaultLight`, otherwise you wouldn't see anything. This default light is a child of the :code:`Environment` Xform in the stage and can be found in the stage context tree.

To create additional spotlights:

#. Add a ground plane, if there isn't already one, so we can see the reflection of the light. **Create > Physics > Ground Plane**.
#. Go to **Create > Lights > Sphere Light**.
#. Pose the light on the stage. 
   - In the **Stage** tab on the top right, select the newly created light in the stage tree.
   - In the **Property** tab on the bottom , in the **Transform** section use the **Translate** tool to move it to a position above the ground plane, such as ``(0, 0, 7)``.
   - In the **Property** tab, in the **Transform** section, use the **Orient** tool to set the rotation to ``(0, 0, 0)``. 
#. Modify light color, brightness, and scope properties:
   - Inside the **Property** tab, change its color in **Main > Color** by clicking on the color bar and pick a color of your choice. For example a light green color ``(RGB: 0.5, 1.0, 0.5)``.
   - Also inside the **Property** tab, change its intensity **Main > Intensity** to **1e6**; **Main > Radius** to **0.05**
   - In the **Shaping** section, change the **cone:angle** to **45** degrees and **cone:softness** to **0.05**.
#. To make the new spotlight easier to see, we will reduce the intensity of the default light by going to its **Property** tab and set **Main > Intensity** to **300**.

.. figure:: /images/isim_4.5_base_ref_gui_lighting.png
    :align: center

Summary
========

This tutorial begins the necessary steps to create a virtual world suitable for physics simulation and testing |isaac-sim_short|.
The following topics were covered:

* Adding a ground plane, lighting, and physics scene.

Next Steps
^^^^^^^^^^^^^^^^^^^^^^

Continue on to :ref:`isaac_sim_app_tutorial_intro_assemble_robot` to learn how to add simple objects to |isaac-sim_short| and edit their properties.

Further Learning
^^^^^^^^^^^^^^^^^^^^^^

For more in-depth and creative world-building tools, refer to our sister Omniverse tool :doc:`Composer <composer:index>`.

.. |eyecon| image:: /images/isim_4.5_base_ref_gui_eyecon.png
    :width: 30
