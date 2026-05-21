==========================================
Tutorial 6: Setup a Manipulator
==========================================


Learning Objectives
=======================

This is the first manipulator tutorial in a series of four tutorials. This tutorial shows how to import the UR10e robot from Universal Robots and the 2F-140 gripper from Robotiq into |isaac-sim| from URDF files and connect them together under one articulation.

*30 Minutes Tutorial*

|isaac-sim_short| always uses Python 3.12, so the UR description package and any ROS packages used in this tutorial must be available in a Python 3.12 environment. How you obtain the package depends on your platform:

- **Ubuntu 24.04 + ROS 2 Jazzy** — install the prebuilt ``ros-jazzy-ur-description`` apt package; the system Python (3.12) already matches |isaac-sim_short|.
- **Ubuntu 22.04 + ROS 2 Humble or Jazzy** — the system Python is 3.10, so the workspace must be cloned and rebuilt against Python 3.12 using the included ``build_ros.sh`` script.
- **Windows + Pixi-based ROS 2 Jazzy** — add the UR description package to your Pixi environment (``pixi add ros-jazzy-ur-description``); Pixi-managed ROS 2 Jazzy already runs on Python 3.12. See :ref:`isaac_sim_app_install_ros_other_platforms` for Pixi setup. WSL2 is not supported for the ROS-based URDF import workflow — use the prebuilt USD files in the content browser instead.

.. attention::
   ROS 2 Humble on Windows (Pixi) is not a supported configuration for this tutorial. On Windows, only ROS 2 Jazzy with Pixi is supported. Switch to ROS 2 Jazzy on Windows, or move to a Linux configuration, to follow this tutorial as written.

Verify or choose your configuration in the **Build Environment** banner at the top of this page to see the steps for your setup. Your selection drives the platform-specific commands throughout the rest of this page.

.. config-selector::
   :title: Build Environment
   :options: platform=Linux|Windows,ubuntu_version=Ubuntu 24.04|Ubuntu 22.04,ros_distro=Jazzy|Humble
   :dependencies: ubuntu_version=platform:Linux

Prerequisites
==============

- If you are new to |isaac-sim|, complete the :ref:`Wheeled Robot Set Up Tutorials <isaac_sim_app_tutorial_intro_environment_setup>` tutorial prior to beginning this tutorial.
- Review the ROS 2 installations :ref:`isaac_sim_app_install_ros` prior to beginning this tutorial.
- Review the URDF importer :ref:`isaac_sim_urdf_importer` tutorial.
- In a ROS sourced terminal, install xacro for your selected configuration (see the **Build Environment** banner at the top of the page):

  .. config-content::
     :show-when: platform=Linux

     .. code-block:: bash

        sudo apt install ros-$ROS_DISTRO-xacro

  .. config-content::
     :show-when: platform=Windows,ros_distro=Jazzy

     .. code-block:: bash

        pixi add ros-$ROS_DISTRO-xacro

  .. config-content::
     :show-when: platform=Windows,ros_distro=Humble

     .. attention::
        ROS 2 Humble on Windows (Pixi) is not a supported configuration. Switch to ROS 2 Jazzy on Windows, or move to a Linux configuration, to follow this tutorial as written.

- Locate the ``import_manipulator`` folder in the content browser at ``Isaac Sim/Samples/Rigging/Manipulator/import_manipulator/``.

Build and Install the UR Description Package
==============================================================

Follow the steps for the configuration you selected in the **Build Environment** selector at the top of this page.

.. config-content::
   :show-when: platform=Linux,ubuntu_version=Ubuntu 24.04,ros_distro=Jazzy

   Install the prebuilt UR description package and source ROS 2 Jazzy:

   .. code-block:: bash

      sudo apt install ros-jazzy-ur-description
      source /opt/ros/jazzy/setup.bash

   Then launch |isaac-sim_short| from the same terminal:

   .. code-block:: bash

      ./isaac-sim.sh

.. config-content::
   :show-when: platform=Linux,ubuntu_version=Ubuntu 22.04

   On Ubuntu 22.04, the system Python (3.10) does not match the Python 3.12 used by |isaac-sim_short|, and the UR description package is not natively available for Python 3.12. Clone the package and rebuild it with the included ``build_ros.sh`` script.

   .. Note::
      See :ref:`isaac_sim_ros_workspace` for more information on setting up your custom ROS 2 package in your ROS workspace.

   #. Change into your Isaac Sim ROS Workspace, then into the distro-specific workspace's ``src`` folder:

      .. config-content::
         :show-when: ros_distro=Jazzy

         .. code-block:: bash

            cd <path to Isaac Sim ROS Workspace>
            cd jazzy_ws/src

      .. config-content::
         :show-when: ros_distro=Humble

         .. code-block:: bash

            cd <path to Isaac Sim ROS Workspace>
            cd humble_ws/src

   #. Clone the branch of the `Universal Robots ROS 2 Description repository <https://github.com/UniversalRobots/Universal_Robots_ROS2_Description>`_ that matches your ROS distribution:

      .. config-content::
         :show-when: ros_distro=Jazzy

         .. code-block:: bash

            git clone --branch jazzy https://github.com/UniversalRobots/Universal_Robots_ROS2_Description.git

      .. config-content::
         :show-when: ros_distro=Humble

         .. code-block:: bash

            git clone --branch humble https://github.com/UniversalRobots/Universal_Robots_ROS2_Description.git

   #. Return to the Isaac Sim ROS Workspace root and build against Python 3.12:

      .. code-block:: bash

         cd ../..
         ./build_ros.sh

   #. Source the Python 3.12 ROS environment and launch |isaac-sim_short|.

      .. config-content::
         :show-when: ros_distro=Jazzy

         .. code-block:: bash

            source build_ws/jazzy/jazzy_ws/install/local_setup.bash
            source build_ws/jazzy/isaac_sim_ros_ws/install/local_setup.bash
            ./isaac-sim.sh

      .. config-content::
         :show-when: ros_distro=Humble

         .. code-block:: bash

            source build_ws/humble/humble_ws/install/local_setup.bash
            source build_ws/humble/isaac_sim_ros_ws/install/local_setup.bash
            ./isaac-sim.sh

