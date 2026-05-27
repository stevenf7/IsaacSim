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

   - In the **ROS2 Node** field, type ``robot_state_publisher``, click **Find Node**.
   - In the **USD Output** field, select the desired output (for example, ``~/Desktop/``).
   - In the **Robot Type** field, select ``Manipulator``.
   - In the **Base Type** field, select ``Fixed``.

   .. image:: /images/isim_6.0_full_tut_gui_ur10_importer.png
      :width: 80%
      :align: center
      :alt: UR10e Import

#. Click **Import**, the importer should automatically open the ur robot.

For reference, the resulting USD file is available in the content browser at ``Isaac Sim/Samples/Rigging/Manipulator/import_manipulator/ur10e/ur/ur.usda``.

Set Gains Using the Gain Tuner
=================================

The importer does not set the gains for the UR robot automatically. You can use the Gain Tuner to set the gains for the UR robot.
In this tutorial, we will use the gain tuner to set the natural frequency and damping ratio for the UR robot, which are defined as:

.. math::
    \omega_n = \sqrt{\frac{K_p}{m}}

    \zeta = \frac{K_d}{2 m \omega_n}

Where :math:`\omega_n` is the natural frequency and :math:`\zeta` is the damping ratio, and :math:`m` is the computed joint inertia based on the mass of the robot at both sides of the joint. 
The damping ratio is such that :math:`\zeta = 1.0` is a critically damped system, :math:`\zeta < 1.0` is underdamped, and :math:`\zeta > 1.0` is overdamped.

Use the :ref:`isaac_gain_tuner` to set and verify the gains for the UR robot.

#. Go to **Tools** > **Robotics** > **Asset Editors** >  **Gain Tuner**.
#. On the **Gain Tuner** window, on the **Robot Selection** dropdown, select the **ur** articulation in the stage.
#. In the **Tune Gains** panel, you can adjust the gains for the robot and the gripper fingers joints. Test it with the **Test Gains Settings** panel. let's start by setting the natural frequency to ``300`` and the damping ratio to ``1.0``. 

.. hint::

   We recommend determining the gains for a small group of joints first, if it is difficult to tune the gains for the whole robot. Below are some tips for tuning the gains:

   * Higher the natural frequency, the faster the robot will respond to the target position. Lower the damping ratio, the faster the robot will reach the target position.
   * If the resulting plot shows the robot is undershooting the target position, you can increase the ``Nat. Freq.`` slightly.
   * If the resulting plot shows the robot is overshooting the target position, you can decrease the ``Nat. Freq.`` slightly and increase the ``Damping Ratio``.
   * Disabling gravity can help you see the gains more clearly.
   * Only gain test the joints that are expected to be moving together, the gain test order can be selected by the **Sequence** dropdown.
   * Reduce the maximum speed of a joint that you are tuning, if it is not expected to be commanded to move that fast in practice. The default values in the Gains Test are the maximum velocity written into the USD.

.. image:: /images/isim_5.0_full_tut_gui_gain_tuner_ur10e.png
   :width: 80%
   :align: center

.. note::
   See :ref:`isaac_gain_tuner` for more information on the Gain Tuner and :ref:`isaac_sim_app_tutorial_advanced_joint_tuning` for more information on how to tune the gains for the robot.

   For reference, the resulting USD file is available in the content browser at ``Isaac Sim/Samples/Rigging/Manipulator/import_manipulator/ur10e/ur_gains_tuner/ur.usda``.




.. Import the Robotiq 2F-140 Gripper
.. =====================================================

.. Use the URDF file provided by `ros-industrial-attic <https://github.com/ros-industrial-attic/robotiq/tree/kinetic-devel>`_. 
.. Even though this package is built for ROS1 and is deprecated, you can still adopt the URDF files and import the gripper for |isaac-sim|.

.. Convert XACRO to URDF
.. -----------------------

.. #. Download the Repository from `here <https://github.com/ros-industrial-attic/robotiq/tree/kinetic-devel>`_.

..    .. code-block:: bash

..       git clone https://github.com/ros-industrial-attic/robotiq.git

.. #. Navigate to the ``robotiq/robotiq_2f_140_gripper_visualization/urdf`` folder, open each xacro file. 

..    - Replace ``$(find robotiq_2f_140_gripper_visualization)`` with the relative path to the target file (for example, ``robotiq_arg2f_transimission.xacro``) from the current xacro file.

..       For example, in ``robotiq_arg2f_140_model.xacro``, replace:

..       .. code-block:: bash

..             <xacro:include filename="$(find robotiq_2f_140_gripper_visualization)/urdf/robotiq_arg2f_transmission.xacro" />

..       With:

..       .. code-block:: bash
     
..             <xacro:include filename="./robotiq_arg2f_transmission.xacro" />

..    - Replace ``package://`` with the relative path to the target file (for example, ``robotiq_arg2f_${stroke}_inner_finger.stl``) from the current xacro file.  

..       For example, in ``robotiq_arg2f_140_model.xacro``, replace:

..         .. code-block:: bash

..             <mesh filename="package://robotiq_2f_140_gripper_visualization/meshes/visual/robotiq_arg2f_${stroke}_inner_finger.stl" />

