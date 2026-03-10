..
   Copyright (c) 2022-2026, NVIDIA CORPORATION. All rights reserved.
   NVIDIA CORPORATION and its licensors retain all intellectual property
   and proprietary rights in and to this software, related documentation
   and any modifications thereto. Any use, reproduction, disclosure or
   distribution of this software and related documentation without an express
   license agreement from NVIDIA CORPORATION is strictly prohibited.


.. _vision_msgs_package: https://github.com/ros-perception/vision_msgs/tree/ros2
.. _ackermann_msgs_package: https://github.com/ros-drivers/ackermann_msgs/tree/ros2

.. _isaac_sim_app_install_ros_other_platforms:


ROS 2 Installation (Other Platforms)
========================================================

|isaac-sim| provides a ROS 2 bridge for ROS system integration. The same set of common
components are used to define the types of data being published and received by the simulator.

The |isaac-sim_short| supported ROS distros are:

============== ======================== =============================================
Platform       ROS Distro                ROS Installation Notes
============== ======================== =============================================
Ubuntu 24.04    Jazzy (recommended)      See :ref:`isaac_sim_app_install_ros`

Ubuntu 22.04    Humble                   Use default installation (Python 3.10). 
                                         Use Python 3.12 build of ROS 2 Workspace to use custom ROS interfaces with Isaac Sim.

Ubuntu 22.04    Jazzy                    Build from source (Python 3.10). 
                                         Use Python 3.12 build of ROS 2 Workspace to use custom ROS interfaces with Isaac Sim.

Windows 10      Humble, Jazzy (Beta)     Use default installation in WSL. Custom ROS Interfaces are not supported.
                                     
Windows 11      Humble, Jazzy (Beta)     Use default installation in WSL. Custom ROS Interfaces are not supported.
============== ======================== =============================================

For the ROS 2 bridge, |isaac-sim_short| is compatible with **ROS 2 Humble** and **ROS 2 Jazzy**.

.. attention:: **Experimental: Native ROS 2 Distro Support** -- |isaac-sim_short| now experimentally supports loading any ROS 2 distro that is natively installed on your platform (Ubuntu 22.04 or Ubuntu 24.04). To use this, source your locally installed ROS 2 distro and launch |isaac-sim_short| from the same terminal. While Humble and Jazzy remain the officially tested and recommended distros, other natively supported distros may work with this workflow.

ROS 2 Jazzy on Ubuntu 24.04 is recommended. Refer to :ref:`isaac_sim_app_install_ros`, if that is your mode of installation. Otherwise, verify or choose your configuration to continue:

.. config-selector::
   :options: platform=Ubuntu 22.04|Windows,ros_distro=Humble|Jazzy,package_type=Default ROS Interfaces|Custom ROS Interfaces


.. _isaac_sim_app_install_ros_options_other_platforms:

Install ROS 2
===========================================

.. config-content::
   :show-when: platform=Ubuntu 22.04,ros_distro=Humble

   #. Download ROS 2 following the instructions on the official website:

      - `ROS 2 Humble Ubuntu 22.04 <https://docs.ros.org/en/humble/Installation/Ubuntu-Install-Debians.html>`_

   #. (Optional) Some message types (Detection2DArray and Detection3DArray used for publishing bounding boxes) in the ROS 2 Bridge depend on the `vision_msgs_package`_. Run the command below to install the package on your system. If you have built ROS 2 from source, clone the package and include it in your ROS 2 installation workspace before re-building. If you don't need to run the ``vision_msgs`` publishers, you can skip this step.

      .. code-block::

         sudo apt install ros-humble-vision-msgs

   #. (Optional) Some message types (``AckermannDriveStamped`` used for publishing and subscribing to Ackermann steering commands) in the ROS 2 Bridge depend on the `ackermann_msgs_package`_. Run the command below to install the package on your system. If you have built ROS 2 from source, clone the package and include it in your ROS 2 installation workspace before re-building. If you don't need to run the ``ackermann_msgs`` publishers or subscribers, you can skip this step.

      .. code-block::

         sudo apt install ros-humble-ackermann-msgs

   #. Ensure that the ROS environment is sourced in the terminal or in your ``~/.bashrc`` file. You must perform this step each time and before using any ROS commands:

      .. code-block::

         source /opt/ros/humble/setup.bash
   
   .. note:: For Linux, you can not source this installation in the same terminal as running |isaac-sim_short|. Source with |isaac-sim_short| internal ROS libraries, Python 3.12, before running |isaac-sim_short|. 


.. config-content::
   :show-when: platform=Ubuntu 22.04,ros_distro=Jazzy

   #. Download and build ROS 2 Jazzy from source following the instructions on the official website:

      - `ROS 2 Jazzy Ubuntu 22.04 <https://docs.ros.org/en/jazzy/Installation/Alternatives/Ubuntu-Development-Setup.html>`_

   #. (Optional) Some message types (``Detection2DArray`` and ``Detection3DArray``, which are used for publishing bounding boxes) in the ROS 2 Bridge depend on the `vision_msgs_package`_. Clone the linked repository and build it in a ROS workspace. If you don't need to run the ``vision_msgs`` publishers, you can skip this step.

   #. (Optional) Clone the linked repository and build it in a ROS workspace. If you have built ROS 2 from source, clone the package and include it in your ROS 2 installation workspace before re-building. If you don't need to run the ``ackermann_msgs`` publishers or subscribers, you can skip this step. Some message types (``AckermannDriveStamped`` used for publishing and subscribing to Ackermann steering commands) in the ROS 2 Bridge depend on the `ackermann_msgs_package`_. 

   #. Ensure that the ROS environment is sourced in the terminal or in your ``~/.bashrc`` file. You must perform this step each time and before using any ROS commands:

      .. code-block::

         . ~/ros2_jazzy/install/local_setup.bash
   
   .. note:: For Linux, you can not source this installation in the same terminal as running |isaac-sim_short|. Source with |isaac-sim_short| internal ROS libraries, Python 3.12, before running |isaac-sim_short|. 


