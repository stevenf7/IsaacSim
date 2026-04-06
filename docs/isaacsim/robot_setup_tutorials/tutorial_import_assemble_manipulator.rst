==========================================
Tutorial 6: Setup a Manipulator
==========================================


Learning Objectives
=======================

This is the first manipulator tutorial in a series of four tutorials. This tutorial shows how to import the UR10e robot from Universal Robots and the 2F-140 gripper from Robotiq into |isaac-sim| from URDF files and connect them together under one articulation.

*30 Minutes Tutorial*

Prerequisites
==============

- If you are new to |isaac-sim|, complete the :ref:`Wheeled Robot Set Up Tutorials <isaac_sim_app_tutorial_intro_environment_setup>` tutorial prior to beginning this tutorial.
- Review the ROS 2 installations :ref:`isaac_sim_app_install_ros` prior to beginning this tutorial.
- Review the URDF importer :ref:`isaac_sim_urdf_importer` tutorial.
- In a ROS sourced terminal, install xacro using the following command (Linux only):

  .. code-block:: bash

      sudo apt install ros-$ROS_DISTRO-xacro

- Locate the ``import_manipulator`` folder in the content browser at ``Isaac Sim/Samples/Rigging/Manipulator/import_manipulator/``.

.. Note::
   The ROS URDF import steps are tested on Linux only, it may not work on Windows (WSL). On Windows with Pixi-based installation, these steps are supported. If you are using Windows (WSL), you can skip the ROS import steps and use the USD files provided in the content browser.
   
Build and Install the UR Description Package (Linux only)
==============================================================

|isaac-sim_short| requires Python 3.10 on Ubuntu 22.04 and Python 3.12 on Ubuntu 24.04, which is not natively supported by the ROS 2 UR description package, so we need to build the package from source.

.. Note::
   See :ref:`isaac_sim_ros_workspace` for more information on setting up your custom ROS 2 package in your ROS workspace.

Clone the UR Description Package
---------------------------------

#. Clone the UR description package from the `Universal Robots ROS 2 Description repository <https://github.com/UniversalRobots/Universal_Robots_ROS2_Description>`_.

   .. code-block:: bash

      git clone https://github.com/UniversalRobots/Universal_Robots_ROS2_Description.git

#. Switch to the branch that matches your ROS distribution.

   .. tab-set::
      
      .. tab-item:: ROS 2 Humble

         .. code-block:: bash

            git checkout humble

      .. tab-item:: ROS 2 Jazzy

         .. code-block:: bash

            git checkout jazzy

#. Copy the repository into your Isaac Sim ROS Workspace ``src`` folder.

Build the UR Description Package Using Python 3.11
--------------------------------------------------

#. Go to the Isaac Sim ROS Workspace, and run the following command to build the UR description package using Python 3.11.

   .. code-block:: bash

      ./build_ros.sh

#. Source the Python 3.11 ROS environment and launch Isaac Sim. Replace ``<ROS distro>`` with your ROS distribution (for example, ``humble`` or ``jazzy``).

   .. code-block:: bash

      source build_ws/<ROS distro>/<ROS distro>_ws/install/local_setup.bash
      source build_ws/<ROS distro>/isaac_sim_ros_ws/install/local_setup.bash
      ./path/to/isaac-sim.sh
   


Build the UR Description Package Using System ROS
-------------------------------------------------

#. Source your system ROS environment. Refer to :ref:`isaac_sim_ros_workspace_setup` for more information on setting up your ROS 2 workspace.
#. Navigate to your Isaac Sim ROS Workspace and run the following commands to build it:

   .. code-block:: bash

      rosdep install -i --from-path src --rosdistro $ROS_DISTRO -y 
      colcon build
      source install/setup.sh
   

Import the UR10e Robot (Linux only)
======================================

Enable the ROS 2 Robot Description URDF Importer Extension
----------------------------------------------------------

#. Go to ``Window`` > ``Extensions``.
#. Type ``URDF`` in the search box, and find the ``ROS 2 Robot Description URDF Importer Extension``.
#. If you can't find it, remove the ``@feature`` filter from the search box.
#. If you still can't find it, make sure Isaac Sim was launched from the same terminal where ROS was sourced.
#. Enable the extension by clicking the toggle button labeled ``ENABLE``.
#. Check the box for ``AUTOLOAD``, just to the right of ``ENABLE``.

