..
   Copyright (c) 2026, NVIDIA CORPORATION. All rights reserved.
   NVIDIA CORPORATION and its licensors retain all intellectual property
   and proprietary rights in and to this software, related documentation
   and any modifications thereto. Any use, reproduction, disclosure or
   distribution of this software and related documentation without an express
   license agreement from NVIDIA CORPORATION is strictly prohibited.


.. _isaac_sim_robot_schema:

Robot Schema
============

The Robot Schema extends OpenUSD with a set of applied API schemas that describe robotic structures in a standardized, composable way. It builds on USD Common definitions and the Physics Schema for kinematic tree definitions, providing the canonical representation for robots in Isaac Sim.

The schema is implemented across two extensions:

- ``isaacsim.robot.schema`` -- Schema definitions, application helpers, and programmatic utilities for traversing and maintaining robot structures.
- ``isaacsim.robot.schema.ui`` -- Interactive :ref:`isaac_sim_robot_inspector_window` for viewing robot kinematic trees in multiple display modes, selectively masking and bypassing components, anchoring links to the world, and visualizing joint connections in the viewport.


Schema Overview
===============

The Robot Schema defines six applied API schemas and one typed schema:

.. list-table::
   :header-rows: 1
   :widths: 25 75

   * - Schema
     - Purpose
   * - **IsaacRobotAPI**
     - Root definition applied to the robot's top-level prim. Holds metadata and ordered lists of links and joints.
   * - **IsaacLinkAPI**
     - Flags a rigid body (or other simulated body) as a link in the robot composition.
   * - **IsaacJointAPI**
     - Flags a physics joint as part of the robot composition and carries DOF ordering information.
   * - **IsaacSiteAPI**
     - Marks a point of interest on the robot (tool mount, sensor location, end-effector frame).
   * - **IsaacAttachmentPointAPI**
     - Defines attachment points used by surface grippers.
   * - **IsaacNamedPose**
     - Typed prim schema storing a named joint configuration with an IK target transform, used by the :ref:`Robot Poser <isaac_sim_robot_poser>`.
   * - **IsaacSurfaceGripper**
     - Typed prim schema for surface-gripper mechanics (grip forces, distances, retry behavior).

.. image:: ../images/isim_6.0_base_ref_gui_robot_schema_description.png
   :width: 800px
   :align: center
   :alt: Robot Schema Description


.. _isaac_sim_robot_schema_robot_api:

Robot API
---------

``IsaacRobotAPI`` is applied to the robot's root prim and serves as the single source of truth for the robot's composition and metadata.

**Relationships**

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Relationship
     - Description
   * - ``isaac:physics:robotLinks``
     - Ordered list of links that compose the robot, starting with the base link. May include sites interleaved after their parent links.
   * - ``isaac:physics:robotJoints``
     - Ordered list of joints connecting the links.
   * - ``isaac:robot:namedPoses``
     - List of :ref:`IsaacNamedPose <isaac_sim_robot_schema_named_pose>` prims defining stored joint configurations for the robot.

**Attributes**

.. list-table::
   :header-rows: 1
   :widths: 25 10 65

   * - Attribute
     - Type
     - Description
   * - ``isaac:description``
     - String
     - Free-form text describing the robot's purpose and capabilities.
   * - ``isaac:namespace``
     - String
     - Unique namespace identifier used for component messaging.
   * - ``isaac:robotType``
     - Token
     - Category of robot (e.g. ``Manipulator``, ``Humanoid``, ``Mobile Base``).
   * - ``isaac:license``
     - Token
     - License under which the robot asset is distributed.
   * - ``isaac:source``
     - String
     - URL or reference to the original asset source.
   * - ``isaac:version``
     - String
     - Semantic version number of the robot asset.
   * - ``isaac:changelog``
     - String[]
     - Ordered list of change descriptions across asset revisions.

.. note:: The Links and Joints lists need only contain elements relevant for reporting. The full kinematic tree may contain additional elements not present in these lists.


.. _isaac_sim_robot_schema_link_api:

Link API
--------

``IsaacLinkAPI`` is applied to each body that participates in the robot composition. It acts as a flag indicating that the prim should appear in robot state reporting.

.. list-table::
   :header-rows: 1
   :widths: 25 10 65

   * - Attribute
     - Type
     - Description
   * - ``isaac:nameOverride``
     - String
     - Optional custom name used instead of the prim name when reporting robot state.

