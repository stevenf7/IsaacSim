


..
   Copyright (c) 2022-2026, NVIDIA CORPORATION. All rights reserved.
   NVIDIA CORPORATION and its licensors retain all intellectual property
   and proprietary rights in and to this software, related documentation
   and any modifications thereto. Any use, reproduction, disclosure or
   distribution of this software and related documentation without an express
   license agreement from NVIDIA CORPORATION is strictly prohibited.


.. _isaac_sim_app_ros2_omnigraph_cpp_node:

=================================
ROS 2 Custom C++ OmniGraph Node
=================================


Learning Objectives
====================

In this example, you learn how to:

- Write a custom C++ |omnigraph_short| node to use with |isaac-sim_short|.


.. note:: This tutorial is supported only on Linux with ROS 2 Jazzy.


Getting Started
=================

**Prerequisite**


- Basic understanding of `building ROS 2 packages <https://docs.ros.org/en/jazzy/Tutorials/Beginner-Client-Libraries/Custom-ROS2-Interfaces.html>`_.


Building a Custom Message Package
==================================

To use our custom message with |isaac-sim_short|, you must build the custom message package with ROS 2. Follow the custom message sample in the official ROS 2 documentation. The definition of the message (``Sphere.msg`` file) is:

.. code-block:: bash

    geometry_msgs/Point center
    float64 radius


Follow the instructions on the ROS 2 Jazzy Documentation for `Creating custom msg and srv files <https://docs.ros.org/en/jazzy/Tutorials/Beginner-Client-Libraries/Custom-ROS2-Interfaces.html>`_.

.. note::

    You only need to complete the steps up to subsection `6. Confirm msg and srv creation <https://docs.ros.org/en/jazzy/Tutorials/Beginner-Client-Libraries/Custom-ROS2-Interfaces.html#confirm-msg-and-srv-creation>`_.

.. important::

    Follow the package and message naming terminology provided in the official tutorials; it is important when you build your own C++ |omnigraph_short| nodes.

Setting Up the Extension C++ Template
======================================

To use the custom ROS 2 |omnigraph_short| nodes, you must build your own extension, which contains the necessary C++ code. For this purpose, we are going to use the `Isaac Sim <https://github.com/isaac-sim/IsaacSim>`_ repository.

#. Clone and build the Isaac Sim repository from GitHub by following the instructions described in the `Quick Start <https://github.com/isaac-sim/IsaacSim?tab=readme-ov-file#quick-start>`_ section.
  
    Ensure that ``./_build/linux-x86_64/release/isaac-sim.sh`` works as expected.

#. Create a new *Isaac Sim OmniGraph Node Extension* template using the ``./repo.sh template new`` command.

    Select (with the arrow keys) or fill in the prompts with the following values:

    * **? Do you accept the governing terms?** ``Yes``
    * **? Select what you want to create with arrow keys:** ``Extension``
    * **? Select desired template with arrow keys:** ``[isaacsim-omnigraph-extension]: Isaac Sim OmniGraph Node Extension``
    * **? Enter name of extension [name-spaced, lowercase, alphanumeric]:** ``custom.cpp.ros2_node``
    * **? Enter title:** ``ROS 2 C++ Custom OmniGraph Node``
    * **? Enter version:** ``0.1.0``
    * **? Enter description:** ``A new Isaac Sim OmniGraph node extension.``
    * **? Enter category:** ``Simulation``

    |

    After answering the prompts, the template will be created in the ``source/extensions/custom.cpp.ros2_node`` path.

#. Edit the ``deps/kit-sdk-deps.packman.xml`` file to add the following lines at the end, before the ``</project>`` closing tag:

    .. code-block:: bash

        <dependency name="system_ros" linkPath="../_build/target-deps/system_ros" tags="${config}">
            <source path="<FULL_PATH_TO_THE_ROS_2_INSTALL>" />
        </dependency>

        <dependency name="additional_ros_workspace" linkPath="../_build/target-deps/additional_ros" tags="${config}">
            <source path="<FULL_PATH_TO_WORKSPACE_CREATED_ABOVE>/install/tutorial_interfaces" />
        </dependency>

    Update the source ``path`` according to your local setup. For example:

      * ``<FULL_PATH_TO_THE_ROS_2_INSTALL>``: ``/opt/ros/jazzy``
      * ``<FULL_PATH_TO_WORKSPACE_CREATED_ABOVE>``: ``/home/user/ros2_ws``

    This ensures that the ``premake5.lua`` file can find the relevant ROS 2 headers and libraries on your system. These are needed for building your custom nodes.

