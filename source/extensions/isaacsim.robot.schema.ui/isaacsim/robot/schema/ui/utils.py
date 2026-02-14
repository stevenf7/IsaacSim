# SPDX-FileCopyrightText: Copyright (c) 2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Shared UI utilities for robot schema visualization."""

from typing import Any

import carb
import omni.kit.viewport.utility as viewport_utility
import omni.usd
import usd.schema.isaac.robot_schema.utils as robot_schema_utils
from omni.kit.viewport.utility.camera_state import ViewportCameraState
from omni.ui import color as cl
from pxr import Gf, Sdf, Trace, Usd, UsdGeom, UsdPhysics
from usd.schema.isaac import robot_schema

# --------------------------------------------------------------------------
# Shared color constants
# --------------------------------------------------------------------------
CONNECTION_COLOR = cl("#1D5F41")
LINE_COLOR = cl("#383838")
LINE_BACKGROUND_COLOR = cl("#c3c3c3")


# --------------------------------------------------------------------------
# Stage and Prim Access Utilities
# --------------------------------------------------------------------------


def get_stage_safe(context_name: str = "") -> Usd.Stage | None:
    """Retrieve the current USD stage safely.

    Args:
        context_name: Name of the USD context. Empty string uses the default context.

    Returns:
        The current USD stage, or None if unavailable.

    Example:

    .. code-block:: python

        stage = get_stage_safe()
    """
    context = omni.usd.get_context(context_name)
    if not context:
        return None
    return context.get_stage()


def get_prim_safe(path: Sdf.Path | str | None, stage: Usd.Stage | None = None) -> Usd.Prim | None:
    """Retrieve a prim at the given path safely.

    Args:
        path: The USD path or path string to the prim.
        stage: Optional USD stage. If None, retrieves from the default context.

    Returns:
        The prim if it exists and is valid, or None otherwise.

    Example:

    .. code-block:: python

        prim = get_prim_safe("/World/Robot")
    """
    if path is None:
        return None
    if stage is None:
        stage = get_stage_safe()
    if not stage:
        return None
    if not isinstance(path, Sdf.Path):
        path = Sdf.Path(path)
    prim = stage.GetPrimAtPath(path)
    if prim and prim.IsValid():
        return prim
    return None


# --------------------------------------------------------------------------
# Vector Conversion Utilities
# --------------------------------------------------------------------------


def to_vec3d(position: Any) -> Gf.Vec3d | None:
    """Convert a position to a 3D vector.

    Args:
        position: A position value (tuple, list, vector, or indexable object).

    Returns:
        A vector representation, or None if conversion fails.

    Example:

    .. code-block:: python

        position = to_vec3d([0.0, 1.0, 2.0])
    """
    if position is None:
        return None
    if isinstance(position, Gf.Vec3d):
        return position
    try:
        return Gf.Vec3d(position[0], position[1], position[2])
    except (TypeError, IndexError):
        try:
            return Gf.Vec3d(position)
        except Exception:
            return None


def to_float_list(position: Any) -> list[float]:
    """Convert a position to a list of floats.

    Args:
        position: A position value (tuple, list, vector, or indexable object).

    Returns:
        A list of three floats [x, y, z].

    Example:

    .. code-block:: python

        floats = to_float_list((1.0, 2.0, 3.0))
    """
    return [float(x) for x in position]


# --------------------------------------------------------------------------
# Camera Utilities
# --------------------------------------------------------------------------


def get_camera_path() -> str | None:
    """Retrieve the current viewport camera's USD path.

    Returns:
        The camera prim path, or None if unavailable.

    Example:

    .. code-block:: python

        camera_path = get_camera_path()
    """
    return viewport_utility.get_viewport_window_camera_path()


def get_camera_position() -> Gf.Vec3d | None:
    """Retrieve the current viewport camera's world position.

    Returns:
        The camera world position, or None if unavailable.

    Example:

    .. code-block:: python

        position = get_camera_position()
    """
    camera_path = get_camera_path()
    if not camera_path:
        return None
    camera_state = ViewportCameraState()
    return camera_state.position_world