Links are not restricted to rigid bodies. The API can be applied to deformable bodies or other simulation types, though computing robot state from non-rigid links requires custom handling.

All links that belong to the robot must have ``IsaacLinkAPI`` applied, regardless of whether they appear in the ``IsaacRobotAPI`` links list.


.. _isaac_sim_robot_schema_joint_api:

Joint API
---------

``IsaacJointAPI`` is applied to physics joints that participate in the robot composition. It flags the joint for inclusion and carries DOF ordering information.

.. list-table::
   :header-rows: 1
   :widths: 30 10 60

   * - Attribute
     - Type
     - Description
   * - ``isaac:nameOverride``
     - String
     - Optional custom name used instead of the prim name when reporting robot state.
   * - ``isaac:physics:DofOffsetOpOrder``
     - Token[]
     - Ordered list of degree-of-freedom tokens (``TransX``, ``TransY``, ``TransZ``, ``RotX``, ``RotY``, ``RotZ``) defining the flattened DOF index ordering. Single-DOF joints (revolute, prismatic) and zero-DOF joints (fixed) do not require this attribute.

All joints that belong to the robot must have ``IsaacJointAPI`` applied, regardless of whether they appear in the ``IsaacRobotAPI`` joints list.

.. note:: In prior revisions, per-axis DOF offset attributes (``isaac:physics:Tr_X:DoFOffset``, etc.) were used instead of the token array. These are deprecated. Use ``UpdateDeprecatedJointDofOrder`` or ``UpdateDeprecatedSchemas`` to migrate existing assets.


.. _isaac_sim_robot_schema_site_api:

Site API
--------

``IsaacSiteAPI`` describes points of interest on the robot -- tool attachment frames, sensor mount locations, end-effector reference frames, and similar.

.. list-table::
   :header-rows: 1
   :widths: 25 10 65

   * - Attribute
     - Type
     - Description
   * - ``isaac:Description``
     - String
     - Description of the site (e.g. ``"Tool Attachment Point"``).
   * - ``isaac:forwardAxis``
     - Token
     - Axis considered the forward direction of the site (``X``, ``Y``, or ``Z``).

Sites are included in the ``robotLinks`` relationship. They can be placed immediately after their parent link or grouped at the end of the list, controlled by the ``sites_last`` parameter during population.

.. note:: ``IsaacSiteAPI`` replaces the deprecated ``IsaacReferencePointAPI``. Robots still carrying the old schema will function but emit deprecation warnings. Use ``UpdateDeprecatedSchemas`` to migrate.


.. _isaac_sim_robot_schema_named_pose:

Named Pose
----------

``IsaacNamedPose`` is a typed prim schema (inheriting from ``Xform``) that stores a reusable joint configuration for a segment of the robot's kinematic chain. Each named pose captures the joints between a start link and an end link/site, the corresponding joint values, and the target end-effector transform encoded in the prim's Xform ops.

Named poses are collected under a ``Named_Poses`` scope beneath the robot root prim and registered via the ``isaac:robot:namedPoses`` relationship on ``IsaacRobotAPI``. They are created and managed through the :ref:`Robot Poser <isaac_sim_robot_poser>` UI or programmatically via the ``isaacsim.robot.poser`` API.

**Relationships**

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Relationship
     - Description
   * - ``isaac:robot:pose:startLink``
     - The start link of the kinematic chain covered by this pose.
   * - ``isaac:robot:pose:endLink``
     - The end link or site of the kinematic chain.
   * - ``isaac:robot:pose:joints``
     - Ordered list of joint prims in the chain between the start and end links.

**Attributes**

.. list-table::
   :header-rows: 1
   :widths: 30 10 60

   * - Attribute
     - Type
     - Description
   * - ``isaac:robot:pose:valid``
     - Bool
     - Whether the stored pose represents a valid IK solution.
   * - ``isaac:robot:pose:jointValues``
     - Float[]
     - Joint values in USD native units (degrees for revolute, meters for prismatic), ordered to match the ``joints`` relationship.
   * - ``isaac:robot:pose:jointFixed``
     - Bool[]
     - Per-joint fixed flags. When ``True``, the corresponding joint is held constant during IK solving.

Because ``IsaacNamedPose`` inherits from ``Xform``, its translate and orient ops store the target end-effector pose in the robot's coordinate frame. Moving the prim in the viewport updates this target, and the :ref:`Robot Poser <isaac_sim_robot_poser>` can track the prim's transform in real time to solve IK continuously.