#. Edit the ``source/extensions/custom.cpp.ros2_node/premake5.lua`` file to include the headers and libraries of the custom message package.

    Extend the ``includedirs`` definition (under the ``-- C++ Carbonite plugin`` section) to include system level ROS includes and the additional sourced ROS workspace includes. Add the ``libdirs`` and ``links`` definitions to link against the ROS 2 C API libs and the custom message with its libs.

    .. code-block:: lua

        includedirs {
            "%{root}/source/extensions/custom.cpp.ros2_node/include",
            -- System level ROS includes
            "%{target_deps}/system_ros/include/builtin_interfaces",
            "%{target_deps}/system_ros/include/geometry_msgs",
            "%{target_deps}/system_ros/include/rcl",
            "%{target_deps}/system_ros/include/rcl_yaml_param_parser",
            "%{target_deps}/system_ros/include/rcutils",
            "%{target_deps}/system_ros/include/rmw",
            "%{target_deps}/system_ros/include/rosidl_dynamic_typesupport",
            "%{target_deps}/system_ros/include/rosidl_runtime_c",
            "%{target_deps}/system_ros/include/rosidl_typesupport_interface",
            "%{target_deps}/system_ros/include/service_msgs",
            "%{target_deps}/system_ros/include/std_msgs",
            "%{target_deps}/system_ros/include/type_description_interfaces",
            -- Additional sourced ROS workspace includes
            "%{target_deps}/additional_ros/include/tutorial_interfaces",
        }

        libdirs {
            -- System level ROS libraries
            "%{target_deps}/system_ros/lib",
            -- Additional sourced ROS workspace libraries
            "%{target_deps}/additional_ros/lib",
        }

        links{
            --  Minimal ROS 2 C API libs needed for your nodes to work
            "rosidl_runtime_c", "rcutils", "rcl", "rmw",
            -- Add dependencies of the custom message with its libs
            "geometry_msgs__rosidl_typesupport_c", "geometry_msgs__rosidl_typesupport_c",
            "tutorial_interfaces__rosidl_typesupport_c", "tutorial_interfaces__rosidl_generator_c",
        }

#. Create the ``ROS2CustomMessageNode.ogn`` definition file and the ``ROS2CustomMessageNode.cpp`` source code file with the following specification in the ``source/extensions/custom.cpp.ros2_node/nodes`` folder.

    .. literalinclude:: ../static/source/tutorial_ros2_custom_omnigraph_node_cpp_ROS2CustomMessageNode.ogn
        :caption: ROS2CustomMessageNode.ogn
        :language: json

    .. literalinclude:: ../static/source/tutorial_ros2_custom_omnigraph_node_cpp_ROS2CustomMessageNode.cpp
        :caption: ROS2CustomMessageNode.cpp
        :language: c++

    The ``rcl`` ROS 2 API is used for creating and working with the ROS 2 components in the |omnigraph_short| node:

    * In the C++ Node, ``compute()`` is called when the ``Exec In`` condition is true, this is where the node and publisher are initially created. The message is also published from this function. 

#. Run ``./build.sh`` to build your new extension with ROS 2 |omnigraph_short| nodes.

    After the build is complete, the built extension will be under the ``_build/linux-x86_64/release/exts`` folder.

Adding the Extension to |isaac-sim_short|
==========================================

To add the extension and corresponding nodes into |isaac-sim_short|:

#. Source the ROS 2 installation and the local ROS 2 workspace containing the ``tutorial_interfaces`` package created above.

    .. code-block:: bash

        source /opt/ros/jazzy/setup.bash

    .. code-block:: bash

        source install/local_setup.bash

#. Run |isaac-sim_short| from this terminal.

#. Go to **Window > Extensions** and search for the ``custom.cpp.ros2_node`` extension. Then enable it by toggling the switch.

    .. note::

        If you want to use the extension in a different Isaac Sim application than the one used to build it, follow these steps to make the extension available in the new application:

        #. Go to **Window > Extensions**, look for the hamburger menu (1) to the right side of the search bar (just above **Third Party** tab). Click **Settings** (2).

        #. Click the ``+`` icon under **Extension Search Paths** and add the path to your built extension in the previous section (your built extensions are under ``_build/linux-x86_64/release/exts``).

        #. Verify that your extensions are under the **Third Party** tab (3). Then, enable the extension by toggling the switch.

        .. figure:: /images/isim_4.5_full_tut_gui_add_ext_to_isim.png
            :align: center
            :alt: Adding extensions to Isaac Sim
            :width: 80%

Building the Action Graph and Running the Nodes
==================================================

With the ``custom.cpp.ros2_node`` extension enabled, go and create an ActionGraph with the new ROS 2 node:

#. Go to **Window > Graph Editors > Action Graph** and create a **New Action Graph**.

    - Search for ``ROS 2`` in the **Action Graph** tab, drag the ``ROS2 Publish Custom Message`` node into the graph.

    - Search for ``Playback Tick`` and drag it into the graph.

    - Connect ``Tick`` from the ``On Playback Tick`` node to ``Exec In`` for the ROS 2 node.

    .. figure:: /images/isim_4.5_full_tut_gui_custom_cpp_nodes_graph.png
        :align: center
        :alt: Custom C++ ROS2 OGN Example Extension ActionGraph
        :width: 80%

#. Click **Play** on the scene and the node starts publishing to ROS 2.

#. Verify the publishing, by opening a new terminal and sourcing ROS 2 and the local workspace in it.

    Verify that the ``/custom_node/sphere_msg`` topic is available by running ``ros2 topic list``.
    Also, show the published messages by running ``ros2 topic echo /custom_node/sphere_msg``.

Summary
========

This tutorial covered the following topics:

- Building your own extension, which contains ROS 2 C++ |omnigraph_short| nodes

- Using these nodes with |isaac-sim_short| 


Next Steps
^^^^^^^^^^^^^^^^^^^^^^

Continue on to the next tutorial in the ROS2 Tutorials series, :ref:`isaac_sim_app_tutorial_ros2_launch` to learn how to deploy Isaac Sim using ROS 2 Launch.

