# SPDX-FileCopyrightText: Copyright (c) 2021-2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
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
from typing import Generic, TypeVar

import isaacsim.core.experimental.utils.prim as prim_utils
import isaacsim.core.experimental.utils.stage as stage_utils
import numpy as np
import usdrt
import warp as wp
from isaacsim.core.experimental.objects import (
    Capsule,
    Cone,
    Cube,
    Cylinder,
    Mesh,
    Plane,
    Sphere,
)
from isaacsim.core.experimental.prims import (
    GeomPrim,
    Prim,
    XformPrim,
)
from pxr import UsdGeom, UsdPhysics

from .obstacle_strategy import (
    ObstacleConfiguration,
    ObstacleRepresentation,
    ObstacleStrategy,
)
from .trackable_api import TrackableApi
from .utils import collision_approximation, scene_validation
from .world_interface import WorldInterface

_BOUNDING_BOX_CACHE = collision_approximation.create_bbox_cache()

# Attribute name constants - centralized here to avoid hardcoding strings throughout
# These match the attribute names from usdrt.Rt.Xformable and usdrt.UsdPhysics.CollisionAPI
_TRANSFORM_TOKEN = usdrt.Rt.Tokens.fabricHierarchyWorldMatrix
_LOCAL_TRANSFORM_TOKEN = usdrt.Rt.Tokens.fabricHierarchyLocalMatrix


# Mappings of Tokens to track and APIs to verify, depending on the user selection.
_COLLISION_ENABLED_TOKENS = {TrackableApi.PHYSICS_COLLISION: usdrt.UsdPhysics.Tokens.physicsCollisionEnabled}
_COLLISION_APIS = {TrackableApi.PHYSICS_COLLISION: UsdPhysics.CollisionAPI}


def _add_sphere_from_prim(
    prim_path: str,
    prim: usdrt.Usd.Prim,
    world_interface: WorldInterface,
    obstacle_configuration: ObstacleConfiguration,
    rt_change_tracker: usdrt.Rt.ChangeTracker,
    collision_api: TrackableApi,
):
    """Add a sphere prim to the planning world interface.

    Args:
        prim_path: Path to the sphere prim.
        prim: USDRT prim object.
        world_interface: Planning world interface to populate.
        obstacle_configuration: Configuration for the obstacle representation.
        rt_change_tracker: USDRT change tracker for attribute monitoring.
        collision_api: Collision API which is used to signal that the obstacle is enabled/disabled.
    """
    # collision_api not yet in use, but when it is, we should get the collision enabled
    # from the correct API.

    # Track updates on relevant attributes:
    sphere_schema = usdrt.UsdGeom.Sphere(prim)
    rt_change_tracker.TrackAttribute(sphere_schema.GetRadiusAttr().GetName())

    # Given that this object is being added directly as a sphere,
    # we can get its data from the core API:
    isaac_core_object = Sphere(paths=prim_path)
    collision_object = GeomPrim(paths=prim_path)

    world_interface.add_spheres(
        prim_paths=[prim_path],
        radii=isaac_core_object.get_radii(),
        scales=isaac_core_object.get_local_scales(),
        safety_tolerances=wp.array([[obstacle_configuration.safety_tolerance]]),
        poses=isaac_core_object.get_world_poses(),
        enabled_array=collision_object.get_enabled_collisions(),
    )


def _add_cube_from_prim(
    prim_path: str,
    prim: usdrt.Usd.Prim,
    world_interface: WorldInterface,
    obstacle_configuration: ObstacleConfiguration,
    rt_change_tracker: usdrt.Rt.ChangeTracker,
    collision_api: TrackableApi,
):
    """Add a cube prim to the planning world interface.

    Args:
        prim_path: Path to the cube prim.
        prim: USDRT prim object.
        world_interface: Planning world interface to populate.
        obstacle_configuration: Configuration for the obstacle representation.
        rt_change_tracker: USDRT change tracker for attribute monitoring.
        collision_api: Collision API which is used to signal that the obstacle is enabled/disabled.
    """
    # collision_api not yet in use, but when it is, we should get the collision enabled
    # from the correct API.

    # Schemas which include attributes we will want to track for updates:
    cube_schema = usdrt.UsdGeom.Cube(prim)
    rt_change_tracker.TrackAttribute(cube_schema.GetSizeAttr().GetName())

    # Given that this object is being added directly as a cube,
    # we can get its data from the core API:
    isaac_core_object = Cube(paths=prim_path)
    collision_object = GeomPrim(paths=prim_path)

    world_interface.add_cubes(
        prim_paths=[prim_path],
        sizes=isaac_core_object.get_sizes(),
        scales=isaac_core_object.get_local_scales(),
        safety_tolerances=wp.array([[obstacle_configuration.safety_tolerance]]),
        poses=isaac_core_object.get_world_poses(),
        enabled_array=collision_object.get_enabled_collisions(),
    )