Composing Robots
================

Robot compositions are built by applying ``IsaacRobotAPI`` to each sub-robot's root prim. The final assembly is achieved by either:

- Adding a sub-robot's root prim to the parent robot's links and joints lists, which causes the parent to recursively include the sub-robot's full kinematic tree.
- Selecting specific links and joints from sub-robots and adding them directly to the parent robot's lists.


Applying the Robot Schema
=========================

All robots in Isaac Sim's asset library and those imported through :ref:`isaac_sim_urdf_importer` or :ref:`isaac_sim_mjcf_importer` have the Robot Schema pre-applied. For robots imported in prior versions or from external sources, the schema must be applied manually.

Through the GUI
---------------

#. Select the root prim of the robot in the Stage panel.
#. In the Properties panel, click the **+ Add** button.
#. Select **Isaac > Robot Schema > Robot API**.

This applies ``IsaacRobotAPI`` to the root prim and automatically traverses the physics articulation to apply ``IsaacLinkAPI`` and ``IsaacJointAPI`` to all discovered bodies and joints.

.. image:: ../images/isim_6.0_base_ref_gui_robot_schema_apply.png
   :width: 400px
   :align: center

Properties for each schema appear in the Properties panel under their respective API sections (displayed in purple).

If the robot structure changes over time (e.g., new links or joints are added), either manually apply the individual APIs to new prims, or reapply the Robot API to the root prim to re-run automatic population.

.. note:: When applying the schema, if your asset follows the :ref:`isaac_sim_app_reference_asset_structure` guidelines, apply it either in the base layer or in a dedicated robot schema layer -- not directly in the interface layer. Auto-population requires authored physics, so temporarily add the physics layer as a sublayer during schema application, then remove it before saving.

Through Code
------------

The following snippet applies the Robot Schema programmatically. Following the :ref:`isaac_sim_app_reference_asset_structure` guidelines, the schema is authored in a separate layer so it remains independent of other payloads and is easy to update as the schema evolves.

.. literalinclude:: ../snippets/omniverse_usd/robot_schema/applying_the_robot_schema_through_code.py
    :language: python


Parsing Robot Structure
=======================

The robot kinematic tree is derived from the Physics Schema augmented with Robot Schema relationships. Parsing proceeds as follows:

#. Collect links from the ``robotLinks`` relationship on the ``IsaacRobotAPI`` prim.
#. Collect joints from the ``robotJoints`` relationship.
#. Starting from the first link (the base link), perform a breadth-first traversal through joints to connected links, building a tree.

The tree must be acyclic. Joints that would form loops must have their **Exclude from Articulation** attribute set; otherwise, loops are broken arbitrarily during parsing based on visit order.

Example
-------

#. In the Content Browser, drag a UR10e robot (``Robots/UniversalRobots/ur10e/ur10e.usd``) onto the stage.
#. In the Variant selection menu in the Properties panel, select the Robotiq 2f-140 gripper variant.

.. image:: ../images/isim_5.0_base_ref_gui_robot_schema_variant.png
   :width: 350px
   :align: center

#. Open the Script Editor via **Window > Script Editor** and run:

   .. literalinclude:: ../snippets/omniverse_usd/robot_schema/open_the_script_editor_in_window_script_editor_and.py
       :language: python

   The console output:

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

Note how the gripper appears in the robot structure even though it is a separate sub-robot composed into the UR10e. Select the UR10e prim on the stage to see how the Robot Lists include ``ee_link``.


.. _isaac_sim_robot_schema_utilities:

Utility Functions
=================

The ``isaacsim.robot.schema`` extension provides a comprehensive set of utility functions in the ``utils`` module, accessible via:

.. literalinclude:: ../snippets/omniverse_usd/robot_schema/import_utils.py
    :language: python

Traversal and Tree Generation
-----------------------------