def get_camera_pose(offset: float = 0.0) -> tuple[Gf.Vec3d, Gf.Vec3d] | None:
    """Retrieve the current camera position and forward direction.

    Computes the camera's world-space position and forward direction vector.
    USD cameras look down -Z in local space.

    Args:
        offset: Optional offset along the forward direction to apply to the position.

    Returns:
        A tuple of (position, forward_direction), or None if the camera is unavailable.

    Example:

    .. code-block:: python

        camera_pose = get_camera_pose()
    """
    camera_path = get_camera_path()
    if not camera_path:
        return None
    stage = get_stage_safe()
    if not stage:
        return None
    camera_prim = stage.GetPrimAtPath(camera_path)
    if not camera_prim or not camera_prim.IsValid():
        return None
    xform_cache = UsdGeom.XformCache(Usd.TimeCode.Default())
    world_transform = xform_cache.GetLocalToWorldTransform(camera_prim)
    position = world_transform.ExtractTranslation()
    # USD cameras look down -Z in local space
    forward_direction = -Gf.Vec3d(world_transform[2][0], world_transform[2][1], world_transform[2][2])
    if forward_direction.GetLength() == 0.0:
        return None
    forward_direction.Normalize()
    position = Gf.Vec3d(position[0], position[1], position[2])
    if offset:
        position = position + forward_direction * offset
    return position, forward_direction


def is_in_front_of_camera(
    point: Any, camera_position: Gf.Vec3d, camera_forward: Gf.Vec3d, z_offset: float = 0.001
) -> bool:
    """Check if a point is in front of the camera.

    Args:
        point: The world-space point to check (tuple, list, or vector).
        camera_position: The camera position vector.
        camera_forward: The camera forward direction vector.
        z_offset: Small offset to avoid z-fighting issues.

    Returns:
        True if the point is in front of the camera, False otherwise.

    Example:

    .. code-block:: python

        visible = is_in_front_of_camera(point, camera_pos, camera_forward)
    """
    point_vector = to_vec3d(point)
    if point_vector is None:
        return False
    direction = point_vector - camera_position
    if direction.GetLength() > 0:
        direction.Normalize()
    return Gf.Dot((point_vector - camera_position) - direction * z_offset, camera_forward) > 0


# --------------------------------------------------------------------------
# Viewport Utilities
# --------------------------------------------------------------------------


def get_active_viewport() -> Any | None:
    """Retrieve the active viewport API.

    Returns:
        The active viewport API object, or None if unavailable.

    Example:

    .. code-block:: python

        viewport_api = get_active_viewport()
    """
    return viewport_utility.get_active_viewport()


def world_to_screen_position(
    position: Any, viewport_api: Any | None = None
) -> tuple[float, float] | tuple[float, float, float] | None:
    """Convert a world position to screen coordinates.

    Args:
        position: The world-space position to convert.
        viewport_api: Optional viewport API. If None, uses the active viewport.

    Returns:
        A tuple (x, y) of screen coordinates if the position is visible,
        or a tuple (x, y, z) of world coordinates as fallback if viewport
        conversion fails, or None if the position is invalid.

    Example:

    .. code-block:: python

        screen_pos = world_to_screen_position((0.0, 0.0, 0.0))
    """
    position_vector = to_vec3d(position)
    if position_vector is None:
        return None
    if viewport_api is None:
        viewport_api = get_active_viewport()
    if viewport_api:
        try:
            ndc_position = viewport_api.world_to_ndc.Transform(position_vector)
            texture_position, viewport = viewport_api.map_ndc_to_texture([ndc_position[0], ndc_position[1]])
            if viewport is not None and texture_position is not None:
                return (texture_position[0], texture_position[1])
        except Exception:
            pass
    return (position_vector[0], position_vector[1], position_vector[2])