def _add_cone_from_prim(
    prim_path: str,
    prim: usdrt.Usd.Prim,
    world_interface: WorldInterface,
    obstacle_configuration: ObstacleConfiguration,
    rt_change_tracker: usdrt.Rt.ChangeTracker,
    collision_api: TrackableApi,
):
    """Add a cone prim to the planning world interface.

    Args:
        prim_path: Path to the cone prim.
        prim: USDRT prim object.
        world_interface: Planning world interface to populate.
        obstacle_configuration: Configuration for the obstacle representation.
        rt_change_tracker: USDRT change tracker for attribute monitoring.
        collision_api: Collision API which is used to signal that the obstacle is enabled/disabled.
    """
    # collision_api not yet in use, but when it is, we should get the collision enabled
    # from the correct API.

    # Track relevant attributes:
    cone_schema = usdrt.UsdGeom.Cone(prim)
    rt_change_tracker.TrackAttribute(cone_schema.GetAxisAttr().GetName())
    rt_change_tracker.TrackAttribute(cone_schema.GetRadiusAttr().GetName())
    rt_change_tracker.TrackAttribute(cone_schema.GetHeightAttr().GetName())

    # Given that this object is being added directly as a cone,
    # we can get its data from the core API:
    isaac_core_object = Cone(paths=prim_path)
    collision_object = GeomPrim(paths=prim_path)
    world_interface.add_cones(
        prim_paths=[prim_path],
        axes=isaac_core_object.get_axes(),
        radii=isaac_core_object.get_radii(),
        lengths=isaac_core_object.get_heights(),
        scales=isaac_core_object.get_local_scales(),
        safety_tolerances=wp.array([[obstacle_configuration.safety_tolerance]]),
        poses=isaac_core_object.get_world_poses(),
        enabled_array=collision_object.get_enabled_collisions(),
    )


def _add_plane_from_prim(
    prim_path: str,
    prim: usdrt.Usd.Prim,
    world_interface: WorldInterface,
    obstacle_configuration: ObstacleConfiguration,
    rt_change_tracker: usdrt.Rt.ChangeTracker,
    collision_api: TrackableApi,
):
    """Add a plane prim to the planning world interface.

    Args:
        prim_path: Path to the plane prim.
        prim: USDRT prim object.
        world_interface: Planning world interface to populate.
        obstacle_configuration: Configuration for the obstacle representation.
        rt_change_tracker: USDRT change tracker for attribute monitoring.
        collision_api: Collision API which is used to signal that the obstacle is enabled/disabled.
    """
    # collision_api not yet in use, but when it is, we should get the collision enabled
    # from the correct API.

    # useful schemas:
    plane_schema = usdrt.UsdGeom.Plane(prim)
    rt_change_tracker.TrackAttribute(plane_schema.GetAxisAttr().GetName())
    rt_change_tracker.TrackAttribute(plane_schema.GetLengthAttr().GetName())
    rt_change_tracker.TrackAttribute(plane_schema.GetWidthAttr().GetName())

    # Given that this object is being added directly as a plane,
    # we can get its data from the core API:
    isaac_core_object = Plane(paths=prim_path)
    collision_object = GeomPrim(paths=prim_path)
    world_interface.add_planes(
        prim_paths=[prim_path],
        axes=isaac_core_object.get_axes(),
        lengths=isaac_core_object.get_lengths(),
        widths=isaac_core_object.get_widths(),
        scales=isaac_core_object.get_local_scales(),
        safety_tolerances=wp.array([[obstacle_configuration.safety_tolerance]]),
        poses=isaac_core_object.get_world_poses(),
        enabled_array=collision_object.get_enabled_collisions(),
    )


def _add_capsule_from_prim(
    prim_path: str,
    prim: usdrt.Usd.Prim,
    world_interface: WorldInterface,
    obstacle_configuration: ObstacleConfiguration,
    rt_change_tracker: usdrt.Rt.ChangeTracker,
    collision_api: TrackableApi,
):
    """Add a capsule prim to the planning world interface.

    Args:
        prim_path: Path to the capsule prim.
        prim: USDRT prim object.
        world_interface: Planning world interface to populate.
        obstacle_configuration: Configuration for the obstacle representation.
        rt_change_tracker: USDRT change tracker for attribute monitoring.
        collision_api: Collision API which is used to signal that the obstacle is enabled/disabled.
    """
    # collision_api not yet in use, but when it is, we should get the collision enabled
    # from the correct API.

    # Track relevant attributes:
    capsule_schema = usdrt.UsdGeom.Capsule(prim)
    rt_change_tracker.TrackAttribute(capsule_schema.GetAxisAttr().GetName())
    rt_change_tracker.TrackAttribute(capsule_schema.GetRadiusAttr().GetName())
    rt_change_tracker.TrackAttribute(capsule_schema.GetHeightAttr().GetName())

    # Given that this object is being added directly as a capsule,
    # we can get its data from the core API:
    isaac_core_object = Capsule(paths=prim_path)
    collision_object = GeomPrim(paths=prim_path)
    world_interface.add_capsules(
        prim_paths=[prim_path],
        axes=isaac_core_object.get_axes(),
        radii=isaac_core_object.get_radii(),
        lengths=isaac_core_object.get_heights(),
        scales=isaac_core_object.get_local_scales(),
        safety_tolerances=wp.array([[obstacle_configuration.safety_tolerance]]),
        poses=isaac_core_object.get_world_poses(),
        enabled_array=collision_object.get_enabled_collisions(),
    )


