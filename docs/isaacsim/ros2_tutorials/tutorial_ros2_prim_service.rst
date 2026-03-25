..
   Copyright (c) 2022-2026, NVIDIA CORPORATION. All rights reserved.
   NVIDIA CORPORATION and its licensors retain all intellectual property
   and proprietary rights in and to this software, related documentation
   and any modifications thereto. Any use, reproduction, disclosure or
   distribution of this software and related documentation without an express
   license agreement from NVIDIA CORPORATION is strictly prohibited.

.. _isaac_sim_app_tutorial_ros2_service_prim:

=================================================
ROS 2 Service for Manipulating Prims Attributes  
=================================================


Learning Objectives
=======================

In this tutorial, you:

- Have a brief discussion on the Isaac Sim ROS 2 service message types for manipulating prim attributes.
- Create ROS 2 services to list prims and their attributes, as well as to read and write a specific prim attribute.

Getting Started
=====================

If sourcing ROS 2 is a part of your ``.bashrc`` then |isaac-sim_short| can be run directly.

**Prerequisite**

- Complete :ref:`isaac_sim_app_install_ros`.

- If using multiple systems, set the ``FASTRTPS_DEFAULT_PROFILES_FILE`` environment variable as per instructions in :ref:`isaac_sim_app_install_ros` before launching |isaac-sim_short|, as well as any terminal where ROS messages will be sent or received, and ROS 2 Extension is enabled.

- The Isaac Sim ROS 2 Workspace (with the ``isaac_ros2_messages`` ROS 2 package) built and sourced in the terminal where the service will be called. Refer to :ref:`isaac_sim_ros_workspace_setup` for more details. 
   
   .. Note:: |isaac-sim_short| already has this service included as part of the internal ROS 2 bridge libraries.

Service Message Types
=======================

The ROS2 Service Prim node provides four services with the following message types:

    * Get all prim path (and types) under a specific path

        ``isaac_ros2_messages/srv/GetPrims``

        .. code-block:: bash

            string path             # get prims at path
            ---
            string[] paths          # list of prim paths
            string[] types          # prim type names
            bool success            # indicate a successful execution of the service
            string message          # informational, for example, for error messages

    * Get all attribute names and types for a specific prim

        ``isaac_ros2_messages/srv/GetPrimAttributes``

        .. code-block:: bash

            string path             # prim path
            ---
            string[] names          # list of attribute base names (name used to Get or Set an attribute)
            string[] displays       # list of attribute display names (name displayed in Property tab)
            string[] types          # list of attribute data types
            bool success            # indicate a successful execution of the service
            string message          # informational, for example, for error messages

    * Get a prim attribute type and values

        ``isaac_ros2_messages/srv/GetPrimAttribute``

        .. code-block:: bash

            string path             # prim path
            string attribute        # attribute name
            ---
            string value            # attribute value (as JSON)
            string type             # attribute type
            bool success            # indicate a successful execution of the service
            string message          # informational, for example, for error messages

    * Set a prim attribute value

        ``isaac_ros2_messages/srv/SetPrimAttribute``

        .. code-block:: bash

            string path             # prim path
            string attribute        # attribute name
            string value            # attribute value (as JSON)
            ---
            bool success            # indicate a successful execution of the service
            string message          # informational, for example, for error messages

.. note::

    Prim attributes are read and write as JSON (applied directly to the data, without keys). Arrays, vectors, matrices and other numeric containers (for example: ``pxr.Gf.Vec3f``, ``pxr.Gf.Matrix4d``, and ``pxr.Gf.Quatd``) are interpreted as a list of numbers (row first).

Manipulating Prims Attributes
==============================

The following example shows how to list the prims and attributes, as well as read and write the pose of an object in the stage using the ROS2 Service Prim node.

.. note::

    Make sure the Isaac Sim ROS 2 Workspace (with the ``isaac_ros2_messages`` ROS 2 package) is built and sourced in the terminal where the service will be called. See :ref:`isaac_sim_ros_workspace_setup` for more details. 
    |isaac-sim_short| already has this service included as part of the internal ROS 2 bridge libraries.

#. In a new stage, create an object (Cube) using the **Create > Shape > Cube** menu.
#. Go to **Window > Graph Editors > Action Graph** to create an Action Graph and add, connect and configure the following |omnigraph_short| nodes into the Action Graph:

    .. figure:: /images/tutorial_ros2_prim_service.png
        :align: center
        :width: 500
        :alt: Prim service

#. Play the simulation to start the services.
#. Use the following command in a new ROS 2 sourced terminal to:

    * List the available services:

        .. code-block:: bash

            ros2 service list

    * Get all child prim paths and types under the prim ``/World``:

        .. code-block:: bash

            ros2 service call /get_prims isaac_ros2_messages/srv/GetPrims "{path: /World}"

    * Get all the attribute names and types for the Cube (``/World/Cube``) prim:

        .. code-block:: bash

            ros2 service call /get_prim_attributes isaac_ros2_messages/srv/GetPrimAttributes "{path: /World/Cube}"

    * Get the pose (position and orientation) of the Cube (``/World/Cube``) prim:

        .. code-block:: bash

            # get position
            ros2 service call /get_prim_attribute isaac_ros2_messages/srv/GetPrimAttribute "{path: /World/Cube, attribute: xformOp:translate}"
            # get orientation (quaternion: wxyz)
            ros2 service call /get_prim_attribute isaac_ros2_messages/srv/GetPrimAttribute "{path: /World/Cube, attribute: xformOp:orient}"

    * Set the new pose (position and orientation) of the Cube (``/World/Cube``) prim:

        .. code-block:: bash

            # set position
            ros2 service call /set_prim_attribute isaac_ros2_messages/srv/SetPrimAttribute "{path: /World/Cube, attribute: xformOp:translate, value: [1, 2, 3]}"
            # set orientation (quaternion: wxyz)
            ros2 service call /set_prim_attribute isaac_ros2_messages/srv/SetPrimAttribute "{path: /World/Cube, attribute: xformOp:orient, value: [0.7325378, 0.4619398, 0.1913417, 0.4619398]}"

Summary
========

In this tutorial you learned how to create ROS 2 services to list prims and their attributes, as well as to read and write a specific prim attribute.

Next Steps
^^^^^^^^^^^^^^^^^^^^^^
Continue on to the next tutorial in our ROS2 Tutorials series, :ref:`isaac_sim_app_ros2_custom_message_python`.
