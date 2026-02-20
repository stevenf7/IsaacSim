=============================================
Tutorial 8: Generate Robot Configuration File
=============================================


Learning Objectives
=======================

This is the third manipulator tutorial in a series of four tutorials. This tutorial will show you how to generate the robot configuration file for the UR10e robot from Universal Robots and the 2F-140 gripper from Robotiq.
These robot configuration files provide information about the robot's kinematics, dynamics, and other properties that are used in RMPFlow, CuMotion, and Lula kinematics solvers.

*30 Minutes Tutorial*

Prerequisites
==============

- Review :doc:`tutorial_configure_manipulator` tutorial prior to beginning this tutorial, continue the following steps from the asset built in the previous tutorial.

.. note::
    If you have not completed the previous tutorial, you can find the prebuilt asset in the content browser at ``Isaac Sim/Samples/Rigging/Manipulator/Configure_Manipulator/ur10e/ur/ur_gripper.usd``.
   

Generate Robot URDF
======================

Generate the robot URDF file from the UR10e robot and the 2F-140 gripper.

Enable the Isaac Sim USD to URDF Exporter Extension
---------------------------------------------------

#. Go to **Window** > **Extensions**.
#. Type **URDF** in the search box, and find the **Isaac Sim USD to URDF Exporter Extension**.
#. If you can't find it, remove the **@feature** filter from the search box.
#. Enable the extension by clicking the toggle button labeled **ENABLE**.
#. Check the box for **AUTOLOAD**, just to the right of **ENABLE**.


Export the URDF File
---------------------

#. Open the ``ur_gripper.usd`` asset you made in the previous tutorial, or use the completed asset provided above.
#. Click **File** > **Export URDF**.
#. In File name on the bottom left corner, save the file name to ``ur_gripper.urdf``.
#. In the **Mesh Directory Path** field, select the correct folder path to save the URDF meshes.
#. Click **Export**.

.. image:: /images/isim_5.0_full_tut_gui_export_urdf.png
   :width: 80%
   :align: center

.. note:: Learn more about the USD to URDF Exporter Extension in the :ref:`isaac_sim_app_extension_urdf_exporter` manual.


.. _isaac_sim_app_tutorial_generate_robot_config_lula:


Generate Lula Robot Description Files and Collision Spheres
=============================================================

Generate the Lula robot description files and collision spheres for the UR10e robot and the 2F-140 gripper. 

Enable the Isaac Sim Lula Extension
-----------------------------------

#. Go to  **Window** > **Extensions**.
#. Type **Lula** in the search box, and find the **Isaac Sim Lula** Extension.
#. If you can't find it, remove the **@feature** filter from the search box.
#. Enable the extension by clicking the toggle button labeled **ENABLE**.
#. Check the box for **AUTOLOAD**, just to the right of **ENABLE**.


Prepare the Robot Asset for Lula
--------------------------------

The Lula robot description editor does not support instantiable meshes. You must prepare the robot asset for Lula by removing the instantiable meshes.

#. Open the ``ur_gripper.usd`` asset you made in the previous tutorial, or use the completed asset provided above.
#. Select all ``visuals`` and ``collisions`` prims on the stage. 
#. On the property editor, uncheck the **Instantiable** field.

   .. hint::
      You can use the search feature to find the ``visuals`` and ``collisions`` prims by searching for ``visuals`` and ``collisions`` respectively.


The completed asset for this tutorial can be found in the content browser at ``Isaac Sim/Samples/Rigging/Manipulator/configure_manipulator/ur10e/ur/ur_gripper_lula.usd``.

Configure Joints in Lula Robot Description Editor
-------------------------------------------------

1. Press **PLAY** to start the simulation.
2. Click **Tools** > **Robotics > **Lula Robot Description Editor**.
3. In the **Selection Panel**, select the **ur** articulation.
4. Go down to the **Set Joint Properties** section.
5. For each of the Universal Robots joints, set the **Joint Status** to **Active Joint**, keep the other settings as default.
6. Keep the Robotiq 2F-140 gripper joints as **Fixed Joint**, so the robotics controller will not attempt to move the gripper joints to optimize for the robot position.

.. hint:: 
   The gripper and arm usually are controlled separately. Because the Lula framework does not actually control the gripper during collision checking, the cspace does not need to include the gripper joints.