def _add_cylinder_from_prim(
    prim_path: str,
    prim: usdrt.Usd.Prim,
    world_interface: WorldInterface,
    obstacle_configuration: ObstacleConfiguration,
    rt_change_tracker: usdrt.Rt.ChangeTracker,
    collision_api: TrackableApi,
):
    """Add a cylinder prim to the planning world interface.

    Args:
        prim_path: Path to the cylinder prim.
        prim: USDRT prim object.
        world_interface: Planning world interface to populate.
        obstacle_configuration: Configuration for the obstacle representation.
        rt_change_tracker: USDRT change tracker for attribute monitoring.
        collision_api: Collision API which is used to signal that the obstacle is enabled/disabled.
    """
    # Track relevant attributes:
    cylinder_schema = usdrt.UsdGeom.Cylinder(prim)
    rt_change_tracker.TrackAttribute(cylinder_schema.GetAxisAttr().GetName())
    rt_change_tracker.TrackAttribute(cylinder_schema.GetRadiusAttr().GetName())
    rt_change_tracker.TrackAttribute(cylinder_schema.GetHeightAttr().GetName())

    # Given that this object is being added directly as a cylinder,
    # we can get its data from the core API:
    isaac_core_object = Cylinder(paths=prim_path)
    collision_object = GeomPrim(paths=prim_path)
    world_interface.add_cylinders(
        prim_paths=[prim_path],
        axes=isaac_core_object.get_axes(),
        radii=isaac_core_object.get_radii(),
        lengths=isaac_core_object.get_heights(),
        scales=isaac_core_object.get_local_scales(),
        safety_tolerances=wp.array([[obstacle_configuration.safety_tolerance]]),
        poses=isaac_core_object.get_world_poses(),
        enabled_array=collision_object.get_enabled_collisions(),
    )


def _add_mesh_from_prim(
    prim_path: str,
    prim: usdrt.Usd.Prim,
    world_interface: WorldInterface,
    obstacle_configuration: ObstacleConfiguration,
    rt_change_tracker: usdrt.Rt.ChangeTracker,
    collision_api: TrackableApi,
):
    """Add a mesh prim to the planning world interface.

    Args:
        prim_path: Path to the mesh prim.
        prim: USDRT prim object.
        world_interface: Planning world interface to populate.
        obstacle_configuration: Configuration for the obstacle representation.
        rt_change_tracker: USDRT change tracker for attribute monitoring.
        collision_api: Collision API which is used to signal that the obstacle is enabled/disabled.
    """
    # collision_api not yet in use, but when it is, we should get the collision enabled
    # from the correct API.

    # Track relevant attributes:
    mesh_schema = usdrt.UsdGeom.Mesh(prim)
    rt_change_tracker.TrackAttribute(mesh_schema.GetPointsAttr().GetName())
    rt_change_tracker.TrackAttribute(mesh_schema.GetFaceVertexIndicesAttr().GetName())
    rt_change_tracker.TrackAttribute(mesh_schema.GetFaceVertexCountsAttr().GetName())
    rt_change_tracker.TrackAttribute(mesh_schema.GetNormalsAttr().GetName())

    # Given that this object is being added directly as a mesh,
    # we can get its data from the core API:
    isaac_core_object = Mesh(paths=prim_path)
    collision_object = GeomPrim(paths=prim_path)
    face_indices, face_counts, _, _ = isaac_core_object.get_face_specs()

    world_interface.add_meshes(
        prim_paths=[prim_path],
        points=isaac_core_object.get_points(),
        face_vertex_indices=face_indices,
        face_vertex_counts=face_counts,
        normals=isaac_core_object.get_normals(),
        scales=isaac_core_object.get_local_scales(),
        safety_tolerances=wp.array([[obstacle_configuration.safety_tolerance]]),
        poses=isaac_core_object.get_world_poses(),
        enabled_array=collision_object.get_enabled_collisions(),
    )


