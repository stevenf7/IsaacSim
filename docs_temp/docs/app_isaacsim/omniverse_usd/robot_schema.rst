..
   Copyright (c) 2025, NVIDIA CORPORATION. All rights reserved.
   NVIDIA CORPORATION and its licensors retain all intellectual property
   and proprietary rights in and to this software, related documentation
   and any modifications thereto. Any use, reproduction, disclosure or
   distribution of this software and related documentation without an express
   license agreement from NVIDIA CORPORATION is strictly prohibited.


.. _isaac_sim_robot_schema:

Robot Schema
============

The Robot Schema extends OpenUSD definitions to define robotic structures. While currently experimental, it provides a standardized way to represent robots by building upon USD Common definitions and the Physics Schema for kinematic tree definitions.

The schema defines four fundamental Structure Types:

.. image:: ../images/isim_6.0_base_ref_gui_robot_schema_description.png
   :width: 800px
   :align: center
   :alt: Robot Schema Description

In this second revision, we introduce new utilities to the schema to auto-populate the Links and Joints lists, based on the physics of the robot. Additionally, we deprecated the indexed attributes for the DOF offsets, and replaced them with a single attribute list stating the degrees of freedom order. Also, ReferencePointAPI was renamed to SiteAPI.
We also added metadata to the robot to describe its type, what License it is under, the source of the original asset, and a version control with changelog, in the form of attributes to the Robot API.


Robot API
---------

The ``IsaacRobotAPI`` serves as the root definition for a robot, describing its complete composition. Applied to the robot's root prim, it contains:

#. Description: Metadata describing the robot's purpose and capabilities
#. Namespace: Unique identifier namespace for robot component messaging
#. Links: Ordered list of constituent links, starting with the base link
#. Joints: Ordered list of connecting joints
#. Type: The type of robot, such as "Manipulator", "Humanoid", "Moving base", "etc."
#. License: The license under which the robot is distributed.
#. Source: The source of the original asset (e.g., the link to the original asset, or the company/website of the original author)
#. Version: The version of the robot asset. This should be updated whenever the robot asset is updated, and should be a semantic versioning number.
#. Changelog: A changelog of the robot asset, with the changes made to the asset over time. This should be updated whenever the robot asset is updated, and should be a list of changes made to the asset.

.. Note:: The Links and Joints lists need only contain elements relevant for reporting. The full kinematic tree may contain additional unlisted elements.



.. _isaac_sim_robot_schema_link_api:

Link API
--------

The Link API describes a single link in the robot and serves as a flag to indicate that the link should be included in the robot composition. This schema should be applied to the bodies of the robot. It contains the following attributes:

#. Name Override: By default, Isaac Sim will use the prim name as the link name when reporting the robot state. This attribute allows for a custom name to be used.

Links are not limited to Rigid bodies, and could be applied to other types of simulation, such as deformable bodies. Care must be taken when using links on deformable bodies, as it would require an equivalent way to compute the robot state if needed.

All Links used by the robot must have an ``IsaacLinkAPI`` applied, regardless of whether they are included in the ``IsaacRobotAPI`` Links list or not.



.. _isaac_sim_robot_schema_joint_api:

Joint API
---------

The Joint API describes a single joint in the robot and serves as a flag to indicate that the joint should be included in the robot composition. This schema should be applied to the joints of the robot. It contains the following attributes:

#. Name Override: By default, Isaac Sim will use the prim name as the joint name when reporting the robot state. This attribute allows for a custom name to be used.
#. DOF (Degree of Freedom) Offset: For each degree of freedom, we introduce an index offset to the reported state, so we can report all DOF stats as a single flat list. This is useful for composing robots that have multiple degrees of freedom but share a common root joint. There is one attribute per degree of freedom axis. The default value is 0-6, depending on the axis. If the joint represents a single degree of freedom, this attribute can be ignored.

All Joints used by the robot must have an ``IsaacJointAPI`` applied, regardless of whether they are included in the ``IsaacRobotAPI`` Joints list or not.



.. _isaac_sim_robot_schema_reference_point_api:

Site API (Formerly Reference Point API)
------------------------------------------

The ``IsaacSiteAPI`` describes points of interest on the robot, for example, attachment points for tools or sensors. This schema should be applied to the points of interest of the robot. It contains the following attributes:

#. Description: A description of the reference point, for example "Tool Attachment Point" or "Sensor Location".
#. Forward Axis: The axis that is considered to be the forward direction of the reference point (X, Y, Z).

.. note:: The Site API replaces the Reference Point API. The Reference Point API is deprecated and not available to be applied to new robots. Robots with Reference Point API applied will still work in this release, but will issue a depreaction warning, and need to be updated to use the Site API.

Composing Robots
================

Robot compositions can be created by applying the Robot API to each sub-robot's root prim. The final assembly is achieved by either:
- Adding a sub-robot's root prim to the parent robot's joints and links lists.
- Selecting specific links and joints from sub-robots