def is_position_in_viewport(position: Any, viewport_api: Any | None = None) -> bool:
    """Check if a world position is within the viewport screen space.

    Args:
        position: The world-space position to check.
        viewport_api: Optional viewport API. If None, uses the active viewport.

    Returns:
        True if the position is visible in the viewport, False otherwise.

    Example:

    .. code-block:: python

        visible = is_position_in_viewport((0.0, 0.0, 0.0))
    """
    position_vector = to_vec3d(position)
    if position_vector is None:
        return False
    if viewport_api is None:
        viewport_api = get_active_viewport()
    if not viewport_api:
        return False
    try:
        ndc_position = viewport_api.world_to_ndc.Transform(position_vector)
        texture_position, viewport = viewport_api.map_ndc_to_texture([ndc_position[0], ndc_position[1]])
        return viewport is not None
    except Exception:
        return False


# --------------------------------------------------------------------------
# Path Mapping for Hierarchy Stage
# --------------------------------------------------------------------------


class PathMap:
    """Bidirectional mapping between original USD paths and hierarchy stage paths.

    Maintains two dictionaries to allow lookup in either direction, enabling
    translation between the original stage's prim paths and the generated
    hierarchy stage's prim paths.
    """

    def __init__(self):
        self.original_to_hierarchy = {}
        self.hierarchy_to_original = {}

    def insert(self, original_path: Sdf.Path, hierarchy_path: Sdf.Path) -> None:
        """Add a path mapping.

        Args:
            original_path: The path in the original USD stage.
            hierarchy_path: The corresponding path in the hierarchy stage.

        Example:

        .. code-block:: python

            path_map.insert(original_path, hierarchy_path)
        """
        self.original_to_hierarchy[original_path] = hierarchy_path
        self.hierarchy_to_original[hierarchy_path] = original_path

    def get_hierarchy_path(self, original_path: Sdf.Path) -> Sdf.Path | None:
        """Get the hierarchy stage path for an original path.

        Args:
            original_path: The path in the original USD stage.

        Returns:
            The corresponding hierarchy stage path, or None if not found.

        Example:

        .. code-block:: python

            hierarchy_path = path_map.get_hierarchy_path(original_path)
        """
        return self.original_to_hierarchy.get(original_path)

    def get_original_path(self, hierarchy_path: Sdf.Path) -> Sdf.Path | None:
        """Get the original stage path for a hierarchy path.

        Args:
            hierarchy_path: The path in the hierarchy stage.

        Returns:
            The corresponding original stage path, or None if not found.

        Example:

        .. code-block:: python

            original_path = path_map.get_original_path(hierarchy_path)
        """
        return self.hierarchy_to_original.get(hierarchy_path)

    def clear(self) -> None:
        """Clear all path mappings.

        Example:

        .. code-block:: python

            path_map.clear()
        """
        self.original_to_hierarchy.clear()
        self.hierarchy_to_original.clear()


# --------------------------------------------------------------------------
# Joint Position Utilities
# --------------------------------------------------------------------------


def joint_has_both_bodies(joint_prim: Usd.Prim | None) -> bool:
    """Check if a joint has both body0 and body1 relationships defined.

    Args:
        joint_prim: The joint prim to inspect.

    Returns:
        True if both body0 and body1 relationships have valid targets, False otherwise.

    Example:

    .. code-block:: python

        has_bodies = joint_has_both_bodies(joint_prim)
    """
    if joint_prim is None:
        return False
    joint = UsdPhysics.Joint(joint_prim)
    if not joint:
        return False
    body0_rel = joint.GetBody0Rel()
    body1_rel = joint.GetBody1Rel()
    if not body0_rel or not body1_rel:
        return False
    body0_targets = body0_rel.GetTargets()
    body1_targets = body1_rel.GetTargets()
    return bool(body0_targets) and bool(body1_targets)