Launch the URDF Publisher Topic
---------------------------------

#. In the system ROS sourced terminal that you created earlier, launch the UR10e description by running:

   .. code-block:: bash

      ros2 launch ur_description view_ur.launch.py ur_type:=ur10e

#. Verify that you see a window similar to the image below:

   .. image:: /images/isim_5.0_full_tut_gui_ur10_rviz.png
      :width: 80%
      :align: center
      :alt: UR10e Description

#. Set up one more terminal for ``rqt_graph``, to see ROS nodes and topics being published:

   .. code-block:: bash

      rqt_graph

#. Verify that you see a window similar to the image below:

   .. image:: /images/isim_5.0_full_tut_gui_ur10_rqt.png
      :width: 80%
      :align: center
      :alt: UR10e RQT Graph

.. hint::
   If the nodes are not showing up in ``rqt_graph``, press the refresh button next to the drop down menu.

Import the UR10e Robot into Isaac Sim
----------------------------------------

#. Go to Isaac Sim.
#. Navigate to **File** > **Import from the ROS 2 URDF Node**.

   - In the **Node** field, type ``robot_state_publisher``, click **Refresh**.
   - In the **Model** field, select the desired output (for example, ``~/Desktop``).
   - Select **Natural Frequency** for joint configuration.
   - Select all the joints listed below, then set the **Natural Frequency** to ``300`` to ensure the joints are sufficiently stiff.

   .. image:: /images/isim_5.0_full_tut_gui_ur10_importer.png
      :width: 80%
      :align: center
      :alt: UR10e Import

#. Click **Import**.

For reference, the resulting USD file is available in the content browser at ``Isaac Sim/Samples/Rigging/Manipulator/import_manipulator/ur10e/ur/ur.usd``.

Import the Robotiq 2F-140 Gripper (Linux only)
=====================================================

Use the URDF file provided by `ros-industrial-attic <https://github.com/ros-industrial-attic/robotiq/tree/kinetic-devel>`_. 
Even though this package is built for ROS1 and is deprecated, you can still adopt the URDF files and import the gripper for |isaac-sim|.

Convert XACRO to URDF
-----------------------

#. Download the Repository from `here <https://github.com/ros-industrial-attic/robotiq/tree/kinetic-devel>`_.

   .. code-block:: bash

      git clone https://github.com/ros-industrial-attic/robotiq.git

#. Navigate to the ``robotiq/robotiq_2f_140_gripper_visualization/urdf`` folder, open each xacro file. 

   - Replace ``$(find robotiq_2f_140_gripper_visualization)`` with the relative path to the target file (for example, ``robotiq_arg2f_transimission.xacro``) from the current xacro file.

      For example, in ``robotiq_arg2f_140_model.xacro``, replace:

      .. code-block:: bash

            <xacro:include filename="$(find robotiq_2f_140_gripper_visualization)/urdf/robotiq_arg2f_transmission.xacro" />

      With:

      .. code-block:: bash
     
            <xacro:include filename="./robotiq_arg2f_transmission.xacro" />

   - Replace ``package://`` with the relative path to the target file (for example, ``robotiq_arg2f_${stroke}_inner_finger.stl``) from the current xacro file.  

      For example, in ``robotiq_arg2f_140_model.xacro``, replace:

        .. code-block:: bash

            <mesh filename="package://robotiq_2f_140_gripper_visualization/meshes/visual/robotiq_arg2f_${stroke}_inner_finger.stl" />

      With:

      .. code-block:: bash

            <mesh filename="../meshes/visual/robotiq_arg2f_${stroke}_inner_finger.stl" />

#. Convert the xacro files to URDF format:

   .. code-block:: bash

      xacro robotiq_arg2f_140_model.xacro > robotiq_2f_140.urdf

   If you encounter the error ``xacro: command not found``, you need to install xacro.

   * Install xacro using the following command:

    .. code-block:: bash

        sudo apt install ros-$ROS_DISTRO-xacro