def _add_triangulated_mesh_from_prim(
    prim_path: str,
    prim: usdrt.Usd.Prim,
    world_interface: WorldInterface,
    obstacle_configuration: ObstacleConfiguration,
    rt_change_tracker: usdrt.Rt.ChangeTracker,
    collision_api: TrackableApi,
):
    """Add a triangulated mesh prim to the planning world interface.

    Args:
        prim_path: Path to the mesh prim.
        prim: USDRT prim object.
        world_interface: Planning world interface to populate.
        obstacle_configuration: Configuration for the obstacle representation.
        rt_change_tracker: USDRT change tracker for attribute monitoring.
        collision_api: Collision API which is used to signal that the obstacle is enabled/disabled.
    """
    # collision_api not yet in use, but when it is, we should get the collision enabled
    # from the correct API.

    # Track relevant attributes:
    mesh_schema = usdrt.UsdGeom.Mesh(prim)
    rt_change_tracker.TrackAttribute(mesh_schema.GetPointsAttr().GetName())
    rt_change_tracker.TrackAttribute(mesh_schema.GetFaceVertexIndicesAttr().GetName())
    rt_change_tracker.TrackAttribute(mesh_schema.GetFaceVertexCountsAttr().GetName())

    # Given that this object is being added directly as a triangulated mesh,
    # we can get its data from the core API:
    isaac_core_object = Mesh(paths=prim_path)
    collision_object = GeomPrim(paths=prim_path)

    # triangulate the mesh:
    all_triangulated_mesh_indices = collision_approximation.triangulate_mesh(isaac_core_object)

    if len(all_triangulated_mesh_indices) < 1:
        raise ValueError("collision_approximation.triangulate_mesh failed to triangulate any meshes.")
    triangulated_mesh_indices = all_triangulated_mesh_indices[0]

    # reshape to something more natural, pass as a warp array to match other inputs.
    triangulated_mesh_indices = wp.from_numpy(
        triangulated_mesh_indices,
        dtype=wp.int32,
    )

    world_interface.add_triangulated_meshes(
        prim_paths=[prim_path],
        points=isaac_core_object.get_points(),
        face_vertex_indices=[triangulated_mesh_indices],
        scales=isaac_core_object.get_local_scales(),
        safety_tolerances=wp.array([[obstacle_configuration.safety_tolerance]]),
        poses=isaac_core_object.get_world_poses(),
        enabled_array=collision_object.get_enabled_collisions(),
    )


def _add_oriented_bounding_box_from_prim(
    prim_path: str,
    prim: usdrt.Usd.Prim,
    world_interface: WorldInterface,
    obstacle_configuration: ObstacleConfiguration,
    rt_change_tracker: usdrt.Rt.ChangeTracker,
    collision_api: TrackableApi,
):
    """Add an oriented bounding box representation to the planning world interface.

    Args:
        prim_path: Path to the prim.
        prim: USDRT prim object.
        world_interface: Planning world interface to populate.
        obstacle_configuration: Configuration for the obstacle representation.
        rt_change_tracker: USDRT change tracker for attribute monitoring.
        collision_api: Collision API which is used to signal that the obstacle is enabled/disabled.
    """
    # collision_api not yet in use, but when it is, we should get the collision enabled
    # from the correct API.

    # TODO: Can we track "extent" or something like that?

    # compute the oriented bounding box of the prim:
    obb = collision_approximation.compute_obb(
        bbox_cache=_BOUNDING_BOX_CACHE,
        prim_path=prim_path,
    )

    isaac_core_object = XformPrim(paths=prim_path)
    collision_object = GeomPrim(paths=prim_path)

    world_interface.add_oriented_bounding_boxes(
        prim_paths=[prim_path],
        centers=[wp.from_numpy(obb.center, dtype=wp.float32)],
        rotation_matrices=[wp.from_numpy(obb.rotation_matrix, dtype=wp.float32)],
        half_side_lengths=[wp.from_numpy(obb.half_side_lengths, dtype=wp.float32)],
        scales=isaac_core_object.get_local_scales(),
        safety_tolerances=wp.array([[obstacle_configuration.safety_tolerance]]),
        poses=isaac_core_object.get_world_poses(),
        enabled_array=collision_object.get_enabled_collisions(),
    )


_ADD_OBJECT_CALLBACK_MAP = {
    ObstacleRepresentation.SPHERE: _add_sphere_from_prim,
    ObstacleRepresentation.CUBE: _add_cube_from_prim,
    ObstacleRepresentation.CONE: _add_cone_from_prim,
    ObstacleRepresentation.PLANE: _add_plane_from_prim,
    ObstacleRepresentation.CAPSULE: _add_capsule_from_prim,
    ObstacleRepresentation.CYLINDER: _add_cylinder_from_prim,
    ObstacleRepresentation.MESH: _add_mesh_from_prim,
    ObstacleRepresentation.TRIANGULATED_MESH: _add_triangulated_mesh_from_prim,
    ObstacleRepresentation.OBB: _add_oriented_bounding_box_from_prim,
    # TODO:
    # SIGNED_DISTANCE_FIELD:
    # CONVEX_HULL:
    # BOUNDING_SPHERE:
    # CONVEX_DECOMPOSITION:
}


def _update_prim_transforms(
    prim_paths: list[str],
    world_interface: WorldInterface,
):
    """Update transforms for a batch of tracked prims that have changed.

    Args:
        prim_paths: List of prim paths with transform changes to update.
        world_interface: Planning world interface to update.
    """
    xformable_core = XformPrim(paths=prim_paths)
    world_interface.update_obstacle_transforms(
        prim_paths=prim_paths,
        poses=xformable_core.get_world_poses(),
    )


def _update_prim_physics_collision_enables(
    prim_paths: list[str],
    world_interface: WorldInterface,
):
    """Update collision enable states for a batch of tracked prims that have changed.

    Args:
        prim_paths: List of prim paths with collision enable changes to update.
        world_interface: Planning world interface to update.
    """

    collision_object = GeomPrim(paths=prim_paths)
    world_interface.update_obstacle_enables(
        prim_paths=prim_paths,
        enabled_array=collision_object.get_enabled_collisions(),
    )