.. list-table::
   :header-rows: 1
   :widths: 40 60

   * - Function
     - Description
   * - ``GenerateRobotLinkTree(stage, robot_link_prim)``
     - Builds and returns a ``RobotLinkNode`` tree representing the robot's kinematic structure. Returns the root node.
   * - ``GetAllRobotLinks(stage, robot_link_prim, include_reference_points)``
     - Returns all links of the robot. Retrieves from schema relationships and supplements with any missing links discovered through articulation traversal.
   * - ``GetAllRobotJoints(stage, robot_link_prim, parse_nested_robots)``
     - Returns all joints of the robot. Retrieves from schema relationships and supplements with any missing joints from articulation traversal.
   * - ``GetJointBodyRelationship(joint_prim, bodyIndex)``
     - Returns the target path for a joint's body connection (index 0 or 1). Returns ``None`` if the joint is excluded from articulation.
   * - ``GetJointPose(robot_prim, joint_prim)``
     - Returns the joint's pose as a 4x4 matrix in the robot's coordinate frame.
   * - ``GetLinksFromJoint(root, joint_prim)``
     - Given a tree root and a joint, returns two lists: links before the joint (toward the base) and links after the joint (toward the leaves).
   * - ``PrintRobotTree(root, indent)``
     - Prints an indented text representation of the link tree to the console.

The ``RobotLinkNode`` class represents a node in the kinematic tree:

.. literalinclude:: ../snippets/omniverse_usd/robot_schema/robot_link_node.py
    :language: python

Schema Population
-----------------

.. list-table::
   :header-rows: 1
   :widths: 45 55

   * - Function
     - Description
   * - ``PopulateRobotSchemaFromArticulation(stage, robot_prim, articulation_prim, *, detect_sites, sites_last)``
     - Traverses the physics articulation graph via BFS, applies ``IsaacLinkAPI`` and ``IsaacJointAPI`` to discovered prims, and writes the ordered ``robotLinks`` and ``robotJoints`` relationships. Optionally detects and applies ``IsaacSiteAPI`` to leaf Xforms under links.
   * - ``RecalculateRobotSchema(stage, robot_prim, articulation_prim, *, detect_sites, sites_last)``
     - Similar to ``PopulateRobotSchemaFromArticulation`` but preserves the existing order of valid items. New links and joints are appended; invalid targets are removed. Use this for incremental updates.

Both functions accept:

- ``detect_sites`` (bool): When ``True``, child Xforms with no children under each link are detected and have ``IsaacSiteAPI`` applied automatically.
- ``sites_last`` (bool): When ``False``, detected sites are inserted immediately after their parent link. When ``True``, all sites are appended at the end of the links list.

Site Detection and Management
-----------------------------

.. list-table::
   :header-rows: 1
   :widths: 40 60

   * - Function
     - Description
   * - ``DetectAndApplySites(stage, robot_prim, *, sites_last)``
     - Scans all links under a robot for child Xforms that qualify as sites (leaf Xforms with no children, no existing APIs). Applies ``IsaacSiteAPI`` to each. Returns ``(all_sites, sites_by_parent_path)``.
   * - ``AddSitesToRobotLinks(robot_prim, sites, sites_by_parent, *, sites_last)``
     - Adds detected sites to the ``robotLinks`` relationship, either interleaved after their parent link or appended at the end.

Validation and Maintenance
--------------------------

.. list-table::
   :header-rows: 1
   :widths: 45 55

   * - Function
     - Description
   * - ``ValidateRobotSchemaRelationships(robot_prim)``
     - Checks all targets in ``robotLinks`` and ``robotJoints``. Returns ``(valid_links, invalid_links, valid_joints, invalid_joints)``.
   * - ``EnsurePrependListForRobotRelationships(robot_prim)``
     - Rebuilds ``robotLinks`` and ``robotJoints`` using USD prepend list operations for correct layering behavior.
   * - ``RebuildRelationshipAsPrepend(prim, rel_name, targets)``
     - Low-level helper that rebuilds a single relationship using prepend list operations.
   * - ``UpdateDeprecatedSchemas(robot_prim)``
     - Traverses the robot subtree and replaces ``IsaacReferencePointAPI`` with ``IsaacSiteAPI``. Also migrates deprecated per-axis DOF offset attributes on joints.
   * - ``UpdateDeprecatedJointDofOrder(joint_prim)``
     - Migrates a single joint's deprecated per-axis ``DoFOffset`` attributes to the ``DofOffsetOpOrder`` token array. Removes the deprecated attributes from the edit layer.

Named Pose Query
-----------------