@Trace.TraceFunction
def get_link_position(link: Usd.Prim | Sdf.Path | str | None) -> Gf.Vec3d | None:
    """Compute the world-space position of a link prim origin.

    Args:
        link: Link prim or prim path.

    Returns:
        The link's world-space position vector, or None if computation fails.

    Example:

    .. code-block:: python

        position = get_link_position("/World/Robot/Link1")
    """
    if link is None:
        return None

    prim = None
    if isinstance(link, Usd.Prim):
        prim = link if link.IsValid() else None
    else:
        stage = get_stage_safe()
        if not stage:
            return None
        if not isinstance(link, Sdf.Path):
            link = Sdf.Path(link)
        prim = get_prim_safe(link, stage)

    if not prim:
        return None

    try:
        world_transform = UsdGeom.XformCache(Usd.TimeCode.Default()).GetLocalToWorldTransform(prim)
        translation = world_transform.ExtractTranslation()
        return Gf.Vec3d(*translation)
    except Exception as error:
        carb.log_warn(f"Failed to compute link position for {prim.GetPath()}: {error}")
        return None


@Trace.TraceFunction
def get_joint_position(robot_root_path: Sdf.Path | str, joint_path: Sdf.Path | str) -> Gf.Vec3d | None:
    """Compute the world-space position of a robot joint.

    Retrieves the joint pose from the robot schema and transforms it
    to world coordinates using the robot's world transform.

    Args:
        robot_root_path: The path to the robot root prim.
        joint_path: The path to the joint prim.

    Returns:
        The joint's world-space position vector, or None if computation fails.

    Example:

    .. code-block:: python

        position = get_joint_position("/World/Robot", "/World/Robot/joint")
    """
    stage = get_stage_safe()
    if not stage:
        return None

    if not isinstance(robot_root_path, Sdf.Path):
        robot_root_path = Sdf.Path(robot_root_path)
    if not isinstance(joint_path, Sdf.Path):
        joint_path = Sdf.Path(joint_path)

    robot_prim = get_prim_safe(robot_root_path, stage)
    joint_prim = get_prim_safe(joint_path, stage)

    if not robot_prim or not joint_prim:
        return None

    try:
        pose_matrix = robot_schema_utils.GetJointPose(robot_prim, joint_prim)
        if pose_matrix is None:
            return None
        translation = Gf.Vec3d(*pose_matrix.ExtractTranslation())
        # Transform from robot coordinates to world coordinates
        robot_world_transform = UsdGeom.XformCache(Usd.TimeCode.Default()).GetLocalToWorldTransform(robot_prim)
        world_position = robot_world_transform.Transform(translation)
        return world_position
    except Exception as error:
        carb.log_warn(f"Failed to compute joint position for {joint_path}: {error}")
        return None


# --------------------------------------------------------------------------
# Robot Hierarchy Generation
# --------------------------------------------------------------------------