For reference, the resulting URDF files is available in the content browser at ``Isaac Sim/Samples/Rigging/Manipulator/import_manipulator/robotiq_2f_140_urdf/urdf/robotiq_2f_140.urdf``.


Import Robotiq 2F-140 Gripper into Isaac Sim
-----------------------------------------------

#. Go to Isaac Sim.
#. Let's create a new stage by going to **File** > **New**.
#. Navigate to **File** > **Import**.
#. Select the ``robotiq_2f_140.urdf`` file that you imported from the previous step.
#. In the import settings:

   - For USD Output, navigate to your desktop using file browser and select **Desktop** this will be the output location of the gripper USD.
   - For ``finger_joint``, set the Natural Frequency to ``300``.
   - For the other joints of target ``Mimic``, set the Natural Frequency to ``2500``.

#. Click ``Import`` to complete the process.

   .. image:: /images/isim_5.0_full_tut_gui_robotiq_importer.png
      :width: 80%
      :align: center
      :alt: Gripper Import

For reference, the resulting USD file is available in the content browser at ``Isaac Sim/Samples/Rigging/Manipulator/import_manipulator/robotiq_2f_140/robotiq_2f_140.usd``.


Expected Parameters for Finger and Knuckle Joints
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

+---------------------+--------------+--------------+-----------+------------+-----------+------------+
| Joint Name          | Lower Limit  | Upper Limit  | Gearing   | Stiffness  | Damping   | Max Force  |
+=====================+==============+==============+===========+============+===========+============+
| Finger Joint        | 0            | 40.107       | N/A       | 37.51957   | 0.00125   | 1000       |
+---------------------+--------------+--------------+-----------+------------+-----------+------------+
| Left inner Finger   | -8.021       | 48.128       | -1        | N/A        | N/A       | N/A        |
+---------------------+--------------+--------------+-----------+------------+-----------+------------+
| Left Inner Knuckle  | -48.128      | 8.021        | 1         | N/A        | N/A       | N/A        |
+---------------------+--------------+--------------+-----------+------------+-----------+------------+
| Right inner Knuckle | -48.128      | 8.021        | 1         | N/A        | N/A       | N/A        |
+---------------------+--------------+--------------+-----------+------------+-----------+------------+
| Right outer knuckle | -48.128      | 8.021        | 1         | N/A        | N/A       | N/A        |
+---------------------+--------------+--------------+-----------+------------+-----------+------------+
| Right inner Finger  | -8.021       | 48.128       | -1        | N/A        | N/A       | N/A        |
+---------------------+--------------+--------------+-----------+------------+-----------+------------+

Expected Parameters for Mimic Joints
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- Reference Joint: ``/robotiq_arg2f_140_model/joints/finger_joint``
- Reference Joint Axis: ``rotX``
- Natural Frequency: ``2500``
- Damping Ratio: ``0.005``



Connect the UR10e Robot with the Robotiq 2F-140 Gripper
========================================================

Much like a real robot can have its tools changed for different tasks, simulated robots benefit from the same capability. This section outlines two methods to connect the UR10e robot with the Robotiq 2F-140 gripper:

- **Option 1**, shows how to connect the gripper to the robot directly using a fixed joint with a shared articulation. 
- **Option 2**, shows how to use the robot assembler and variant to connect the end effectors to the robot. Depending on the variant selected, the gripper will be added as a payload, which allows us to load or unload the different end effectors depending on which variant is enabled.


Option 1: Connect the UR10e with the Robotiq 2F-140 Gripper using the GUI
---------------------------------------------------------------------------

#. Open the UR10e USD file created from the last activity (``ur.usd``).
#. Drag and drop the ``robotiq_2f_140.usd`` file, we created earlier, into the stage.
#. Rename the ``robotiq_2f_140.usd`` prim to ``ee_link``.
#. Set the ``ee_link`` xform to the position and orientation of ``wrist_3_link``.

   .. code-block:: bash

      Translate (1.18425, 0.2907, 0.06085)
      Orient (-90, 0, -90)