.. config-content::
   :show-when: platform=Windows,ros_distro=Humble
   
   Use WSL2 to run ROS 2 on Windows, which communicates with the |isaac-sim_short| ROS Bridge run using internal ROS 2 libraries.

   #.  Install `WSL2 <https://learn.microsoft.com/en-us/windows/wsl/>`_ on your Windows machine.

   #. Open Powershell with Admin privileges and change the WSL version to 2.

      .. code-block::

         wsl --set-default-version 2

   #. Install Ubuntu 22.04 distro inside WSL.

      .. code-block::

         wsl --install -d Ubuntu-22.04

   #. After the installation is complete, restart the machine and open the Ubuntu 22.04 app in Windows. It takes a few moments to install.

      .. note:: If you encounter errors with enabling virtualization, follow the `Windows virtualization enabling instructions <https://support.microsoft.com/en-us/windows/enable-virtualization-on-windows-11-pcs-c5578302-6e43-4b4b-a449-8ced115f58e1>`_.

   #. After Ubuntu 22.04 is installed in WSL2, download ROS 2 following the instructions on the official website:

      - `ROS 2 Humble Ubuntu 22.04 <https://docs.ros.org/en/humble/Installation/Ubuntu-Install-Debians.html>`_

   #. (Optional) Some message types (``Detection2DArray`` and ``Detection3DArray``, which are used for publishing bounding boxes) in the ROS 2 Bridge depend on the `vision_msgs_package`_. Run the command below to install the package on your system. If you have built ROS 2 from source, clone the package and include it in your ROS 2 installation workspace before re-building. If you don't need to run the ``vision_msgs`` publishers, you can skip this step.

      .. code-block::

         sudo apt install ros-humble-vision-msgs

   #. (Optional) Some message types (``AckermannDriveStamped`` used for publishing and subscribing to Ackermann steering commands) in the ROS 2 Bridge depend on the `ackermann_msgs_package`_. Run the command below to install the package on your system. If you have built ROS 2 from source, clone the package and include it in your ROS 2 installation workspace before re-building. If you don't need to run the ``ackermann_msgs`` publishers or subscribers, you can skip this step.

      .. code-block::

         sudo apt install ros-humble-ackermann-msgs

   #. Ensure that the ROS environment is sourced in the terminal or in your WSL2 ``~/.bashrc`` file. You must perform this step each time and before using any ROS commands: 

      .. code-block::

         source /opt/ros/humble/setup.bash

   #. After ROS 2 installation is complete, open WSL2 and run the following command to get the IP address of WSL2:

      .. code-block::

         hostname -I

   #. Open Powershell as Admin and run the following command to retrieve the IPv4 address of the Windows host:

      .. code-block::

         ipconfig /all

   #. Set the variables in Powershell according to the respective IP addresses:

      .. code-block::

         $Windows_IP = "<WINDOWS_IP>"
         $WSL2_IP = "<WSL2_IP>"

   #. Setup port forwarding in Powershell for the specific ports used by default DDS (FastDDS) in ROS:

      .. code-block::

         netsh interface portproxy add v4tov4 listenport=7400 listenaddress=$Windows_IP connectport=7400 connectaddress=$WSL2_IP
         netsh interface portproxy add v4tov4 listenport=7410 listenaddress=$Windows_IP connectport=7410 connectaddress=$WSL2_IP
         netsh interface portproxy add v4tov4 listenport=9387 listenaddress=$Windows_IP connectport=9387 connectaddress=$WSL2_IP

   
   After the ROS Bridge is enabled on |isaac-sim_short| and the Windows network settings have been applied, |isaac-sim_short| is able to communicate with ROS 2 nodes in WSL2.

.. config-content::
   :show-when: platform=Windows,ros_distro=Jazzy
   
   Use WSL2 to run ROS 2 on Windows, which communicates with the |isaac-sim_short| ROS Bridge run using internal ROS 2 libraries.

   #.  Install `WSL2 <https://learn.microsoft.com/en-us/windows/wsl/>`_ on your Windows machine.

   #. Open Powershell with Admin privileges and change the WSL version to 2.

      .. code-block::

         wsl --set-default-version 2

   #. Install Ubuntu 24.04 distro inside WSL.

      .. code-block::

         wsl --install -d Ubuntu-24.04

   #. After the installation is complete, restart the machine and open the Ubuntu 24.04 app in Windows. It takes a few moments to install.

      .. note:: If you encounter errors with enabling virtualization, follow the `Windows virtualization enabling instructions <https://support.microsoft.com/en-us/windows/enable-virtualization-on-windows-11-pcs-c5578302-6e43-4b4b-a449-8ced115f58e1>`_.

   #. After Ubuntu 24.04 is installed in WSL2, download ROS 2 following the instructions on the official website:

      - `ROS 2 Jazzy Ubuntu 24.04 <https://docs.ros.org/en/jazzy/Installation/Ubuntu-Install-Debians.html>`_

   #. (Optional) Some message types (``Detection2DArray`` and ``Detection3DArray``, which are used for publishing bounding boxes) in the ROS 2 Bridge depend on the `vision_msgs_package`_. Run the command below to install the package on your system. If you have built ROS 2 from source, clone the package and include it in your ROS 2 installation workspace before re-building. If you don't need to run the ``vision_msgs`` publishers, you can skip this step.

      .. code-block::

         sudo apt install ros-jazzy-vision-msgs

   #. (Optional) Some message types (``AckermannDriveStamped`` used for publishing and subscribing to Ackermann steering commands) in the ROS 2 Bridge depend on the `ackermann_msgs_package`_. Run the command below to install the package on your system. If you have built ROS 2 from source, clone the package and include it in your ROS 2 installation workspace before re-building. If you don't need to run the ``ackermann_msgs`` publishers or subscribers, you can skip this step.

      .. code-block::

         sudo apt install ros-jazzy-ackermann-msgs

   #. Ensure that the ROS environment is sourced in the terminal or in your WSL2 ``~/.bashrc`` file. You must perform this step each time and before using any ROS commands: 

      .. code-block::

         source /opt/ros/jazzy/setup.bash

   #. After ROS 2 installation is complete, open WSL2 and run the following command to get the IP address of WSL2:

      .. code-block::

         hostname -I

   #. Open Powershell as Admin and run the following command to retrieve the IPv4 address of the Windows host:

      .. code-block::

         ipconfig /all

   #. Set the variables in Powershell according to the respective IP addresses:

      .. code-block::

         $Windows_IP = "<WINDOWS_IP>"
         $WSL2_IP = "<WSL2_IP>"

   #. Setup port forwarding in Powershell for the specific ports used by default DDS (FastDDS) in ROS:

      .. code-block::

         netsh interface portproxy add v4tov4 listenport=7400 listenaddress=$Windows_IP connectport=7400 connectaddress=$WSL2_IP
         netsh interface portproxy add v4tov4 listenport=7410 listenaddress=$Windows_IP connectport=7410 connectaddress=$WSL2_IP
         netsh interface portproxy add v4tov4 listenport=9387 listenaddress=$Windows_IP connectport=9387 connectaddress=$WSL2_IP

   
   After the ROS Bridge is enabled on |isaac-sim_short| and the Windows network settings have been applied, |isaac-sim_short| is able to communicate with ROS 2 nodes in WSL2.



To install the ROS 2 workspaces and run our tutorials, follow the steps in the :ref:`isaac_sim_ros_workspace_other_platforms` section.


.. _isaac_sim_ros_workspace_other_platforms:
   