def _create_hierarchy_node(
    hierarchy_stage: Usd.Stage,
    link_node: Any,
    parent_link_prim: Usd.Prim,
    parent_joint_in_chain: Usd.Prim | None,
    parent_link_source_prim: Usd.Prim | None,
    robot_root_path: Sdf.Path,
    path_map: PathMap,
    joint_connections: list[Any],
) -> None:
    """Create a hierarchy node and its children recursively.

    Internal helper function for generate_robot_hierarchy_stage().

    Args:
        hierarchy_stage: The in-memory hierarchy stage being built.
        link_node: The current link tree node to process.
        parent_link_prim: The parent prim in the hierarchy stage.
        parent_joint_in_chain: The parent joint prim for connection tracking.
        parent_link_source_prim: The parent link prim in the source stage.
        robot_root_path: The path to the robot root prim.
        path_map: The path mapping object for tracking paths.
        joint_connections: List to append connection items to.
    """
    # Import here to avoid circular dependency
    from .model import ConnectionItem

    current_joint_prim = link_node._joint_to_parent
    if current_joint_prim:
        hierarchy_joint_path = parent_link_prim.GetPath().AppendChild(current_joint_prim.GetName())
        hierarchy_joint_prim = hierarchy_stage.DefinePrim(hierarchy_joint_path, current_joint_prim.GetTypeName())
        hierarchy_link_path = hierarchy_joint_prim.GetPath().AppendChild(link_node.name)
        path_map.insert(current_joint_prim.GetPath(), hierarchy_joint_prim.GetPath())

        # Create connection item for this joint
        joint_position = get_joint_position(robot_root_path, current_joint_prim.GetPath())
        if parent_joint_in_chain:
            parent_joint_position = get_joint_position(robot_root_path, parent_joint_in_chain.GetPath())
        else:
            parent_joint_position = get_link_position(parent_link_source_prim)

        connection_item = ConnectionItem(
            joint_prim=current_joint_prim,
            parent_joint_prim=parent_joint_in_chain,
            parent_link_prim=parent_link_source_prim,
            robot_root_path=robot_root_path,
            joint_pos=joint_position,
            parent_joint_pos=parent_joint_position,
        )
        joint_connections.append(connection_item)
        next_parent_joint = current_joint_prim
    else:
        hierarchy_link_path = parent_link_prim.GetPath().AppendChild(link_node.name)
        next_parent_joint = parent_joint_in_chain

    hierarchy_link_prim = hierarchy_stage.DefinePrim(hierarchy_link_path, "Xform")
    path_map.insert(link_node.prim.GetPath(), hierarchy_link_prim.GetPath())

    for child_node in link_node.children:
        _create_hierarchy_node(
            hierarchy_stage,
            child_node,
            hierarchy_link_prim,
            next_parent_joint,
            link_node.prim,
            robot_root_path,
            path_map,
            joint_connections,
        )


def generate_robot_hierarchy_stage() -> tuple[Usd.Stage | None, PathMap, list[Any]]:
    """Generate an in-memory USD stage representing the robot joint hierarchy.

    Scans the current stage for prims with the Robot API applied, builds
    a link tree for each robot, and creates a hierarchy stage where joints
    are represented as parent-child relationships rather than as properties.

    Returns:
        A tuple of (hierarchy_stage, path_map, joint_connections).
        ``hierarchy_stage`` is an in-memory stage with the hierarchy structure,
        ``path_map`` translates between original and hierarchy paths, and
        ``joint_connections`` contains connection items for viewport visualization.
        Returns (None, an empty path map, []) if no robots are found.

    Example:

    .. code-block:: python

        hierarchy_stage, path_map, connections = generate_robot_hierarchy_stage()
    """
    stage = get_stage_safe()
    path_map = PathMap()
    joint_connections: list[Any] = []

    if not stage:
        return None, path_map, joint_connections

    root_prim = stage.GetPrimAtPath("/")
    robot_prims = [prim for prim in Usd.PrimRange(root_prim) if prim.HasAPI(robot_schema.Classes.ROBOT_API.value)]

    if not robot_prims:
        return None, path_map, joint_connections

    # Collect valid robots with their link trees
    robot_data = []
    for prim in robot_prims:
        joints = robot_schema_utils.GetAllRobotJoints(stage, prim)
        robot_tree = robot_schema_utils.GenerateRobotLinkTree(stage, prim)
        if robot_tree:
            robot_data.append((prim, robot_tree, joints))

    if not robot_data:
        return None, path_map, joint_connections

    hierarchy_stage = Usd.Stage.CreateInMemory()
    if not hierarchy_stage:
        return None, path_map, joint_connections

    for robot_root_prim, robot_tree, joints in robot_data:
        hierarchy_root_prim = hierarchy_stage.DefinePrim(robot_root_prim.GetPath(), "Xform")
        path_map.insert(robot_root_prim.GetPath(), hierarchy_root_prim.GetPath())
        robot_root_path = robot_root_prim.GetPath()

        _create_hierarchy_node(
            hierarchy_stage,
            robot_tree,
            hierarchy_root_prim,
            None,
            None,
            robot_root_path,
            path_map,
            joint_connections,
        )

    return hierarchy_stage, path_map, joint_connections
