=============================================
Tutorial 8: Generate Robot Configuration File
=============================================


Learning Objectives
=======================

This is the third manipulator tutorial in a series of four tutorials. This tutorial will show you how to generate the robot configuration file for the UR10e robot from Universal Robots and the 2F-140 gripper from Robotiq.
These robot configuration files provide information about the robot's kinematics, dynamics, and other properties that are used in RMPFlow and |cumotion| motion planners.

*30 Minutes Tutorial*

Prerequisites
==============

- Review :doc:`tutorial_configure_manipulator` tutorial prior to beginning this tutorial, continue the following steps from the asset built in the previous tutorial.

.. note::
    If you have not completed the previous tutorial, you can find the prebuilt asset in the content browser at ``Isaac Sim/Samples/Rigging/Manipulator/configure_manipulator/ur10e/ur/ur_gripper.usd``.
   

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
#. In File name on the bottom left corner, save the file name to ``robot.urdf``.

   .. tip::
      Using ``robot.urdf`` matches the default ``--urdf`` value in the pick-and-place tutorial scripts, so you won't need to pass ``--urdf`` explicitly when running them.

#. In the **Mesh Directory Path** field, select the correct folder path to save the URDF meshes.
#. Click **Export**.

.. image:: /images/isim_6.0_full_tut_gui_export_urdf.png
   :width: 80%
   :align: center

.. note:: Learn more about the USD to URDF Exporter Extension in the :ref:`isaac_sim_app_extension_urdf_exporter` manual.


.. _isaac_sim_app_tutorial_generate_robot_config_lula:


Generate Robot Description Files and Collision Spheres
=============================================================

Generate the XRDF file and collision spheres for the UR10e robot and the 2F-140 gripper. 

Enable the Robot Description Editor Extension
---------------------------------------------

#. Go to **Window** > **Extensions**.
#. Search for ``isaacsim.robot_setup.xrdf_editor`` and find the **cuMotion/Lula Robot Description Editor** extension.
#. If you can't find it, remove the **@feature** filter from the search box.
#. Enable the extension by clicking the toggle button labeled **ENABLE**.
#. Check the box for **AUTOLOAD**, just to the right of **ENABLE**.


Prepare the Robot Asset
-----------------------

The Robot Description Editor does not support instanceable meshes. You must prepare the robot asset by disabling instanceable meshes.

#. Open the ``ur_gripper.usd`` asset you made in the previous tutorial, or use the completed asset provided above.
#. Select all ``visuals`` and ``collisions`` prims on the stage.
#. In the **Property** panel, uncheck the **Instanceable** checkbox for each.

   .. hint::
      You can use the search feature to find the ``visuals`` and ``collisions`` prims by searching for ``visuals`` and ``collisions`` respectively.

.. figure:: /manipulators/images/isim_6.0_full_tut_gui_lula_description_editor_instanceable_disable.png
   :align: center
   :alt: Property panel showing the Instanceable checkbox that should be unchecked

   The **Instanceable** checkbox (highlighted in red) should be unchecked for all geometry prims.

Configure Joint Properties
--------------------------

#. Press **Play** to start the simulation.
#. Open the editor via **Tools** > **Robotics** > **cuMotion/Lula Robot Description Editor**.
#. In the **Selection Panel**, set **Select Articulation** to the **ur** articulation prim path.
#. In **Set Joint Properties**, assign each joint a **Joint Status**:

   * Mark each Universal Robots arm joint as **Active Joint**. These joints are directly controlled by cuMotion.
   * Keep the Robotiq 2F-140 gripper joints as **Fixed Joint**. cuMotion holds these joints at the specified default position.

.. important:: **Do not stop the simulation**, you will need it to generate the collision spheres.

.. image:: /images/isim_6.0_full_tut_gui_robot_description_editor.png
   :width: 50%
   :align: center

Pay attention to the default joint positions for fixed joints. They should match the initial pose defined in the manipulator USD, or you will need to reset the robot to those positions during task initialization.

Generate Collision Spheres
--------------------------

.. important:: **Do not stop the simulation** or exit the Robot Description Editor during this step, or you will need to redo the previous steps.

Repeat the following for each link in the **ur** articulation, including gripper links:

#. In the **Selection Panel**, select the link under **Select Link**. Use **upper_arm_link** as an example.
#. In **Link Sphere Editor** > **Generate Spheres**, select a mesh from the **Select Mesh** dropdown (e.g. ``/collisions/upperarm/mesh``).
#. Set the **Radius Offset** and **Number of Spheres** (e.g. ``0.03`` and ``8`` respectively).
#. Optionally adjust sphere positions by clicking and dragging them in the viewport.
#. Click **GENERATE SPHERES**. The spheres will turn cyan when finalized.