.. important:: **Do not stop the simulation**, you will need it to generate the collision spheres.

.. image:: /images/isim_5.0_full_tut_gui_lula_robot_description_editor.png
   :width: 80%
   :align: center


 
Pay attention to the default values of the joints in ``cspace_to_urdf_rules``. 
They must be the same positions with the initial pose in the manipulator USD, or you need to reset the robot joint positions to these initial positions during task initialization. 

Generate Collision Spheres
---------------------------

#. **Do not stop the simulation**, or exit the Lula Robot Description Editor, or you will need to redo the previous steps.
#. Go down to the **Link Sphere editor** section.
#. For each of the robot links that you want ot generate collision spheres for, in the **Selection Panel/Select link**, select the link. Use **upper_arm_link** as an example.
#. In the **Link Sphere editor/Generate Spheres/Select Mesh** dropdown menu, select the mesh that the collision spheres are based on. For example, select ``/collisions/upperarm/mesh``.
#. Set the **Radius Offset** to ``0.03``. This is the offset between the mesh radius and the collision sphere radius.
#. Set the **Number of Spheres** to ``8``. This is the number of collision spheres to generate. Validate that you see eight red spheres on the **upper_arm_link**.
#. Optionally, adjust the **Sphere Position** by left clicking on the spheres and dragging them around.
#. Click **Generate Spheres**, the sphere will turn a cyan color to indicate that the collision spheres have been generated.
#. Repeat the same steps for all the other links in the **ur** articulation, including the gripper links.

   .. image:: /images/isim_5.0_full_tut_gui_lula_link_sphere_editor.png
      :width: 80%
      :align: center

   .. important:: **Do not stop the simulation**, you will need it to generate the robot configuration file.

#. Verify that the completed asset looks like the following image:

   .. image:: /images/isim_5.0_full_tut_gui_lula_link_sphere_editor_add_spheres.png
      :width: 80%
      :align: center

The following suggestions can help you tune the collision spheres:

    #. In general, make the collision spheres large enough to encompass the link, but not too large to cause solver issues. 
    #. When choosing the size and number of collision spheres, the more collision spheres the more accurate the collision detection will be, but too many collision spheres will slow down the solver.
    #. Unless you have specified collider meshes, there's no restrictions to generate collision spheres on the collision meshes of the links only. If the visual mesh give you better collision mesh approximation, you can generate the collision spheres on the visual mesh.
    #. For longer arm links, it is generally easier to use the method above to only generate collision spheres on the ends of the link, then use ``Link Sphere editor/Generate Spheres/Add Spheres`` to add the collision spheres to the entire link evenly.
    #. If the sphere sizes are too small or too large, you can use ``Link Sphere editor/Generate Spheres/Scale Spheres in Link`` to scale the sphere sizes.
    #. The generate spheres utility is not guaranteed to work for all meshes.  It only works for water-tight triangle meshes. If the automatic generator doesn't work for a link, add the spheres and connect them by hand.


Export the Lula Robot Description File
--------------------------------------

#. **Do not stop the simulation or save the file**, you need it to export the robot configuration file.
#. In the **Lula Robot Description Editor**, go to the very bottom and find the **Export To File** section.
#. Expand **Export to Lula Robot Description File**, click the file icon and specify the file name to ``ur10e.yaml``.
#. Click **Save** to export the robot configuration file:

   .. image:: /images/isim_5.0_full_tut_gui_lula_export_robot_description_file.png
      :width: 80%
      :align: center

#. You can also export the cuMotion XRDF file by going to **Export To File** > **Export to cuMotion XRDF** and specify the file name to ``ur10e.xrdf``.
#. Stop the simulation after the robot configuration files are exported.

.. image:: /images/isim_5.0_full_tut_gui_lula_export_cucore_xrdf_file.png
   :width: 80%
   :align: center

See :ref:`isaac_sim_app_tutorial_motion_generation_robot_description_editor` for more information on the robot description files.


Summary
=======

In this tutorial, you have learned how to generate the robot configuration file for the UR10e robot and the 2F-140 gripper using the :ref:`isaac_sim_app_tutorial_motion_generation_robot_description_editor` 
and the :ref:`isaac_sim_app_extension_urdf_exporter` extensions.