def _update_prim_scales(
    prim_paths: list[str],
    world_interface: WorldInterface,
):
    """Update scales for a batch of tracked prims that have changed.

    Args:
        prim_paths: List of prim paths with scale changes to update.
        world_interface: Planning world interface to update.
    """
    collision_object = GeomPrim(paths=prim_paths)
    world_interface.update_obstacle_scales(
        prim_paths=prim_paths,
        scales=collision_object.get_local_scales(),
    )


def _update_sphere_properties_from_prim(
    prim_path: str,
    prim: usdrt.Usd.Prim,
    world_interface: WorldInterface,
    rt_change_tracker: usdrt.Rt.ChangeTracker,
):
    """Update sphere properties in the planning world interface.

    Args:
        prim_path: Path to the sphere prim.
        prim: USDRT prim object.
        world_interface: Planning world interface to update.
        rt_change_tracker: USDRT change tracker for monitoring changes.
    """
    radii = None

    sphere_schema = usdrt.UsdGeom.Sphere(prim)
    changed_attributes = rt_change_tracker.GetChangedAttributes(prim)

    isaac_core_object = Sphere(paths=prim_path)

    if sphere_schema.GetRadiusAttr().GetName() in changed_attributes:
        radii = isaac_core_object.get_radii()

    world_interface.update_sphere_properties(
        prim_paths=[prim_path],
        radii=radii,
    )


def _update_cube_properties_from_prim(
    prim_path: str,
    prim: usdrt.Usd.Prim,
    world_interface: WorldInterface,
    rt_change_tracker: usdrt.Rt.ChangeTracker,
):
    """Update cube properties in the planning world interface.

    Args:
        prim_path: Path to the cube prim.
        prim: USDRT prim object.
        world_interface: Planning world interface to update.
        rt_change_tracker: USDRT change tracker for monitoring changes.
    """
    sizes = None

    cube_schema = usdrt.UsdGeom.Cube(prim)
    changed_attributes = rt_change_tracker.GetChangedAttributes(prim)

    isaac_core_object = Cube(paths=prim_path)

    if cube_schema.GetSizeAttr().GetName() in changed_attributes:
        sizes = isaac_core_object.get_sizes()

    world_interface.update_cube_properties(
        prim_paths=[prim_path],
        sizes=sizes,
    )


def _update_cone_properties_from_prim(
    prim_path: str,
    prim: usdrt.Usd.Prim,
    world_interface: WorldInterface,
    rt_change_tracker: usdrt.Rt.ChangeTracker,
):
    """Update cone properties in the planning world interface.

    Args:
        prim_path: Path to the cone prim.
        prim: USDRT prim object.
        world_interface: Planning world interface to update.
        rt_change_tracker: USDRT change tracker for monitoring changes.
    """
    axes = None
    radii = None
    lengths = None

    cone_schema = usdrt.UsdGeom.Cone(prim)
    changed_attributes = rt_change_tracker.GetChangedAttributes(prim)

    isaac_core_object = Cone(paths=prim_path)

    if cone_schema.GetAxisAttr().GetName() in changed_attributes:
        axes = isaac_core_object.get_axes()

    if cone_schema.GetRadiusAttr().GetName() in changed_attributes:
        radii = isaac_core_object.get_radii()

    if cone_schema.GetHeightAttr().GetName() in changed_attributes:
        lengths = isaac_core_object.get_heights()

    world_interface.update_cone_properties(
        prim_paths=[prim_path],
        axes=axes,
        radii=radii,
        lengths=lengths,
    )


def _update_plane_properties_from_prim(
    prim_path: str,
    prim: usdrt.Usd.Prim,
    world_interface: WorldInterface,
    rt_change_tracker: usdrt.Rt.ChangeTracker,
):
    """Update plane properties in the planning world interface.

    Args:
        prim_path: Path to the plane prim.
        prim: USDRT prim object.
        world_interface: Planning world interface to update.
        rt_change_tracker: USDRT change tracker for monitoring changes.
    """
    axes = None
    lengths = None
    widths = None

    plane_schema = usdrt.UsdGeom.Plane(prim)
    changed_attributes = rt_change_tracker.GetChangedAttributes(prim)

    isaac_core_object = Plane(paths=prim_path)

    if plane_schema.GetAxisAttr().GetName() in changed_attributes:
        axes = isaac_core_object.get_axes()

    if plane_schema.GetLengthAttr().GetName() in changed_attributes:
        lengths = isaac_core_object.get_lengths()

    if plane_schema.GetWidthAttr().GetName() in changed_attributes:
        widths = isaac_core_object.get_widths()

    world_interface.update_plane_properties(
        prim_paths=[prim_path],
        axes=axes,
        lengths=lengths,
        widths=widths,
    )