Isaac Sim ROS Workspaces
============================

The ROS 2 workspaces contain the necessary packages to run our ROS 2 tutorials and examples.

.. _isaac_included_ros_packages_other_platforms:

Included ROS 2 Packages
^^^^^^^^^^^^^^^^^^^^^^^^^^

A list of sample ROS 2 packages created for |isaac-sim|:

    - **carter_navigation**: Contains the required launch file and ROS 2 navigation parameters for the NVIDIA Carter robot.
    - **cmdvel_to_ackermann**: Contains a script file and launch file used to convert command velocity messages (Twist message type) to Ackermann Drive messages (``AckermannDriveStamped`` message type).
    - **custom_message**: Contains the required launch file and ROS 2 navigation parameters for the NVIDIA Carter robot.
    - **h1_fullbody_controller**: Contains the required launch files, parameters and scripts for running a full body controller for the H1 humanoid robot.
    - **isaac_compressed_image_decoder**: Contains a decoder node for converting H.264 compressed images (``sensor_msgs/CompressedImage``) back to raw ``sensor_msgs/Image`` messages using `PyAV <https://pyav.org/>`_.
    - **isaac_moveit**: Contains the launch files and parameter to run |isaac-sim_short| with the MoveIt2 stack.
    - **isaac_ros_navigation_goal**: Used to automatically set random or user-defined goal poses in ROS 2 Navigation.
    - **isaac_ros2_messages**: A custom set of ROS 2 service interfaces for retrieving poses as well as listing prims and manipulate their attributes.
    - **isaacsim**: Contains launch files and scripts for running and launching Isaac Sim as a ROS 2 node.
    - **isaac_tutorials**: Contains launch files, RViz2 config files, and scripts for the tutorial series.
    - **iw_hub_navigation**: Contains the required launch file and ROS 2 navigation parameters for the iw.hub robot.


.. _isaac_sim_ros_workspace_setup_other_platforms:

Setup ROS 2 Workspaces
^^^^^^^^^^^^^^^^^^^^^^^^^


.. config-content::
   :show-when: platform=Ubuntu 22.04,ros_distro=Humble

   To run our ROS 2 tutorials and examples, you must source your ROS 2 installation workspace in the terminal you plan to work in.

   #. To build the |isaac-sim_short| ROS workspaces, ensure you have followed :ref:`isaac_sim_app_install_ros_options_other_platforms`. 

      .. important:: You are also able to build the workspaces using a ROS Docker container, as described in :ref:`isaac_ros_docker_other_platforms`. Return to this step after setting up your Docker container.
      
   #. Clone the |isaac-sim_short| ROS Workspace Repository from `<https://github.com/isaac-sim/IsaacSim-ros_workspaces>`_.

      A few ROS packages are necessary for the |isaac-sim_short| ROS 2 tutorial series. The entire ROS 2 workspaces are included with the necessary packages.

   #. If you have built ROS 2 from source, replace the ``source /opt/ros/<ros_distro>/setup.bash`` command with ``source <path_ros2_ws>/install/setup.bash`` before building additional workspaces.

               
   #. To build the ROS 2 workspace, you might need to install additional packages:

      .. code-block:: bash

         # For rosdep install command
         sudo apt install python3-rosdep build-essential
         # For colcon build command
         sudo apt install python3-colcon-common-extensions

   #. Ensure that your native ROS 2 has been sourced:

      .. code-block:: bash

         source /opt/ros/humble/setup.bash

   #. Resolve any package dependencies from the root of the ROS 2 workspace by running the following command:

      .. code-block:: bash

         cd humble_ws
         git submodule update --init --recursive # If using docker, perform this step outside the container and relaunch the container
         rosdep install -i --from-path src --rosdistro humble -y

   #. Build the workspace:

      .. code-block:: bash

         colcon build

      Under the root directory, new ``build``, ``install``, and ``log`` directories are created.

   #. To start using the ROS 2 packages built within this workspace, open a new terminal and source the workspace with the following commands:

      .. code-block:: bash

         source /opt/ros/humble/setup.bash
         cd humble_ws
         source install/local_setup.bash
 
   .. config-content:: 
      :show-when: package_type=Custom ROS Interfaces

      **Custom ROS Interfaces**
      
      If you want to use ``rclpy`` and custom ROS 2 packages with |isaac-sim_short|, your ROS 2 workspace must also be built with Python 3.12 which Isaac Sim will interface. Dockerfiles are included with the `Isaac Sim ROS Workspaces repository <https://github.com/isaac-sim/IsaacSim-ros_workspaces>`_ that build minimal dependencies of ROS 2 with Python 3.12.


      Additionally, Dockerfiles are included to build the ROS 2 workspace with Python 3.12. Packages built using this Dockerfile can be used directly with ``rclpy`` and can be sourced to run the |isaac-sim_short| ROS 2 Bridge. 

      #. To use the Dockerfile to build ROS 2 and the workspace with Python 3.12:

         .. code-block:: bash

               cd IsaacSim-ros_workspaces

               ./build_ros.sh -d humble -v 22.04

         The minimal ``humble_ws`` needed to run |isaac-sim_short| is under `build_ws/humble/humble_ws`. Additional workspaces can also be created and built in this Dockerfile.

      #. Open a new terminal and source the ROS 2 Python 3.12 build:

         .. code-block:: bash

               source build_ws/humble/humble_ws/install/local_setup.bash

      #. In the same terminal, source the built ROS 2 workspace:

         .. code-block:: bash

               source build_ws/humble/isaac_sim_ros_ws/install/local_setup.bash 

      #. Run |isaac-sim_short| from the same terminal. The sourced workspace contains the minimal ROS 2 Humble dependencies needed to enable the ROS 2 bridge.

      #. To run external nodes, use a different terminal and source the Python 3.10 build of the workspace in the default ROS distro as explained at the beginning of this section. 