.. list-table::
   :header-rows: 1
   :widths: 45 55

   * - Function
     - Description
   * - ``GetAllNamedPoses(stage, robot_prim)``
     - Returns all :ref:`IsaacNamedPose <isaac_sim_robot_schema_named_pose>` prims registered in the robot's ``namedPoses`` relationship.
   * - ``GetNamedPoseStartLink(named_pose_prim)``
     - Returns the start link path from the named pose.
   * - ``GetNamedPoseEndLink(named_pose_prim)``
     - Returns the end link / site path from the named pose.
   * - ``GetNamedPoseJoints(named_pose_prim)``
     - Returns the ordered list of joint paths in the pose's kinematic chain.
   * - ``GetNamedPoseJointValues(named_pose_prim)``
     - Returns the stored joint values array (native USD units).
   * - ``GetNamedPoseJointFixed(named_pose_prim)``
     - Returns the per-joint fixed flags array.
   * - ``GetNamedPoseValid(named_pose_prim)``
     - Returns whether the stored pose is valid.


.. _isaac_sim_robot_schema_kinematics:

Kinematics
==========

The ``isaacsim.robot.schema`` extension includes a pure-Python kinematics stack for forward kinematics, Jacobian computation, and inverse kinematics. These modules are used internally by the :ref:`Robot Poser <isaac_sim_robot_poser>` and are available for direct use.

.. literalinclude:: ../snippets/omniverse_usd/robot_schema/import_kinematics.py
    :language: python

Math Primitives
---------------

The ``math`` module (``usd.schema.isaac.robot_schema.math``) provides foundational data structures and pure math utilities with no USD stage or simulation dependencies.

**Data structures**

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Class
     - Description
   * - ``Transform``
     - Rigid SE(3) transform (translation ``t`` + quaternion ``q`` in ``[w, x, y, z]`` order). Supports composition via ``@``, inversion via ``inv()``.
   * - ``Joint``
     - Single joint in a kinematic chain. Stores the screw axis (``w`` for revolute, ``v`` for prismatic), home pose, joint limits (``lower``, ``upper``), an optional trailing tip offset, and the USD ``prim_path``. The ``exp(q)`` method returns the relative transform for a given joint value.

**Quaternion utilities**

.. list-table::
   :header-rows: 1
   :widths: 35 65

   * - Function
     - Description
   * - ``quat_mul(q1, q2)``
     - Hamilton product of two quaternions.
   * - ``quat_conj(q)``
     - Quaternion conjugate.
   * - ``quat_rotate(q, v)``
     - Rotate a 3D vector by a unit quaternion.
   * - ``axis_angle_to_quat(axis, angle)``
     - Build a unit quaternion from axis-angle representation.
   * - ``quat_to_matrix(q)``
     - Convert a unit quaternion to a 3x3 rotation matrix.

**Linear algebra**

.. list-table::
   :header-rows: 1
   :widths: 25 75

   * - Function
     - Description
   * - ``skew(v)``
     - 3x3 skew-symmetric matrix for cross-product with ``v``.
   * - ``adjoint(T)``
     - 6x6 adjoint matrix for a rigid transform ``T``.


Kinematic Chain
---------------

The ``kinematic_chain`` module (``usd.schema.isaac.robot_schema.kinematic_chain``) provides the ``KinematicChain`` class that caches the robot's kinematic tree and builds an ordered joint chain between a start and end prim for FK and IK computation.

.. list-table::
   :header-rows: 1
   :widths: 40 60

   * - Method / Property
     - Description
   * - ``KinematicChain(stage, robot_prim, start_prim, end_prim)``
     - Constructor. Builds the kinematic tree once and extracts the joint chain between the two prims. ``start_prim`` and ``end_prim`` are optional; when omitted the cached tree is available for teleport operations without IK.
   * - ``compute_fk(q)``
     - Compute end-effector FK for joint configuration ``q``. Returns ``(Transform, per_joint_transforms)``.
   * - ``compute_fk_and_jacobian(q)``
     - Fused single-pass FK and spatial Jacobian computation. Returns ``(Transform, 6xN Jacobian)``.
   * - ``read_joint_states()``
     - Read current USD joint state for the chain joints. Returns a dict of prim-path to value (radians or meters).
   * - ``teleport(joint_dict)``
     - Apply joint values by propagating FK body transforms through the kinematic tree. For use when simulation is stopped.
   * - ``teleport_anchored(joint_dict)``
     - Apply joint values while keeping a fixed prim's world position unchanged. Handles backward (child-to-parent) joints by rigidly correcting the robot after FK propagation.
   * - ``joints``
     - Ordered list of ``Joint`` objects in the chain.
   * - ``tree_root``
     - Cached kinematic tree root node.


IK Solver Interface
-------------------

The ``ik_solver`` module (``usd.schema.isaac.robot_schema.ik_solver``) defines an abstract solver interface and a global registry.