.. config-content::
   :show-when: platform=Linux,ubuntu_version=Ubuntu 24.04,ros_distro=Humble

   .. attention::
      ROS 2 Humble on Ubuntu 24.04 is not an officially supported configuration in :ref:`isaac_sim_app_install_ros`. Switch to ROS 2 Jazzy on Ubuntu 24.04, or move to ROS 2 Humble on Ubuntu 22.04, to follow this tutorial as written.

.. config-content::
   :show-when: platform=Windows,ros_distro=Jazzy

   On Windows, the URDF import workflow in this tutorial is supported only with a `Pixi-based <https://pixi.sh/>`_ ROS 2 Jazzy installation. Follow :ref:`isaac_sim_app_install_ros_other_platforms` for Windows ROS 2 setup and to install or build the UR description package against the Pixi environment. If you are using WSL2, skip the ROS-based import steps and use the prebuilt USD files in the content browser at ``Isaac Sim/Samples/Rigging/Manipulator/import_manipulator/``.

.. config-content::
   :show-when: platform=Windows,ros_distro=Humble

   .. attention::
      ROS 2 Humble on Windows (Pixi) is not a supported configuration in :ref:`isaac_sim_app_install_ros`. Switch to ROS 2 Jazzy on Windows, or move to a Linux configuration, to follow this tutorial as written. If you need to use the UR10e on Windows without ROS, use the prebuilt USD files in the content browser at ``Isaac Sim/Samples/Rigging/Manipulator/import_manipulator/``.


Import the UR10e Robot
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

#. Open a new terminal with a **native** ROS 2 environment, source ROS 2 for your configuration, and launch the UR10e description.

   .. important::
      Do not reuse the Python 3.12 ``build_ws`` shell used to launch |isaac-sim_short| above. The ``build_ws`` paths exist only to source the matching ROS 2 bridge into |isaac-sim_short|; for ``ros2 launch`` commands, use your OS-native ROS 2 install (or a Docker container for distros that are not natively available on your OS).

   .. config-content::
      :show-when: platform=Linux,ubuntu_version=Ubuntu 24.04,ros_distro=Jazzy

      .. code-block:: bash

         source /opt/ros/jazzy/setup.bash
         ros2 launch ur_description view_ur.launch.py ur_type:=ur10e

   .. config-content::
      :show-when: platform=Linux,ubuntu_version=Ubuntu 22.04,ros_distro=Humble

      Source your native ROS 2 Humble install. If ``ur_description`` is not already available, install it from apt:

      .. code-block:: bash

         sudo apt install ros-humble-ur-description
         source /opt/ros/humble/setup.bash
         ros2 launch ur_description view_ur.launch.py ur_type:=ur10e

      Alternatively, build ``ur_description`` natively (Python 3.10) into ``humble_ws`` with ``colcon build``, then source ``humble_ws/install/local_setup.bash`` instead of using the apt package.

   .. config-content::
      :show-when: platform=Linux,ubuntu_version=Ubuntu 22.04,ros_distro=Jazzy

      ROS 2 Jazzy is not natively available on Ubuntu 22.04, so run the launch command from a ROS 2 Jazzy Docker container with ``jazzy_ws`` mounted and built natively. Follow :ref:`isaac_ros_docker_other_platforms` to start an ``osrf/ros:jazzy-desktop`` container, build ``jazzy_ws`` inside it, then from inside the container run:

      .. code-block:: bash

         source /jazzy_ws/install/local_setup.bash
         ros2 launch ur_description view_ur.launch.py ur_type:=ur10e

   .. config-content::
      :show-when: platform=Windows,ros_distro=Jazzy

      Activate the Pixi environment, then run:

      .. code-block:: bash

         ros2 launch ur_description view_ur.launch.py ur_type:=ur10e

   .. config-content::
      :show-when: platform=Windows,ros_distro=Humble

      .. attention::
         ROS 2 Humble on Windows (Pixi) is not a supported configuration. Switch to ROS 2 Jazzy on Windows, or move to a Linux configuration, to follow this tutorial as written.

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

Import the Robotiq 2F-140 Gripper
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

   If you encounter the error ``xacro: command not found``, install xacro for your configuration:

   .. config-content::
      :show-when: platform=Linux

      .. code-block:: bash

         sudo apt install ros-$ROS_DISTRO-xacro

   .. config-content::
      :show-when: platform=Windows,ros_distro=Jazzy

      .. code-block:: bash

         pixi add ros-$ROS_DISTRO-xacro

   .. config-content::
      :show-when: platform=Windows,ros_distro=Humble

      .. attention::
         ROS 2 Humble on Windows (Pixi) is not a supported configuration. Switch to ROS 2 Jazzy on Windows, or move to a Linux configuration, to follow this tutorial as written.


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