def _update_capsule_properties_from_prim(
    prim_path: str,
    prim: usdrt.Usd.Prim,
    world_interface: WorldInterface,
    rt_change_tracker: usdrt.Rt.ChangeTracker,
):
    """Update capsule properties in the planning world interface.

    Args:
        prim_path: Path to the capsule prim.
        prim: USDRT prim object.
        world_interface: Planning world interface to update.
        rt_change_tracker: USDRT change tracker for monitoring changes.
    """
    axes = None
    radii = None
    lengths = None

    capsule_schema = usdrt.UsdGeom.Capsule(prim)
    changed_attributes = rt_change_tracker.GetChangedAttributes(prim)

    isaac_core_object = Capsule(paths=prim_path)

    if capsule_schema.GetAxisAttr().GetName() in changed_attributes:
        axes = isaac_core_object.get_axes()

    if capsule_schema.GetRadiusAttr().GetName() in changed_attributes:
        radii = isaac_core_object.get_radii()

    if capsule_schema.GetHeightAttr().GetName() in changed_attributes:
        lengths = isaac_core_object.get_heights()

    world_interface.update_capsule_properties(
        prim_paths=[prim_path],
        axes=axes,
        radii=radii,
        lengths=lengths,
    )


def _update_cylinder_properties_from_prim(
    prim_path: str,
    prim: usdrt.Usd.Prim,
    world_interface: WorldInterface,
    rt_change_tracker: usdrt.Rt.ChangeTracker,
):
    """Update cylinder properties in the planning world interface.

    Args:
        prim_path: Path to the cylinder prim.
        prim: USDRT prim object.
        world_interface: Planning world interface to update.
        rt_change_tracker: USDRT change tracker for monitoring changes.
    """
    axes = None
    radii = None
    lengths = None

    cylinder_schema = usdrt.UsdGeom.Cylinder(prim)
    changed_attributes = rt_change_tracker.GetChangedAttributes(prim)

    isaac_core_object = Cylinder(paths=prim_path)

    if cylinder_schema.GetAxisAttr().GetName() in changed_attributes:
        axes = isaac_core_object.get_axes()

    if cylinder_schema.GetRadiusAttr().GetName() in changed_attributes:
        radii = isaac_core_object.get_radii()

    if cylinder_schema.GetHeightAttr().GetName() in changed_attributes:
        lengths = isaac_core_object.get_heights()

    world_interface.update_cylinder_properties(
        prim_paths=[prim_path],
        axes=axes,
        radii=radii,
        lengths=lengths,
    )


def _update_mesh_properties_from_prim(
    prim_path: str,
    prim: usdrt.Usd.Prim,
    world_interface: WorldInterface,
    rt_change_tracker: usdrt.Rt.ChangeTracker,
):
    """Update mesh properties in the planning world interface.

    Args:
        prim_path: Path to the mesh prim.
        prim: USDRT prim object.
        world_interface: Planning world interface to update.
        rt_change_tracker: USDRT change tracker for monitoring changes.
    """
    raise RuntimeError("updating mesh properties is not currently supported by Isaac Sim.")


def _update_triangulated_mesh_properties_from_prim(
    prim_path: str,
    prim: usdrt.Usd.Prim,
    world_interface: WorldInterface,
    rt_change_tracker: usdrt.Rt.ChangeTracker,
):
    """Update triangulated mesh properties in the planning world interface.

    Args:
        prim_path: Path to the mesh prim.
        prim: USDRT prim object.
        world_interface: Planning world interface to update.
        rt_change_tracker: USDRT change tracker for monitoring changes.
    """
    raise RuntimeError("updating triangulated mesh properties is not currently supported by Isaac Sim.")


def _update_oriented_bounding_box_properties_from_prim(
    prim_path: str,
    prim: usdrt.Usd.Prim,
    world_interface: WorldInterface,
    rt_change_tracker: usdrt.Rt.ChangeTracker,
):
    """Update oriented bounding box properties in the planning world interface.

    Args:
        prim_path: Path to the prim.
        prim: USDRT prim object.
        world_interface: Planning world interface to update.
        rt_change_tracker: USDRT change tracker for monitoring changes.

    Raises:
        RuntimeError: This operation is not currently supported.
    """
    raise RuntimeError("updating oriented bounding box properties is not currently supported by Isaac Sim.")


_UPDATE_PROPERTIES_CALLBACK_MAP = {
    ObstacleRepresentation.SPHERE: _update_sphere_properties_from_prim,
    ObstacleRepresentation.CUBE: _update_cube_properties_from_prim,
    ObstacleRepresentation.CONE: _update_cone_properties_from_prim,
    ObstacleRepresentation.PLANE: _update_plane_properties_from_prim,
    ObstacleRepresentation.CAPSULE: _update_capsule_properties_from_prim,
    ObstacleRepresentation.CYLINDER: _update_cylinder_properties_from_prim,
    ObstacleRepresentation.MESH: _update_mesh_properties_from_prim,
    ObstacleRepresentation.TRIANGULATED_MESH: _update_triangulated_mesh_properties_from_prim,
    ObstacleRepresentation.OBB: _update_oriented_bounding_box_properties_from_prim,
    # TODO:
    # SIGNED_DISTANCE_FIELD:
    # CONVEX_HULL:
    # BOUNDING_SPHERE:
    # CONVEX_DECOMPOSITION:
}