.. dropdown:: Suggested per-link sphere settings (ur10e + Robotiq 2F-140)
   :icon: table

   For links with multiple mesh entries, generate spheres for each mesh and combine them on the same link.

   .. list-table::
      :header-rows: 1
      :widths: 30 15 15 40

      * - Select Link
        - Number of Spheres
        - Radius Offset
        - Select Mesh
      * - ``/shoulder_link``
        - 1
        - 0.03
        - ``/collisions/shoulder/mesh``
      * - ``/upper_arm_link``
        - 8
        - 0.03
        - ``/visuals/upperarm/mesh``
      * - ``/forearm_link``
        - 8
        - 0.03
        - ``/visuals/forearm/mesh``
      * - ``/wrist_1_link``
        - 1
        - 0.03
        - ``/visuals/wrist1/mesh``
      * - ``/wrist_2_link``
        - 1
        - 0.02
        - ``/visuals/wrist3/mesh``
      * - ``/wrist_3_link``
        - 1
        - 0.02
        - ``/visuals/wrist3/mesh``
      * - ``/ee_link/robotiq_arg2f_base_link``
        - 1
        - 0.02
        - ``/visuals/robotiq_arg2f_base_link/mesh``
      * - ``/ee_link/left_outer_knuckle``
        - 2
        - 0.02
        - ``/visuals/robotiq_arg2f_140_outer_knuckle/mesh``
      * - ``/ee_link/left_outer_knuckle``
        - 2
        - 0.02
        - ``/visuals/robotiq_arg2f_140_outer_finger/mesh``
      * - ``/ee_link/left_inner_finger``
        - 2
        - 0.02
        - ``/collisions/robotiq_arg2f_140_inner_finger/mesh``
      * - ``/ee_link/right_inner_finger``
        - 2
        - 0.02
        - ``/collisions/robotiq_arg2f_140_inner_finger/mesh``
      * - ``/ee_link/left_inner_knuckle``
        - 2
        - 0.02
        - ``/visuals/robotiq_arg2f_140_inner_knuckle/mesh``
      * - ``/ee_link/right_inner_knuckle``
        - 2
        - 0.02
        - ``/visuals/robotiq_arg2f_140_inner_knuckle/mesh``
      * - ``/ee_link/right_outer_knuckle``
        - 2
        - 0.02
        - ``/visuals/robotiq_arg2f_140_outer_knuckle/mesh``
      * - ``/ee_link/right_outer_knuckle``
        - 2
        - 0.02
        - ``/visuals/robotiq_arg2f_140_outer_finger/mesh``

.. figure:: /images/isim_6.0_full_tut_gui_link_sphere_editor.png
   :width: 80%
   :align: center
   :alt: Collision spheres generated on the upper_arm_link of the UR10e

   Spheres generated for the upper_arm_link.

.. figure:: /images/isim_6.0_full_tut_gui_link_sphere_editor_add_spheres.png
   :width: 80%
   :align: center
   :alt: Collision spheres generated on every link of the UR10e

   Spheres generated for the full ur10e robot.


.. admonition:: General tuning tips
   :class: tip

   * Size spheres to cover the link without being oversized — large spheres cause solver conservatism.
   * More spheres improves collision accuracy but reduces solver performance.
   * For long cylindrical links, generate spheres on the ends and use **Connect Spheres** to fill the middle evenly.
   * Use **Scale Spheres in Link** to resize spheres uniformly across a link.
   * The auto-generator requires water-tight triangle meshes. If it fails for a link, add and connect spheres manually.


Export to XRDF
--------------

.. important:: **Do not stop the simulation** before exporting.

#. At the bottom of the Robot Description Editor, expand **Export To File** > **Export to cuMotion XRDF**.
#. Click the file icon and specify the file name as ``robot.xrdf``.
#. Select the XRDF version to export (version 2.0 is recommended).
#. Click **Save**. Save to the same directory as the robot URDF file.
#. Stop the simulation after the file is exported.

.. _isaac_sim_app_tutorial_generate_robot_config_adding_tool:

Adding a Tool to the Robot Configuration
----------------------------------------

|cumotion| requires a tool frame defined in the XRDF file. The tool frame is used to specify the end-effector frame for the robot.

#. Open the ``robot.xrdf`` file in a text editor.
#. Add the following line to the file:

   .. code-block:: text

      tool_frames: ["wrist_3_link"]

See :ref:`isaac_sim_cumotion_tutorial_robot_configuration` for more information on XRDF files and loading robot configurations into cuMotion.

Assemble the Robot Configuration Directory
===========================================

The pick-and-place tutorial scripts and the ``load_cumotion_robot`` API expect all robot configuration files to live in a single directory. After completing the export steps above, your directory should look like this:

.. code-block:: text

    /path/to/robot/config/
    ├── robot.urdf
    ├── robot.xrdf
    ├── rmp_flow.yaml
    └── meshes/
        └── ...

Pass this directory to the tutorial scripts with ``--xrdf-dir /path/to/robot/config``. For a full description of these files and how they are used by cuMotion, see the :ref:`Robot Configuration Files <isaac_sim_cumotion_tutorial_robot_configuration>` section of the cuMotion tutorial.

The ``rmp_flow.yaml`` file configures the RMPflow reactive motion controller. Save the text below in a file named ``rmp_flow.yaml`` and save it to the same directory as your ``robot.urdf`` and ``robot.xrdf`` files.

.. dropdown:: rmp_flow.yaml — RMPflow configuration example

    .. literalinclude:: ../snippets/robot_setup_tutorials/tutorial_generate_robot_config/rmp_flow.yaml
        :language: yaml

Summary
=======

In this tutorial, you have learned how to generate the robot configuration files for the UR10e robot and the 2F-140 gripper using the :ref:`Robot Description Editor <isaac_sim_app_tutorial_motion_generation_robot_description_editor>` and the :ref:`isaac_sim_app_extension_urdf_exporter` extensions. The resulting XRDF file can be loaded directly into cuMotion motion planners as described in :ref:`isaac_sim_cumotion_tutorial_robot_configuration`.