.. config-content::
   :show-when: platform=Ubuntu 22.04,ros_distro=Jazzy

   Since ROS 2 Jazzy is not natively supported on Ubuntu 22.04, Docker is required to build the ROS 2 workspaces.

   #. Clone the |isaac-sim_short| ROS Workspace Repository from `<https://github.com/isaac-sim/IsaacSim-ros_workspaces>`_.

      A few ROS packages are necessary for the |isaac-sim_short| ROS 2 tutorial series. The entire ROS 2 workspaces are included with the necessary packages.

   #. Follow the instructions in :ref:`isaac_ros_docker_other_platforms` to build and source the workspace using a ROS Docker container.

   .. config-content:: 
      :show-when: package_type=Custom ROS Interfaces

      **Custom ROS Interfaces**
      
      If you want to use ``rclpy`` and custom ROS 2 packages with |isaac-sim_short|, your ROS 2 workspace must also be built with Python 3.12 which Isaac Sim will interface. Dockerfiles are included with the `Isaac Sim ROS Workspaces repository <https://github.com/isaac-sim/IsaacSim-ros_workspaces>`_ that build minimal dependencies of ROS 2 with Python 3.12.

      Packages built using this Dockerfile can be used directly with ``rclpy`` and can be sourced to run the |isaac-sim_short| ROS 2 Bridge.

      #. To use the Dockerfile to build ROS 2 and the workspace with Python 3.12:

         .. code-block:: bash

            cd IsaacSim-ros_workspaces

            ./build_ros.sh -d jazzy -v 22.04

         The minimal ``jazzy_ws`` needed to run |isaac-sim_short| is under `build_ws/jazzy/jazzy_ws`. Additional workspaces can also be created and built in this Dockerfile.

      #. Open a new terminal and source the ROS 2 Python 3.12 build:

         .. code-block:: bash

               source build_ws/jazzy/jazzy_ws/install/local_setup.bash

      #. In the same terminal, source the built ROS 2 workspace:

         .. code-block:: bash

               source build_ws/jazzy/isaac_sim_ros_ws/install/local_setup.bash 

      #. Run |isaac-sim_short| from the same terminal. The sourced workspace contains the minimal ROS 2 Jazzy dependencies needed to enable the ROS 2 bridge.

      #. To run external nodes, use the Docker container as described in :ref:`isaac_ros_docker_other_platforms`.

.. config-content::
   :show-when: platform=Windows,ros_distro=Humble

   To run our ROS 2 tutorials and examples, it's necessary to source your ROS 2 installation workspace in the WSL2 terminal you plan to work in.

   #. Open the Ubuntu 22.04 app (WSL2) in Windows and wait for the WSL2 terminal to be available.

   #. To build the |isaac-sim_short| ROS workspaces, ensure you have followed :ref:`isaac_sim_app_install_ros_options_other_platforms` in WSL2. 
      
   #. Clone the |isaac-sim_short| ROS Workspace Repository from `<https://github.com/isaac-sim/IsaacSim-ros_workspaces>`_.

      A few ROS packages are needed to go through the |isaac-sim_short| ROS 2 tutorial series. The entire ROS 2 workspaces are included with the necessary packages.

   #. If you have built ROS 2 from source, replace the ``source /opt/ros/<ros_distro>/setup.bash`` command with ``source <path_ros2_ws>/install/setup.bash`` before building additional workspaces.

               
   #. To build the ROS 2 workspace, you might need to install additional packages:

      .. code-block:: bash

         # For rosdep install command
         sudo apt install python3-rosdep build-essential
         # For colcon build command
         sudo apt install python3-colcon-common-extensions

   #. Ensure that your native ROS 2 has been sourced:

      .. code-block:: bash

         source /opt/ros/humble/setup.bash

   #. Resolve any package dependencies from the root of the ROS 2 workspace by running the following commands:

      .. code-block:: bash

         cd humble_ws
         git submodule update --init --recursive # If using Docker, perform this step outside the container and relaunch the container
         rosdep install -i --from-path src --rosdistro humble -y

   #. Build the workspace:

      .. code-block:: bash

         colcon build

      Under the root directory, new ``build``, ``install``, and ``log`` directories are created.

   #. To start using the ROS 2 packages built within this workspace, open a new terminal and source the workspace with the following commands:

      .. code-block:: bash

         source /opt/ros/humble/setup.bash
         cd humble_ws
         source install/local_setup.bash

.. config-content::
   :show-when: platform=Windows,ros_distro=Jazzy

   To run our ROS 2 tutorials and examples, it's necessary to source your ROS 2 installation workspace in the WSL2 terminal you plan to work in.

   #. Open the Ubuntu 24.04 app (WSL2) in Windows and wait for the WSL2 terminal to be available.

   #. To build the |isaac-sim_short| ROS workspaces, ensure you have followed :ref:`isaac_sim_app_install_ros_options_other_platforms` in WSL2. 
      
   #. Clone the |isaac-sim_short| ROS Workspace Repository from `<https://github.com/isaac-sim/IsaacSim-ros_workspaces>`_.

      A few ROS packages are needed to go through the |isaac-sim_short| ROS 2 tutorial series. The entire ROS 2 workspaces are included with the necessary packages.

   #. If you have built ROS 2 from source, replace the ``source /opt/ros/<ros_distro>/setup.bash`` command with ``source <path_ros2_ws>/install/setup.bash`` before building additional workspaces.

               
   #. To build the ROS 2 workspace, you might need to install additional packages:

      .. code-block:: bash

         # For rosdep install command
         sudo apt install python3-rosdep build-essential
         # For colcon build command
         sudo apt install python3-colcon-common-extensions

   #. Ensure that your native ROS 2 has been sourced:

      .. code-block:: bash

         source /opt/ros/jazzy/setup.bash

   #. Resolve any package dependencies from the root of the ROS 2 workspace by running the following command:

      .. code-block:: bash

         cd jazzy_ws
         git submodule update --init --recursive # If using docker, perform this step outside the container and relaunch the container
         rosdep install -i --from-path src --rosdistro jazzy -y

   #. Build the workspace:

      .. code-block:: bash

         colcon build

      Under the root directory, new ``build``, ``install``, and ``log`` directories are created.

   #. To start using the ROS 2 packages built within this workspace, open a new terminal and source the workspace with the following commands:

      .. code-block:: bash

         source /opt/ros/jazzy/setup.bash
         cd jazzy_ws
         source install/local_setup.bash


.. _isaac_sim_app_no_system_installed_ros_other_platforms:

Configuring Options and Enabling Internal ROS Libraries
==================================================================