TWorldInterface = TypeVar("TWorldInterface", bound=WorldInterface)


class WorldBinding(Generic[TWorldInterface]):
    """Binding that mirrors tracked USD prims into a planning world interface.

    This class observes specified USD prims on the stage and synchronizes their
    transforms, collision states, and shape properties to a planning world
    implementation. It uses USDRT change tracking for efficient updates.

    Args:
        world_interface: World implementation to populate and update.
        obstacle_strategy: Strategy used to select obstacle representations per prim.
        tracked_prims: Prim paths to track in the USD stage.
        tracked_collision_api: Collision API which is tracked for enable/disable signal.

    Example:

    .. code-block:: python

        from isaacsim.robot_motion.experimental.motion_generation import (
            ObstacleStrategy,
            TrackableApi,
            WorldBinding,
        )
        from isaacsim.robot_motion.experimental.motion_generation.tests.mirror_world_interface import (
            MirrorWorldInterface, # your planning world interface goes here!
        )

        world_binding = WorldBinding(
            world_interface=MirrorWorldInterface(),
            obstacle_strategy=ObstacleStrategy(),
            tracked_prims=["/World/Sphere"],
            tracked_collision_api=TrackableApi.PHYSICS_COLLISION,
        )
    """

    def __init__(
        self,
        world_interface: TWorldInterface,
        obstacle_strategy: ObstacleStrategy,
        tracked_prims: list[str],
        tracked_collision_api: TrackableApi,
    ):
        # TODO: extend support to Motion Generation Collision once it is available.
        if tracked_collision_api is not TrackableApi.PHYSICS_COLLISION:
            raise ValueError(f"No collision API other than PHYSICS_COLLISION is currently supported.")

        self._tracked_collision_api = tracked_collision_api
        self._world_interface = world_interface
        self._obstacle_strategy = obstacle_strategy
        self._tracked_prims = tracked_prims
        self._stage = stage_utils.get_current_stage(backend="usdrt")
        self._rt_change_tracker: usdrt.Rt.ChangeTracker | None = None
        self._initialized = False

    def initialize(self):
        """Initialize tracking and populate the planning world from tracked prims.

        Raises:
            RuntimeError: If already initialized.
            RuntimeError: If any tracked prim lacks the CollisionAPI.
            RuntimeError: If any tracked prim path is invalid in the stage.
            AssertionError: If any ancestor prims of the tracked prims have non-unity
                scaling, which would cause issues with world-space operations.

        Example:

        .. code-block:: python

            from isaacsim.robot_motion.experimental.motion_generation import (
                ObstacleStrategy,
                TrackableApi,
                WorldBinding,
            )
            from isaacsim.robot_motion.experimental.motion_generation.tests.mirror_world_interface import (
                MirrorWorldInterface,
            )

            world_binding = WorldBinding(
                world_interface=MirrorWorldInterface(),
                obstacle_strategy=ObstacleStrategy(),
                tracked_prims=["/World/Sphere"],
                tracked_collision_api=TrackableApi.PHYSICS_COLLISION,
            )
            world_binding.initialize()
        """
        if self._initialized:
            raise RuntimeError(
                "WorldBinding is already initialized, and does not support re-initialization. If you need to track new prims, create a new WorldBinding instance instead. Otherwise, call synchronize() to update the world binding."
            )

        if len(self._tracked_prims) == 0:
            self._initialized = True
            return

        # Check that all of the tracked prims have the necessary APIs applied:
        if not all([prim_utils.has_api(p, _COLLISION_APIS[self._tracked_collision_api]) for p in self._tracked_prims]):
            prims_without_collision_api = [
                p
                for p in self._tracked_prims
                if not prim_utils.has_api(p, _COLLISION_APIS[self._tracked_collision_api])
            ]
            raise RuntimeError(
                f"The following prims do not have {_COLLISION_APIS[self._tracked_collision_api]} applied: {prims_without_collision_api}"
            )

        # NOTE: these prims are USDRT, as we will use them to do RT tracking of the
        # changing poses and attributes.
        self._rt_change_tracker = usdrt.Rt.ChangeTracker(self._stage)
        prims = [self._stage.GetPrimAtPath(usdrt.Sdf.Path(p)) for p in self._tracked_prims]  # usdrt

        # Check that all of the tracked prims are valid:
        valid_prims = [prim.IsValid() for prim in prims]
        if not all(valid_prims):
            invalid_prims = [prim_path for prim_path, valid in zip(self._tracked_prims, valid_prims) if not valid]
            raise RuntimeError(f"The following paths do not correspond to valid prims in the stage: {invalid_prims}")

        # with certainty, we will want to track the transforms, the
        # collision enabled outputs, and the local-transform which is
        # used to set the object scales:
        self._rt_change_tracker.TrackAttribute(_TRANSFORM_TOKEN)
        self._rt_change_tracker.TrackAttribute(_COLLISION_ENABLED_TOKENS[self._tracked_collision_api])
        self._rt_change_tracker.TrackAttribute(_LOCAL_TRANSFORM_TOKEN)

        # We need to check that all ancestor prims have NO scaling about any axes.
        # This guarantees that no shearing can occur and ensures local_scale == world_scale.
        invalid_ancestors = scene_validation.find_all_invalid_ancestors(prim_paths=self._tracked_prims)
        if len(invalid_ancestors) != 0:
            raise AssertionError(f"The following ancestor prims have non-unity scaling.\n{invalid_ancestors}")

        for prim, prim_path in zip(prims, self._tracked_prims):
            obstacle_configuration = self._obstacle_strategy.get_obstacle_configuration(prim_path)
            _ADD_OBJECT_CALLBACK_MAP[obstacle_configuration.representation](
                prim_path=prim_path,
                prim=prim,
                world_interface=self._world_interface,
                obstacle_configuration=obstacle_configuration,
                rt_change_tracker=self._rt_change_tracker,
                collision_api=self._tracked_collision_api,
            )

        self._initialized = True

    def synchronize(self):
        """Synchronize tracked prim updates into the planning world.

        Raises:
            RuntimeError: If the world binding has not been initialized.

        Example:

        .. code-block:: python

            from isaacsim.robot_motion.experimental.motion_generation import (
                ObstacleStrategy,
                TrackableApi,
                WorldBinding,
            )
            from isaacsim.robot_motion.experimental.motion_generation.tests.mirror_world_interface import (
                MirrorWorldInterface,
            )

            world_binding = WorldBinding(
                world_interface=MirrorWorldInterface(),
                obstacle_strategy=ObstacleStrategy(),
                tracked_prims=[],
                tracked_collision_api=TrackableApi.PHYSICS_COLLISION,
            )
            world_binding.initialize()
            world_binding.synchronize()
        """
        # TODO: this can be implemented much more efficiently.
        if not self._initialized:
            raise RuntimeError("WorldBinding is not initialized. Call initialize() first.")

        if len(self._tracked_prims) == 0:
            return

        # Makes use of the usdrt.Rt.ChangeTracker, as documented here:
        # https://docs.omniverse.nvidia.com/kit/docs/usdrt/latest/_apidocs/classusdrt_1_1RtChangeTracker.html
        if not self._rt_change_tracker.HasChanges():
            return

        common_tokens_to_update_functions_map = {
            _TRANSFORM_TOKEN: _update_prim_transforms,
            _LOCAL_TRANSFORM_TOKEN: _update_prim_scales,
            _COLLISION_ENABLED_TOKENS[TrackableApi.PHYSICS_COLLISION]: _update_prim_physics_collision_enables,
            # TODO: add other Motion Generation Collision APIs here when they are supported.
        }

        def _prim_token_changed(prim_path, token):
            prim = self._stage.GetPrimAtPath(usdrt.Sdf.Path(prim_path))
            prim_changed_attrs = self._rt_change_tracker.GetChangedAttributes(prim)
            return token in prim_changed_attrs

        # Update all of the common tokens:
        for token in common_tokens_to_update_functions_map:
            objects_to_update = [p for p in self._tracked_prims if _prim_token_changed(p, token)]
            if len(objects_to_update) > 0:
                common_tokens_to_update_functions_map[token](
                    prim_paths=objects_to_update,
                    world_interface=self._world_interface,
                )

        # Update shape-level properties which have changed:
        # loop through the collision_prims, and update which prims have changed:
        for prim_path in self._tracked_prims:
            # if there are no updates, ignore.
            prim = self._stage.GetPrimAtPath(usdrt.Sdf.Path(prim_path))
            if not self._rt_change_tracker.PrimChanged(prim):
                continue

            # Check if anything other than the transform or collision enabled has changed:
            changed_attributes = self._rt_change_tracker.GetChangedAttributes(prim)
            if set(changed_attributes).issubset(set(common_tokens_to_update_functions_map.keys())):
                continue

            obstacle_configuration = self._obstacle_strategy.get_obstacle_configuration(prim_path)
            _UPDATE_PROPERTIES_CALLBACK_MAP[obstacle_configuration.representation](
                prim_path=prim_path,
                prim=prim,
                world_interface=self._world_interface,
                rt_change_tracker=self._rt_change_tracker,
            )

        # clear the recorded changes:
        self._rt_change_tracker.ClearChanges()

    def get_world_interface(self) -> TWorldInterface:
        """Return the planning world interface instance.

        Returns:
            The world interface used by this binding.

        Example:

        .. code-block:: python

            from isaacsim.robot_motion.experimental.motion_generation import (
                ObstacleStrategy,
                TrackableApi,
                WorldBinding,
            )
            from isaacsim.robot_motion.experimental.motion_generation.tests.mirror_world_interface import (
                MirrorWorldInterface,
            )

            world_binding = WorldBinding(
                world_interface=MirrorWorldInterface(),
                obstacle_strategy=ObstacleStrategy(),
                tracked_prims=[],
                tracked_collision_api=TrackableApi.PHYSICS_COLLISION,
            )
            world_interface = world_binding.get_world_interface()
        """
        return self._world_interface