.. list-table::
   :header-rows: 1
   :widths: 40 60

   * - Class / Function
     - Description
   * - ``IKSolver``
     - Abstract base class. Subclasses implement ``solve(chain, target, q0, **kwargs)`` returning joint values that achieve the target pose.
   * - ``IKSolverRegistry.register(name, solver_cls, *, default)``
     - Register an IK solver class under the given name. Set ``default=True`` to make it the default solver.
   * - ``IKSolverRegistry.get(name)``
     - Return a new instance of the solver registered under the given name. ``None`` returns the default solver.
   * - ``IKSolverRegistry.available()``
     - List all registered solver names.
   * - ``pose_error(Td, T)``
     - Compute 6-DOF pose error between desired and actual transforms. Returns a 6-vector ``[rot_x, rot_y, rot_z, pos_x, pos_y, pos_z]``.

Custom IK solvers can be registered at import time and used by the Robot Poser by passing their name to the ``solver_name`` parameter.


Levenberg-Marquardt Solver
--------------------------

The ``lm_ik`` module (``usd.schema.isaac.robot_schema.lm_ik``) provides the default IK solver registered as ``"lm"``. It implements Levenberg-Marquardt optimization with adaptive damping, joint-limit clamping, null-space bias toward joint mid-range, and per-joint fixed masks.

.. list-table::
   :header-rows: 1
   :widths: 25 15 60

   * - Parameter
     - Default
     - Description
   * - ``lam``
     - ``1e-3``
     - Initial LM damping factor. Adapts automatically: shrinks on progress, grows on overshoot.
   * - ``iters``
     - ``30``
     - Maximum iterations.
   * - ``tol``
     - ``1e-6``
     - Convergence tolerance on the weighted cost.
   * - ``w_rot``
     - ``1.0``
     - Weight on rotational error components.
   * - ``w_pos``
     - ``1.0``
     - Weight on positional error components.
   * - ``max_step``
     - ``0.5``
     - Maximum joint-space step per iteration (prevents wild jumps).
   * - ``null_space_bias``
     - ``0.05``
     - Strength of null-space bias toward joint mid-range. Helps escape singular configurations.
   * - ``joint_fixed``
     - ``None``
     - Boolean mask of chain length. ``True`` locks that DOF (Jacobian column zeroed).


.. _isaac_sim_robot_schema_named_pose_crud:

Named Pose CRUD
===============

The ``isaacsim.robot.poser`` extension provides higher-level CRUD and I/O operations for :ref:`IsaacNamedPose <isaac_sim_robot_schema_named_pose>` prims. These functions build on the :ref:`Kinematic Chain <isaac_sim_robot_schema_kinematics>` and IK solver to create, retrieve, apply, and export named poses.

.. literalinclude:: ../snippets/omniverse_usd/robot_schema/import_named_pose_crud.py
    :language: python

.. list-table::
   :header-rows: 1
   :widths: 45 55

   * - Function
     - Description
   * - ``store_named_pose(stage, robot_prim, pose_name, pose_result)``
     - Creates an ``IsaacNamedPose`` prim, writes joint values, relationships, and the target Xform, and registers it in the robot's ``namedPoses`` relationship.
   * - ``get_named_pose(stage, robot_prim, pose_name)``
     - Retrieves a stored pose as a ``PoseResult`` dataclass.
   * - ``list_named_poses(stage, robot_prim)``
     - Returns the names of all named poses on the robot.
   * - ``delete_named_pose(stage, robot_prim, pose_name)``
     - Removes the pose prim and its entry from the ``namedPoses`` relationship.
   * - ``apply_pose_by_name(stage, robot_prim, pose_name)``
     - Applies a stored pose to the robot. Teleports when simulation is stopped; drives via joint targets when running.
   * - ``export_poses(stage, robot_prim, filepath)``
     - Exports all named poses to a JSON file.
   * - ``import_poses(stage, robot_prim, filepath)``
     - Imports named poses from a JSON file and stores them on the robot.

For interactive authoring of named poses, see the :ref:`Robot Poser <isaac_sim_robot_poser>` documentation.


Asset Structure
===============

Following the guidelines for :ref:`isaac_sim_app_reference_asset_structure`, apply the Robot Schema on a separate layer and load it as a sublayer on the robot asset. This keeps the schema isolated from physics and geometry payloads, making it straightforward to update as the schema evolves across releases.