.. config-content::
   :show-when: platform=Ubuntu 22.04,ros_distro=Humble

   .. config-content::
      :show-when: package_type=Custom ROS Interfaces

      Because you are already sourcing the Python 3.12 build of ROS 2 and the Python 3.12 build of your ROS 2 workspace, you would not need to enable the internal ROS 2 libraries that ship with Isaac Sim. 

   .. config-content::
      :show-when: package_type=Default ROS Interfaces

      If you meet the following configurations, you must run Isaac Sim with the internal ROS libraries that ship with |isaac-sim_short|:
      
      - Need to use ROS Docker containers
      - Have a ROS 2 workspace built locally, but you only plan on using default or command ROS interfaces (for example, ``std_msgs``, ``geometry_msgs``, ``nav_msgs``)

      In Ubuntu 22.04, |isaac-sim_short| interactive GUI automatically loads the **internal ROS 2 Humble** libraries if no other ROS libraries are sourced. Use the regular launch command to run |isaac-sim_short| with the ROS 2 Bridge enabled. 

      .. code-block:: bash

         ./isaac-sim.sh

      .. note:: The ``ROS_DISTRO`` environment variable is used to check whether ROS has been sourced. 
      
      **Running Standalone Scripts**

      If you are using ``./python.sh`` to run standalone Isaac Sim scripts, you must manually enable the internal ``libs``.

      To directly set a specific internal ROS 2 library, you must set the following environment variables in a new terminal or command prompt before running |isaac-sim_short|. If |isaac-sim_short| is installed in a non-default location, replace ``isaac_sim_package_path`` environment variable with the path to your Isaac Sim installation root folder.
            
      - For running Standalone Scripts:

         .. code-block:: bash

            export isaac_sim_package_path=$HOME/isaacsim

            export ROS_DISTRO=humble

            export RMW_IMPLEMENTATION=rmw_fastrtps_cpp

            # Can only be set once per terminal.
            # Setting this command multiple times will append the internal library path again potentially leading to conflicts
            export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:$isaac_sim_package_path/exts/isaacsim.ros2.core/humble/lib

            # Run Isaac Sim Standalone scripts
            $isaac_sim_package_path/python.sh <path/to/standalone/script>
            

.. config-content::
   :show-when: platform=Ubuntu 22.04,ros_distro=Jazzy

   .. config-content::
      :show-when: package_type=Custom ROS Interfaces

      Because you are already sourcing the Python 3.12 build of ROS 2 and the Python 3.12 build of your ROS 2 workspace, you do not need to enable the internal ROS 2 libraries that ship with Isaac Sim. 

   .. config-content::
      :show-when: package_type=Default ROS Interfaces

      If you meet the following configuration, you must run Isaac Sim with the internal ROS libraries that ship with |isaac-sim_short|.
      
      - Need to use ROS Docker containers
      - Have a ROS 2 workspace built locally, but you only plan on using default or command ROS interfaces (for example, ``std_msgs``, ``geometry_msgs``, ``nav_msgs``).

      In Ubuntu 22.04, the |isaac-sim_short| interactive GUI automatically loads the **internal ROS 2 Humble** libraries, if no other ROS libraries are sourced. Therefore, you must manually override that setting to use Jazzy internal ROS 2 libs.

      .. note:: The ``ROS_DISTRO`` environment variable is used to check whether ROS has been sourced. 
      
      **Running Standalone Scripts or Manually Specify ROS 2 Internal Libraries**

      If you are using ``./python.sh`` to run standalone Isaac Sim scripts, you must manually enable the internal libs. 

      To directly set a specific internal ROS 2 library, you must set the following environment variables in a new terminal or command prompt before running |isaac-sim_short|. If |isaac-sim_short| is installed in a non-default location, replace ``isaac_sim_package_path`` environment variable with the path to your Isaac Sim installation root folder.

      - To run Isaac Sim using manually selected ROS 2 internal libraries (override to Jazzy):

         .. code-block:: bash

            export isaac_sim_package_path=$HOME/isaacsim

            export ROS_DISTRO=jazzy

            export RMW_IMPLEMENTATION=rmw_fastrtps_cpp

            # Can only be set once per terminal.
            # Setting this command multiple times will append the internal library path again potentially leading to conflicts
            export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:$isaac_sim_package_path/exts/isaacsim.ros2.core/jazzy/lib

            # Run Isaac Sim Standalone scripts
            $isaac_sim_package_path/isaac-sim.sh
            
      - To run using standalone scripts:

         .. code-block:: bash

            export isaac_sim_package_path=$HOME/isaacsim

            export ROS_DISTRO=jazzy

            export RMW_IMPLEMENTATION=rmw_fastrtps_cpp

            # Can only be set once per terminal.
            # Setting this command multiple times will append the internal library path again potentially leading to conflicts
            export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:$isaac_sim_package_path/exts/isaacsim.ros2.core/jazzy/lib

            # Run Isaac Sim Standalone scripts
            $isaac_sim_package_path/python.sh <path/to/standalone/script>

.. config-content::
   :show-when: platform=Windows,ros_distro=Humble

   In Windows, |isaac-sim_short| automatically loads the **internal ROS 2 Humble** libraries, if no other ROS libraries are sourced. Enable the ROS 2 Bridge and run |isaac-sim_short| using: 

   .. tab-set::
                    
      .. tab-item:: CMD Prompt

         .. code-block:: winbatch

            set isaac_sim_package_path=C:\isaacsim

            REM Run Isaac Sim with ROS 2 Bridge Enabled
            %isaac_sim_package_path%\isaac-sim.bat --/isaac/startup/ros_bridge_extension=isaacsim.ros2.bridge

      .. tab-item:: Powershell

         .. code-block:: winbatch

            # Set environment variables
            
            $env:isaac_sim_package_path = "C:\isaacsim"

            # Run Isaac Sim with ROS 2 Bridge Enabled
            & "$env:isaac_sim_package_path\isaac-sim.bat" --/isaac/startup/ros_bridge_extension=isaacsim.ros2.bridge

   **Running Standalone Scripts**

   If you are using ``./python.bat`` to run standalone Isaac Sim scripts, you must manually enable the internal ``libs``.

   .. tab-set::
                    
      .. tab-item:: CMD Prompt

         .. code-block:: winbatch

            set isaac_sim_package_path=C:\isaacsim

            set ROS_DISTRO=humble
                        
            set RMW_IMPLEMENTATION=rmw_fastrtps_cpp

            REM Can only be set once per terminal.
            REM Setting this command multiple times will append the internal library path again potentially leading to conflicts
            set PATH=%PATH%;%isaac_sim_package_path%\exts\isaacsim.ros2.core\humble\lib

            REM Run Isaac Sim Standalone scripts
            %isaac_sim_package_path%\python.bat <path/to/standalone/script>

      .. tab-item:: Powershell

         .. code-block:: winbatch

            # Set environment variables
            
            $env:isaac_sim_package_path = "C:\isaacsim"
            $env:ROS_DISTRO = "humble"
            $env:RMW_IMPLEMENTATION = "rmw_fastrtps_cpp"

            # Only set this once per session to avoid path conflicts
            $env:PATH = "$env:PATH;$env:isaac_sim_package_path\exts\isaacsim.ros2.core\humble\lib"

            # Run Run Isaac Sim Standalone scripts
            & "$env:isaac_sim_package_path\python.bat" <path/to/standalone/script>