#. Select ``ee_link/root_joint``.
#. Go to the ``Physics Articulation Root`` section in the Property Editor, remove the ``Articulation Root``.

    Only select a single articulation for the robot.

#. Go down to the ``Joints`` section in the Property Editor.
#. Set ``Body0`` to ``/ur/wrist_3_link``, to joint the end effector to the robot.

   .. image:: /images/isim_5.0_full_tut_gui_connect_gripper_manual.png
      :width: 80%
      :align: center
      :alt: UR10e Manual Connection

Nest the UR10e robot schema into the 2F-140 gripper's robot schema:

#. Select the ``ur`` prim.
#. Go down to the ``IsaacRobotAPI`` section in the Property Editor, and add ``/ur/ee_link`` to both the ``isaac:physics:robotjoints`` and ``isaac:physics:robotLinks`` fields, to make sure that the UR10e robot's robot schema includes the 2F-140 gripper's robot schema.

.. image:: /images/isim_5.0_full_tut_gui_connect_gripper_manual_2.png
   :width: 80%
   :align: center
   :alt: UR10e Manual Connection 2

Your robot is now connected to the gripper, and you can test your robot in :doc:`tutorial_import_assemble_manipulator`.

For reference, we also provide the resulting USD file in Content Browser at ``Isaac Sim/Samples/Rigging/Manipulator/import_manipulator/ur10e/ur/ur_gripper_manual.usd``.

Option 2: Connect the UR10e with the Robotiq 2F-140 Gripper using the Robot Assembler
-------------------------------------------------------------------------------------

Alternatively, you can use the Robot Assembler to connect the UR10e with the Robotiq 2F-140 gripper. The robot assembler will add the gripper as a variant to a sublayer of the base robot, 
giving you greater flexibility to switch between different end effectors.

#. Open the UR10e USD file created from the last activity (``ur.usd``).
#. Drag and drop the ``robotiq_2f_140.usd`` file we created earlier into the stage.
#. Rename the ``robotiq_2f_140`` prim to ``ee_link``.
#. Open the robot assembler by going to **Tools** > **Robotics** > **Asset Editor** > **Robot Assembler**.

   - In **Base Robot**, set **Select Base Robot** to ``/ur``, **Attach Point** to ``wrist_3_link``.
   - In **Attach Robot**, set **Select Attach Robot** to ``/ur/ee_link``, **Attach Point** to ``robotiq_arg2f_base_link``.
   - Set **Assembly Namespace** to ``ee_link``.

#. Click **Begin Assembling Process** to start the process.

   .. image:: /images/isim_5.0_full_tut_gui_connect_gripper_assembler.png
      :width: 80%
      :align: center
      :alt: UR10e Assembler Connection


#. Adjust the attachment point orientation to make sure the end effector is attached to the gripper correctly. Rotate the gripper 90 degrees around the z-axis by clicking **Z +90**.

   .. image:: /images/isim_5.0_full_tut_gui_connect_gripper_assembler_2.png
      :width: 80%
      :align: center
      :alt: UR10e Assembler Connection 2

#. Click **Assemble and Simulate** to test the process.
#. Click **End Simulation And Finish** to complete the process.

Run the Simulation
~~~~~~~~~~~~~~~~~~~~~~~~~

#. In the Stage panel, select the **ur** prim.
#. In the Property Editor at the bottom right, find the **Variants** section.
#. Beside **ee_link**, select **None** and the gripper will be removed from the robot.
#. Beside **ee_link**, select **robotiq_2f_140** and the gripper will be added to the robot.
#. Save the asset by going to **File** > **Save** or press **Ctrl+S**.

.. image:: /images/isim_5.0_full_tut_gui_variant_editor_4.webp
   :width: 80%
   :align: center
   :alt: UR10e Variant Editor


.. Note::

   The completed robotics arm asset is available in the content browser at ``Isaac Sim/Samples/Rigging/Manipulator/import_manipulator/ur10e/ur/ur_gripper.usd``.


Summary
========

In this tutorial, you took the UR10e robot from Universal Robots and the 2F-140 gripper from Robotiq and imported them into |isaac-sim| from URDF files and connected them together under one articulation using the GUI and Robot Assembler.