Applying the Robot Schema
==========================

All robots in Isaac Sim's library and imported through :ref:`isaac_sim_urdf_importer` and :ref:`isaac_sim_mjcf_importer` will have the Robot Schema applied to them. For robots imported in prior versions of Isaac Sim, the schema will need to be applied manually. To do so, select the root prim of the robot, and in the right panel under the `Properties` tab, check the `+ Add` button, and select ``Isaac -> Robot Schema -> Robot API``. This will apply the robot schema to the root prim, and will automatically apply the Link API and Joint API to the child prims.


Properties for the Robot Schema will be displayed in the right panel under the `Properties` tab, in their appropriate API section in purple.

.. image:: ../images/isim_6.0_base_ref_gui_robot_schema_apply.png
   :width: 400px
   :align: center


If the robot is updated over time, there are two options to update the schema: manually add the Link API to new bodies and the Joint API to new joints. Alternatively, apply the schema again to the root prim, which will automatically apply the Link API and Joint API to the child prims.

.. note:: When applying the schema to the robot, if your asset follows the :ref:`isaac_sim_app_reference_asset_structure` guidelines, be sure to apply it either in the base layer of the robot asset or in a separate robot schema layer, and not directly in the interface layer. The auto-population will require the physics to be authored, so you can temporarily add physics as a sublayer to the base layer, and remove it after the schema is applied and before saving the asset.

Applying the Robot Schema through code
--------------------------------------

The following snippet shows how to apply the robot schema through code in existing assets that do not currently have it. Following the :ref:`isaac_sim_app_reference_asset_structure` guidelines, we recommend applying the schema in the base layer, or through a layer, so it remains separate from other payloads and is easier to update as the schema evolves. To use this script, open the asset you desire to add the schema to through the interface layer.

.. literalinclude:: ../snippets/omniverse_usd/robot_schema/applying_the_robot_schema_through_code.py
    :language: python

Parsing Robot Structure
========================

The robot structure relies on the Physics Schema to define the robot kinematic tree. The robot schema extends the Physics Schema to include the robot composition information. To parse the robot structure, we need to first collect the Links and Joints that make up the robot, and then, from the Robot API, we start to build the robot structure from the first link on the Links list, iterating over the joints based on their connection to the next links. The robot structure should always be a tree. Loops in the hierarchy need to be flagged with the "Exclude from Articulation" attribute in the joints; otherwise, they will be arbitrarily broken during parsing, based on the depth-first search of the hierarchy. In the extension ``isaacsim.robot.schema`` we provide a set of utility scripts that parse the robot structure and output the Robot Kinematic tree based on the USD data.

Example
-------

#. In the Content Browser, drag and drop a UR10e robot `Robots/UniversalRobots/ur10e/ur10e.usd` into the stage.
#. On the Variant selection menu at the properties panel, select the Robotiq 2f-140 gripper variant.

.. image:: ../images/isim_5.0_base_ref_gui_robot_schema_variant.png
   :width: 350px
   :align: center

#. Open the Script Editor in `Window > Script Editor`, and run the following script:

   .. literalinclude:: ../snippets/omniverse_usd/robot_schema/open_the_script_editor_in_window_script_editor_and.py
       :language: python

On the console, you should see the following output:

   .. image:: ../images/isim_5.0_base_ref_gui_robot_schema_example.png
      :width: 800px
      :align: center


.. code-block::

   base_link
      shoulder_link
         upper_arm_link
            forearm_link
               wrist_1_link
                  wrist_2_link
                     wrist_3_link
                        robotiq_base_link
                           left_outer_knuckle
                              left_outer_finger
                              left_inner_finger
                                 left_inner_knuckle
                           right_outer_knuckle
                              right_outer_finger
                              right_inner_finger
                                 right_inner_knuckle

Note how the gripper is included in the robot structure, even though it is not part of the UR10e robot. Select the UR10e prim on the stage, and check how the Robot Lists have ``ee_link`` listed.


Robot Schema Utility Functions
------------------------------

#. ``GetAllRobotJoints(stage, robot_link_prim, parse_nested_robots)``: Returns all joints of a robot.
#. ``GetAllRobotLinks(stage, robot_link_prim, include_reference_points)``: Returns all links of a robot.
#. ``GetJointBodyRelationship(joint_prim, bodyIndex)``: Gets the target link for joint's body connection, by index.
#. ``GetJointPose(robot_prim, joint_prim)``: Returns joint pose in robot's coordinate system.
#. ``GetLinksFromJoint(root, joint_prim)``: Returns lists of links before/after specified joint.
#. ``GenerateRobotLinkTree(stage, robot_link_prim)``: Generates tree structure of robot links.
#. ``PrintRobotTree(root, indent)``: Prints visual representation of robot link tree.


Asset Structure
==================

Following the guidelines for :ref:`isaac_sim_app_reference_asset_structure`, it is recommended to apply the schema on a separate layer and load it as a sublayer on the robot asset.