.. config-content::
   :show-when: platform=Windows,ros_distro=Jazzy

   In Windows, |isaac-sim_short| automatically loads the **internal ROS 2 Humble** libraries, if no other ROS libraries are sourced. To manually override that setting to enable Jazzy internal ROS 2 libs, enable the ROS 2 Bridge and run |isaac-sim_short| using: 

   
   .. tab-set::
                    
      .. tab-item:: CMD Prompt

         .. code-block:: winbatch

            set isaac_sim_package_path=C:\isaacsim

            set ROS_DISTRO=jazzy
                        
            set RMW_IMPLEMENTATION=rmw_fastrtps_cpp

            REM Can only be set once per terminal.
            REM Setting this command multiple times will append the internal library path again potentially leading to conflicts
            set PATH=%PATH%;%isaac_sim_package_path%\exts\isaacsim.ros2.core\jazzy\lib

            REM Run Isaac Sim with ROS 2 Bridge Enabled
            %isaac_sim_package_path%\isaac-sim.bat --/isaac/startup/ros_bridge_extension=isaacsim.ros2.bridge

      .. tab-item:: Powershell

         .. code-block:: winbatch

            # Set environment variables
            
            $env:isaac_sim_package_path = "C:\isaacsim"
            $env:ROS_DISTRO = "jazzy"
            $env:RMW_IMPLEMENTATION = "rmw_fastrtps_cpp"

            # Only set this once per session to avoid path conflicts
            $env:PATH = "$env:PATH;$env:isaac_sim_package_path\exts\isaacsim.ros2.core\jazzy\lib"

            # Run Isaac Sim with ROS 2 Bridge Enabled
            & "$env:isaac_sim_package_path\isaac-sim.bat" --/isaac/startup/ros_bridge_extension=isaacsim.ros2.bridge

   **Running Standalone Scripts**

   If you are using ``./python.bat`` to run standalone Isaac Sim scripts, you must manually enable the internal ``libs``.

   .. tab-set::
                    
      .. tab-item:: CMD Prompt

         .. code-block:: winbatch

            set isaac_sim_package_path=C:\isaacsim

            set ROS_DISTRO=jazzy
                        
            set RMW_IMPLEMENTATION=rmw_fastrtps_cpp

            REM Can only be set once per terminal.
            REM Setting this command multiple times will append the internal library path again potentially leading to conflicts
            set PATH=%PATH%;%isaac_sim_package_path%\exts\isaacsim.ros2.core\jazzy\lib

            REM Run Isaac Sim Standalone scripts
            %isaac_sim_package_path%\python.bat <path/to/standalone/script>

      .. tab-item:: Powershell

         .. code-block:: winbatch

            # Set environment variables
            
            $env:isaac_sim_package_path = "C:\isaacsim"
            $env:ROS_DISTRO = "jazzy"
            $env:RMW_IMPLEMENTATION = "rmw_fastrtps_cpp"

            # Only set this once per session to avoid path conflicts
            $env:PATH = "$env:PATH;$env:isaac_sim_package_path\exts\isaacsim.ros2.core\jazzy\lib"

            # Run Run Isaac Sim Standalone scripts
            & "$env:isaac_sim_package_path\python.bat" <path/to/standalone/script>

Enabling the ROS 2 Bridge 
==========================

The instructions :ref:`isaac_sim_app_enable_ros_other_platforms` are the recommended way to enable the ROS 2 bridge. 

You can alternatively enable:

* :ref:`isaac_sim_app_install_cyclonedds_other_platforms`. 
* :ref:`isaac_sim_app_install_zenoh_other_platforms`. 

.. _isaac_sim_app_enable_ros_other_platforms:   

Enabling the ROS 2 Bridge using Fast DDS
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. config-content::
   :show-when: platform=Ubuntu 22.04

   .. tab-set::
      
      .. tab-item:: Single Machine
         
         If using the ROS 2 Bridge to communicate with ROS 2 nodes running on the same machine, use the default configuration of FastDDS. This ensures you are using shared memory transport resulting in the best simulation performance.
      
      .. tab-item:: Multiple Machines or Docker

         If you intend to use the ROS 2 bridge to connect to ROS nodes on different machines on the same network, before launching |isaac-sim_short|, you need to set the Fast DDS middleware on **all terminals** that will be passing ROS 2 messages and enable UDP transport:

         #. Ensure ``fastdds.xml`` exists and that environment variables are set:

            * If you followed :ref:`isaac_sim_ros_workspace_setup_other_platforms`, a ``fastdds.xml`` file is located at the root of the <ros2_ws> folder. Set the environment variable by typing ``export FASTRTPS_DEFAULT_PROFILES_FILE=<path_to_ros2_ws>/fastdds.xml`` in all the terminals that will use ROS 2 functions.
            
            * If you DID NOT follow :ref:`isaac_sim_ros_workspace_setup_other_platforms`, create a file named ``fastdds.xml`` under ``~/.ros/``, paste the following snippet link into the file:

                  .. code-block:: bash

                     <?xml version="1.0" encoding="UTF-8" ?>

                     <license>Copyright (c) 2022-2026, NVIDIA CORPORATION.  All rights reserved.
                     NVIDIA CORPORATION and its licensors retain all intellectual property
                     and proprietary rights in and to this software, related documentation
                     and any modifications thereto.  Any use, reproduction, disclosure or
                     distribution of this software and related documentation without an express
                     license agreement from NVIDIA CORPORATION is strictly prohibited.</license>


                     <profiles xmlns="http://www.eprosima.com/XMLSchemas/fastRTPS_Profiles" >
                        <transport_descriptors>
                              <transport_descriptor>
                                 <transport_id>UdpTransport</transport_id>
                                 <type>UDPv4</type>
                              </transport_descriptor>
                        </transport_descriptors>

                        <participant profile_name="udp_transport_profile" is_default_profile="true">
                              <rtps>
                                 <userTransports>
                                    <transport_id>UdpTransport</transport_id>
                                 </userTransports>
                                 <useBuiltinTransports>false</useBuiltinTransports>
                              </rtps>
                        </participant>
                     </profiles>


         #. Run ``export FASTRTPS_DEFAULT_PROFILES_FILE=~/.ros/fastdds.xml`` in the terminals that will use ROS 2 functions.
         #. (Optional) Run ``export ROS_DOMAIN_ID=(id_number)`` before launching |isaac-sim_short|. Later you can decide whether to use this ``ROS_DOMAIN_ID`` inside your environment, or explicitly use a different ID number for any given topic.
         #. Source your ROS 2 installation or internal ROS 2 libraries and workspace before launching |isaac-sim_short|.