..       With:

..       .. code-block:: bash

..             <mesh filename="../meshes/visual/robotiq_arg2f_${stroke}_inner_finger.stl" />

.. #. Convert the xacro files to URDF format:

..    .. code-block:: bash

..       xacro robotiq_arg2f_140_model.xacro > robotiq_2f_140.urdf

..    If you encounter the error ``xacro: command not found``, install xacro for your configuration:

..    .. config-content::
..       :show-when: platform=Linux

..       .. code-block:: bash

..          sudo apt install ros-$ROS_DISTRO-xacro

..    .. config-content::
..       :show-when: platform=Windows,ros_distro=Jazzy

..       .. code-block:: bash

..          pixi add ros-$ROS_DISTRO-xacro

..    .. config-content::
..       :show-when: platform=Windows,ros_distro=Humble

..       .. attention::
..          ROS 2 Humble on Windows (Pixi) is not a supported configuration. Switch to ROS 2 Jazzy on Windows, or move to a Linux configuration, to follow this tutorial as written.


.. For reference, the resulting URDF files is available in the content browser at ``Isaac Sim/Samples/Rigging/Manipulator/import_manipulator/robotiq_2f_140_urdf/urdf/robotiq_2f_140.urdf``.


.. Import Robotiq 2F-140 Gripper into Isaac Sim
.. -----------------------------------------------

.. #. Go to Isaac Sim.
.. #. Let's create a new stage by going to **File** > **New**.
.. #. Navigate to **File** > **Import**.
.. #. Select the ``robotiq_2f_140.urdf`` file that you imported from the previous step.
.. #. In the import settings:

..    - For USD Output, navigate to your desktop using file browser and select **Desktop** this will be the output location of the gripper USD.
..    - For ``finger_joint``, set the Natural Frequency to ``300``.
..    - For the other joints of target ``Mimic``, set the Natural Frequency to ``2500``.

.. #. Click ``Import`` to complete the process.

..    .. image:: /images/isim_5.0_full_tut_gui_robotiq_importer.png
..       :width: 80%
..       :align: center
..       :alt: Gripper Import

.. For reference, the resulting USD file is available in the content browser at ``Isaac Sim/Samples/Rigging/Manipulator/import_manipulator/robotiq_2f_140/robotiq_2f_140.usd``.


2F-140 Gripper Parameters
============================

In the next section of the tutorial, we will be connecting the UR10e robot with the 2F-140 gripper. Let's review the expected parameters for the gripper joints.


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

Much like a real robot can have its tools changed for different tasks, simulated robots benefit from the same capability. This section outlines two methods to connect the UR10e robot with the Robotiq 2F-140 gripper

We will use the Robot Assembler to connect the UR10e robot with the 2F-140 gripper.

#. Open the UR10e USD file created from the last activity (``ur.usd``).
#. Drag and drop the ``robotiq_2f_140.usd`` file we created earlier into the stage.
#. Open the robot assembler by going to **Tools** > **Robotics** > **Asset Editor** > **Robot Assembler**.

   - In **Base Robot**, set **Select Base Robot** to ``/ur``, **Attach Point** to ``wrist_3_link``.
   - In **Attach Robot**, set **Select Attach Robot** to ``/ur/robotiq_2f_140``, **Attach Point** to ``robotiq_arg2f_base_link``.
   - Set **Assembly Namespace** to ``Gripper``.

#. Click **Begin Assembling Process** to start the process.

   .. image:: /images/isim_6.0_full_tut_gui_connect_gripper_assembler.png
      :width: 80%
      :align: center
      :alt: UR10e Assembler Connection


#. Adjust the attachment point orientation to make sure the end effector is attached to the gripper correctly. Rotate the gripper 90 degrees around the z-axis by clicking **Z +90**.

   .. image:: /images/isim_6.0_full_tut_gui_connect_gripper_assembler_2.png
      :width: 80%
      :align: center
      :alt: UR10e Assembler Connection 2

#. Click **Assemble and Simulate** to test the process.
#. Click **End Simulation And Finish** to complete the process.
#. Save the asset by going to **File** > **Save** or press **Ctrl+S**.

Run the Simulation
~~~~~~~~~~~~~~~~~~~~~~~~~

#. In the Stage panel, select the **ur** prim.
#. In the Property Editor at the bottom right, find the **Variants** section.
#. Beside **Gripper**, select **None** and the gripper will be removed from the robot.
#. Beside **Gripper**, select **robotiq_2f_140** and the gripper will be added to the robot.
#. Save the asset by going to **File** > **Save** or press **Ctrl+S**.

.. image:: /images/isim_6.0_full_tut_gui_variant_editor.webp
   :width: 80%
   :align: center
   :alt: UR10e Variant Editor


.. Note::

   The completed robotics arm asset with the gripper is available in the content browser at ``Isaac Sim/Samples/Rigging/Manipulator/import_manipulator/ur10e/ur_gripper/ur.usda``.


Summary
========

In this tutorial, you took the UR10e robot from Universal Robots and the 2F-140 gripper from Robotiq and imported them into |isaac-sim| from URDF files and connected them together under one articulation using the GUI and Robot Assembler.