.. config-content::
   :show-when: platform=Windows

   To use the ROS 2 bridge to connect to ROS nodes in WSL2, you must set the Fast DDS middleware on **all terminals** that will be passing ROS 2 messages and enable UDP transport:

   
   #. If you DID NOT follow :ref:`isaac_sim_ros_workspace_setup_other_platforms`, create a file named ``fastdds.xml`` under ``C:\.ros\``, paste the following snippet link into the file:

         .. code-block:: bash

            <?xml version="1.0" encoding="UTF-8" ?>

            <license>Copyright (c) 2022-2026, NVIDIA CORPORATION.  All rights reserved.
            NVIDIA CORPORATION and its licensors retain all intellectual property
            and proprietary rights in and to this software, related documentation
            and any modifications thereto.  Any use, reproduction, disclosure or
            distribution of this software and related documentation without an express
            license agreement from NVIDIA CORPORATION is strictly prohibited.</license>


            <profiles xmlns="http://www.eprosima.com/XMLSchemas/fastRTPS_Profiles" >
               <transport_descriptors>
                     <transport_descriptor>
                        <transport_id>UdpTransport</transport_id>
                        <type>UDPv4</type>
                     </transport_descriptor>
               </transport_descriptors>

               <participant profile_name="udp_transport_profile" is_default_profile="true">
                     <rtps>
                        <userTransports>
                           <transport_id>UdpTransport</transport_id>
                        </userTransports>
                        <useBuiltinTransports>false</useBuiltinTransports>
                     </rtps>
               </participant>
            </profiles>


   #. Run ``set FASTRTPS_DEFAULT_PROFILES_FILE=C:\.ros\fastdds.xml`` in the terminals that will use ROS 2 functions.
   #. (Optional) Run ``set ROS_DOMAIN_ID=(id_number)`` before launching |isaac-sim_short|. Later you can decide whether to use this ``ROS_DOMAIN_ID`` inside your environment, or explicitly use a different ID number for any given topic.
   #. Ensure the internal ROS 2 libraries are sourced in the same terminal before launching |isaac-sim_short|.


.. _isaac_sim_app_install_cyclonedds_other_platforms:

Enabling the ROS 2 Bridge using Cyclone DDS
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. config-content::
   :show-when: platform=Ubuntu 22.04

   |isaac-sim_short| supports Cyclone DDS middleware for Linux, ROS 2 Humble, and Jazzy. To use Cyclone DDS, you must disable the default bridge that uses Fast DDS. After the bridge is disabled, you can enable the bridge using Cyclone DDS.

.. config-content::
   :show-when: platform=Windows

   .. note:: |isaac-sim_short| supports Cyclone DDS middleware for Linux only. Windows is not supported at this time.


Enabling the ROS Bridge using Cyclone DDS (Linux Only)
********************************************************

.. config-content::
   :show-when: platform=Windows

   .. note:: Windows is not supported at this time.

.. config-content::
   :show-when: platform=Ubuntu 22.04

   #. Follow the `ROS 2 Humble installation steps <https://docs.ros.org/en/humble/Installation/RMW-Implementations/DDS-Implementations/Working-with-Eclipse-CycloneDDS.html>`_ or `ROS 2 Jazzy installation steps <https://docs.ros.org/en/jazzy/Installation/RMW-Implementations/DDS-Implementations/Working-with-Eclipse-CycloneDDS.html>`_ to setup Cyclone DDS for your ROS 2 installation.

      .. note:: Isaac Sim ROS 2 Humble and Jazzy :ref:`internal libraries <isaac_sim_app_no_system_installed_ros_other_platforms>` include Cyclone DDS compiled with Python 3.12.

   #. Before running Isaac Sim, make sure to set the ``RMW_IMPLEMENTATION`` environment variable. Moving forward, if any examples show setting the environment variable to ``rmw_fastrtps_cpp`` you can replace it with the command below:

      .. code-block:: bash

         export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp


.. _isaac_sim_app_install_zenoh_other_platforms:

Enabling the ROS 2 Bridge using Zenoh (ROS 2 Jazzy, Linux Only)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. config-content::
   :show-when: platform=Windows

   .. note:: Zenoh middleware support is untested on Windows at this time.

.. config-content::
   :show-when: platform=Ubuntu 22.04,ros_distro=Humble

   .. note:: Zenoh middleware support is untested on Ubuntu 22.04 with ROS 2 Humble due to Python 3.12 compilation requirements. For ROS 2 Humble, use Fast DDS or Cyclone DDS.

.. config-content::
   :show-when: platform=Ubuntu 22.04,ros_distro=Jazzy

   .. note:: Zenoh middleware support is untested on Ubuntu 22.04 with ROS 2 Jazzy at this time.

   |isaac-sim_short| supports Zenoh middleware for Linux and ROS 2 Jazzy. `Zenoh <https://zenoh.io/>`_ is an open source communication protocol designed for efficient data distribution across heterogeneous systems, providing an alternative to traditional DDS implementations.

   .. note:: |isaac-sim_short| does not ship with internal Zenoh libraries. You must build Zenoh with Python 3.12 and source it before running |isaac-sim_short|.

   For more details on Zenoh, review the `ROS 2 Zenoh documentation <https://docs.ros.org/en/jazzy/Installation/RMW-Implementations/Non-DDS-Implementations/Working-with-Zenoh.html>`_.

   **Installing and running Zenoh**

   #. Ensure you have already cloned the |isaac-sim_short| ROS Workspace Repository from `<https://github.com/isaac-sim/IsaacSim-ros_workspaces>`_. If not, follow the steps in :ref:`isaac_sim_ros_workspace_setup_other_platforms`.

   #. Clone the ``rmw_zenoh`` repository into the ``jazzy_ws/src`` directory:

      .. code-block:: bash

         cd IsaacSim-ros_workspaces/jazzy_ws/src
         git clone https://github.com/ros2/rmw_zenoh.git -b jazzy

   #. Use the Dockerfile to build ROS 2 and the workspace (including Zenoh) with Python 3.12:

      .. code-block:: bash

         cd IsaacSim-ros_workspaces

         ./build_ros.sh -d jazzy -v 22.04

      The built workspace including Zenoh is under ``build_ws/jazzy/jazzy_ws``.


   #. In a **separate terminal**, start the Zenoh router. The router must be running before any ROS 2 nodes can discover each other.

      Use the Docker container from the :ref:`isaac_ros_docker_other_platforms` section. If you have not already started the ``ros_ws_docker`` container, follow the steps there first. Then, inside the container, install ``ros-jazzy-rmw-zenoh-cpp`` and start the router:

      .. code-block:: bash

         # Inside the ros_ws_docker container
         apt-get update && apt-get install -y ros-jazzy-rmw-zenoh-cpp
         source /opt/ros/jazzy/setup.bash
         export RMW_IMPLEMENTATION=rmw_zenoh_cpp
         ros2 run rmw_zenoh_cpp rmw_zenohd

      .. note:: Without the Zenoh router, nodes will not be able to discover each other because multicast discovery is disabled by default in the node's session config. Instead, nodes receive discovery information about other peers through the Zenoh router's gossip functionality.

   #. Before running |isaac-sim_short|, set the ``RMW_IMPLEMENTATION`` environment variable in the terminal where you will launch Isaac Sim. Moving forward, if any examples show setting the environment variable to ``rmw_fastrtps_cpp`` you can replace it with the command below:

      .. code-block:: bash

         export RMW_IMPLEMENTATION=rmw_zenoh_cpp

   #. Source the Python 3.12 build of both ``jazzy_ws`` and ``isaac_sim_ros_ws``, then run |isaac-sim_short|:

      .. code-block:: bash

         cd IsaacSim-ros_workspaces
         source build_ws/jazzy/jazzy_ws/install/local_setup.bash
         source build_ws/jazzy/isaac_sim_ros_ws/install/local_setup.bash
         cd ~/isaacsim
         ./isaac-sim.sh

   #. For any additional terminals running ROS 2 nodes that need to communicate with |isaac-sim_short|, open a new terminal in the same Docker container:

      .. code-block:: bash

         docker exec -it ros_ws_docker /bin/bash -c \
           "source /opt/ros/jazzy/setup.bash && \
            export RMW_IMPLEMENTATION=rmw_zenoh_cpp && \
            cd /jazzy_ws && source install/local_setup.bash && \
            bash"

.. _isaac_sim_app_disable_ros_other_platforms:

Disabling the ROS Bridge in ``isaac-sim.sh``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. config-content::
   :show-when: platform=Windows

   .. note:: In Windows, the ROS Bridge is disabled by default.

To disable the ROS bridge, use the following steps:

#. Open the file located at ``~/isaacsim/apps/isaacsim.exp.full.kit``.

#. Find the line ``isaac.startup.ros_bridge_extension = "isaacsim.ros2.bridge"``.
#. Change it to ``isaac.startup.ros_bridge_extension = ""`` to disable the ROS 2 bridge.

#. Save and close the file.

.. _isaac_ros_docker_other_platforms:

Running ROS in Docker Containers
================================

.. config-content::
   :show-when: platform=Windows

   .. note:: The Docker workflow is not supported on Windows.

.. config-content::
   :show-when: platform=Ubuntu 22.04


   #. Ensure you have already cloned `Isaac Sim ROS Workspace Repository <https://github.com/isaac-sim/IsaacSim-ros_workspaces>`_.

   #. Navigate to the root of the cloned repo and run the following command. If the repo was cloned to a different location, make sure to update the path in ``~/IsaacSim-ros_workspaces`` to the correct one:
      
      .. code-block:: bash

         cd ~/IsaacSim-ros_workspaces
         git submodule update --init --recursive

   #. Run the appropriate ROS 2 Docker container and mount the appropriate workspace from the Isaac Sim ROS Workspaces repo. If the repo was cloned to a different location, make sure to update the path in ``-v ~/IsaacSim-ros_workspaces`` to the correct one.   

      .. config-content::
         :show-when: ros_distro=Humble
         
         .. code-block:: bash

            xhost +

            docker run -it --net=host --env="DISPLAY" --env="ROS_DOMAIN_ID" -v ~/IsaacSim-ros_workspaces/humble_ws:/humble_ws --name ros_ws_docker osrf/ros:humble-desktop /bin/bash

      .. config-content::
         :show-when: ros_distro=Jazzy

         .. code-block:: bash

            xhost +

            docker run -it --net=host --env="DISPLAY" --env="ROS_DOMAIN_ID" -v ~/IsaacSim-ros_workspaces/jazzy_ws:/jazzy_ws --name ros_ws_docker osrf/ros:jazzy-desktop /bin/bash

      Here ``--net=host`` allows communication between |isaac-sim_short| and ROS Docker containers, while ``xhost +`` and ``--env="DISPLAY"`` facilitate passing through the DISPLAY environment variable, which enables GUI applications, such as ``rviz``, to open from the Docker container. ``--name <container name>`` allows you to refer to the container with a fixed name.

   #. Inside the Docker container navigate to the ros workspace.

      .. code-block:: bash

         cd /${ROS_DISTRO}_ws

   #. Inside the Docker container, set the ``FASTRTPS_DEFAULT_PROFILES_FILE`` environment variable as per instructions in :ref:`isaac_sim_app_enable_ros_other_platforms`.

   #. To install additional dependencies, build the workspace, and source the workspace after it's built:

      .. code-block:: bash

         cd /${ROS_DISTRO}_ws
         apt-get update
         git submodule update --init --recursive # If using Docker, perform this step outside the container and relaunch the container
         rosdep install --from-paths src --ignore-src --rosdistro=$ROS_DISTRO -y
         source /opt/ros/$ROS_DISTRO/setup.sh
         colcon build
         source install/local_setup.bash

   #. If you need to open a new terminal, open the existing Docker:

      .. code-block:: bash

         docker exec -it ros_ws_docker /bin/bash -c 'source /opt/ros/$ROS_DISTRO/setup.bash; exec bash'


   #. Optionally, to test your installation you can setup a basic publisher of clocks inside |isaac-sim_short| using the Omnigraph node :ref:`isaac_sim_app_tutorial_gui_omnigraph`:

      #. Press **play** in the simulator. 
      #. Open a separate terminal, open the Docker, set the ``FASTRTPS_DEFAULT_PROFILES_FILE`` environment variable.
      #. Source ROS 2. 
      #. Verify that ``ros2 topic echo /clock`` prints the timestamps coming from |isaac-sim_short|.

      .. figure:: /images/isaac_main_installation_ros2_docker.png
         :align: center
         :width: 300


   #. (Optional) To save the container with all installed dependencies and built workspaces as a new Docker image for future use:

      #. Open a new terminal on the host and commit the container to an image:

         .. code-block:: bash

            docker commit ros_ws_docker isaac_sim_ros_ws:latest

      #. Remove the old container before starting a new one with the same name:

         .. code-block:: bash

            docker rm ros_ws_docker

      #. To reuse the saved image in a future session, start a new container from it:

         .. config-content::
            :show-when: ros_distro=Humble

            .. code-block:: bash

               xhost +

               docker run -it --net=host --env="DISPLAY" --env="ROS_DOMAIN_ID" -v ~/IsaacSim-ros_workspaces/humble_ws:/humble_ws --name ros_ws_docker isaac_sim_ros_ws:latest /bin/bash

         .. config-content::
            :show-when: ros_distro=Jazzy

            .. code-block:: bash

               xhost +

               docker run -it --net=host --env="DISPLAY" --env="ROS_DOMAIN_ID" -v ~/IsaacSim-ros_workspaces/jazzy_ws:/jazzy_ws --name ros_ws_docker isaac_sim_ros_ws:latest /bin/bash

      #. Inside the container, source the workspace and it is ready to use without rebuilding:

         .. code-block:: bash

            source /opt/ros/$ROS_DISTRO/setup.bash
            cd /${ROS_DISTRO}_ws
            source install/local_setup.bash

