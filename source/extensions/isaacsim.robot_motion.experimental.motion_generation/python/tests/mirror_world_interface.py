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

from dataclasses import dataclass
from typing import Any, Literal

import warp as wp
from isaacsim.robot_motion.experimental.motion_generation import WorldInterface


@dataclass
class MirrorSphere:
    radius: Any
    scale: Any
    safety_tolerance: Any
    pose: tuple[Any, Any]
    enabled: Any


@dataclass
class MirrorCube:
    size: Any
    scale: Any
    safety_tolerance: Any
    pose: tuple[Any, Any]
    enabled: Any


@dataclass
class MirrorCone:
    axis: Any
    radius: Any
    length: Any
    scale: Any
    safety_tolerance: Any
    pose: tuple[Any, Any]
    enabled: Any


@dataclass
class MirrorPlane:
    axis: Any
    length: Any
    width: Any
    scale: Any
    safety_tolerance: Any
    pose: tuple[Any, Any]
    enabled: Any


@dataclass
class MirrorCapsule:
    axis: Any
    radius: Any
    length: Any
    scale: Any
    safety_tolerance: Any
    pose: tuple[Any, Any]
    enabled: Any


@dataclass
class MirrorCylinder:
    axis: Any
    radius: Any
    length: Any
    scale: Any
    safety_tolerance: Any
    pose: tuple[Any, Any]
    enabled: Any


@dataclass
class MirrorMesh:
    points: Any
    face_vertex_indices: Any
    face_vertex_counts: Any
    normals: Any
    scale: Any
    safety_tolerance: Any
    pose: tuple[Any, Any]
    enabled: Any


@dataclass
class MirrorTriangulatedMesh:
    points: Any
    face_vertex_indices: Any
    scale: Any
    safety_tolerance: Any
    pose: tuple[Any, Any]
    enabled: Any


@dataclass
class MirrorOrientedBoundingBox:
    center: Any
    rotation: Any
    half_side_length: Any
    scale: Any
    safety_tolerance: Any
    pose: tuple[Any, Any]
    enabled: Any


class MirrorWorldInterface(WorldInterface):
    def __init__(self):
        self.collision_objects: dict[str, Any] = {}

    def add_spheres(
        self,
        prim_paths: list[str],
        radii: wp.array,
        scales: wp.array,
        safety_tolerances: wp.array,
        poses: tuple[wp.array, wp.array],
        enabled_array: wp.array,
    ):
        radii_np = radii.numpy()
        scales_np = scales.numpy()
        positions_np = poses[0].numpy()
        quaternions_np = poses[1].numpy()
        enabled_np = enabled_array.numpy()
        safety_tolerances_np = safety_tolerances.numpy()
        for index, prim_path in enumerate(prim_paths):
            self.collision_objects[prim_path] = MirrorSphere(
                radius=radii_np[index],
                scale=scales_np[index],
                safety_tolerance=safety_tolerances_np[index],
                pose=(positions_np[index], quaternions_np[index]),
                enabled=enabled_np[index],
            )

    def add_cubes(
        self,
        prim_paths: list[str],
        sizes: wp.array,
        scales: wp.array,
        safety_tolerances: wp.array,
        poses: tuple[wp.array, wp.array],
        enabled_array: wp.array,
    ):
        sizes_np = sizes.numpy()
        scales_np = scales.numpy()
        positions_np = poses[0].numpy()
        quaternions_np = poses[1].numpy()
        enabled_np = enabled_array.numpy()
        safety_tolerances_np = safety_tolerances.numpy()
        for index, prim_path in enumerate(prim_paths):
            self.collision_objects[prim_path] = MirrorCube(
                size=sizes_np[index],
                scale=scales_np[index],
                safety_tolerance=safety_tolerances_np[index],
                pose=(positions_np[index], quaternions_np[index]),
                enabled=enabled_np[index],
            )

    def add_cones(
        self,
        prim_paths: list[str],
        axes: list[Literal["X", "Y", "Z"]],
        radii: wp.array,
        lengths: wp.array,
        scales: wp.array,
        safety_tolerances: wp.array,
        poses: tuple[wp.array, wp.array],
        enabled_array: wp.array,
    ):
        radii_np = radii.numpy()
        lengths_np = lengths.numpy()
        scales_np = scales.numpy()
        positions_np = poses[0].numpy()
        quaternions_np = poses[1].numpy()
        enabled_np = enabled_array.numpy()
        safety_tolerances_np = safety_tolerances.numpy()
        for index, prim_path in enumerate(prim_paths):
            self.collision_objects[prim_path] = MirrorCone(
                axis=axes[index],
                radius=radii_np[index],
                length=lengths_np[index],
                scale=scales_np[index],
                safety_tolerance=safety_tolerances_np[index],
                pose=(positions_np[index], quaternions_np[index]),
                enabled=enabled_np[index],
            )

    def add_planes(
        self,
        prim_paths: list[str],
        axes: list[Literal["X", "Y", "Z"]],
        lengths: wp.array,
        widths: wp.array,
        scales: wp.array,
        safety_tolerances: wp.array,
        poses: tuple[wp.array, wp.array],
        enabled_array: wp.array,
    ):
        lengths_np = lengths.numpy()
        widths_np = widths.numpy()
        scales_np = scales.numpy()
        positions_np = poses[0].numpy()
        quaternions_np = poses[1].numpy()
        enabled_np = enabled_array.numpy()
        safety_tolerances_np = safety_tolerances.numpy()
        for index, prim_path in enumerate(prim_paths):
            self.collision_objects[prim_path] = MirrorPlane(
                axis=axes[index],
                length=lengths_np[index],
                width=widths_np[index],
                scale=scales_np[index],
                safety_tolerance=safety_tolerances_np[index],
                pose=(positions_np[index], quaternions_np[index]),
                enabled=enabled_np[index],
            )

    def add_capsules(
        self,
        prim_paths: list[str],
        axes: list[Literal["X", "Y", "Z"]],
        radii: wp.array,
        lengths: wp.array,
        scales: wp.array,
        safety_tolerances: wp.array,
        poses: tuple[wp.array, wp.array],
        enabled_array: wp.array,
    ):
        radii_np = radii.numpy()
        lengths_np = lengths.numpy()
        scales_np = scales.numpy()
        positions_np = poses[0].numpy()
        quaternions_np = poses[1].numpy()
        enabled_np = enabled_array.numpy()
        safety_tolerances_np = safety_tolerances.numpy()
        for index, prim_path in enumerate(prim_paths):
            self.collision_objects[prim_path] = MirrorCapsule(
                axis=axes[index],
                radius=radii_np[index],
                length=lengths_np[index],
                scale=scales_np[index],
                safety_tolerance=safety_tolerances_np[index],
                pose=(positions_np[index], quaternions_np[index]),
                enabled=enabled_np[index],
            )

    def add_cylinders(
        self,
        prim_paths: list[str],
        axes: list[Literal["X", "Y", "Z"]],
        radii: wp.array,
        lengths: wp.array,
        scales: wp.array,
        safety_tolerances: wp.array,
        poses: tuple[wp.array, wp.array],
        enabled_array: wp.array,
    ):
        radii_np = radii.numpy()
        lengths_np = lengths.numpy()
        scales_np = scales.numpy()
        positions_np = poses[0].numpy()
        quaternions_np = poses[1].numpy()
        enabled_np = enabled_array.numpy()
        safety_tolerances_np = safety_tolerances.numpy()
        for index, prim_path in enumerate(prim_paths):
            self.collision_objects[prim_path] = MirrorCylinder(
                axis=axes[index],
                radius=radii_np[index],
                length=lengths_np[index],
                scale=scales_np[index],
                safety_tolerance=safety_tolerances_np[index],
                pose=(positions_np[index], quaternions_np[index]),
                enabled=enabled_np[index],
            )

    def add_meshes(
        self,
        prim_paths: list[str],
        points: list[wp.array],
        face_vertex_indices: list[wp.array],
        face_vertex_counts: list[wp.array],
        normals: list[wp.array],
        scales: wp.array,
        safety_tolerances: wp.array,
        poses: tuple[wp.array, wp.array],
        enabled_array: wp.array,
    ):
        scales_np = scales.numpy()
        positions_np = poses[0].numpy()
        quaternions_np = poses[1].numpy()
        enabled_np = enabled_array.numpy()
        safety_tolerances_np = safety_tolerances.numpy()
        for index, prim_path in enumerate(prim_paths):
            self.collision_objects[prim_path] = MirrorMesh(
                points=points[index],
                face_vertex_indices=face_vertex_indices[index],
                face_vertex_counts=face_vertex_counts[index],
                normals=normals[index],
                scale=scales_np[index],
                safety_tolerance=safety_tolerances_np[index],
                pose=(positions_np[index], quaternions_np[index]),
                enabled=enabled_np[index],
            )

    def add_triangulated_meshes(
        self,
        prim_paths: list[str],
        points: list[wp.array],
        face_vertex_indices: list[wp.array],
        scales: wp.array,
        safety_tolerances: wp.array,
        poses: tuple[wp.array, wp.array],
        enabled_array: wp.array,
    ):
        scales_np = scales.numpy()
        positions_np = poses[0].numpy()
        quaternions_np = poses[1].numpy()
        enabled_np = enabled_array.numpy()
        safety_tolerances_np = safety_tolerances.numpy()
        for index, prim_path in enumerate(prim_paths):
            self.collision_objects[prim_path] = MirrorTriangulatedMesh(
                points=points[index],
                face_vertex_indices=face_vertex_indices[index],
                scale=scales_np[index],
                safety_tolerance=safety_tolerances_np[index],
                pose=(positions_np[index], quaternions_np[index]),
                enabled=enabled_np[index],
            )

    def add_oriented_bounding_boxes(
        self,
        prim_paths: list[str],
        centers: wp.array,
        rotations: wp.array,
        half_side_lengths: wp.array,
        scales: wp.array,
        safety_tolerances: wp.array,
        poses: tuple[wp.array, wp.array],
        enabled_array: wp.array,
    ):
        scales_np = scales.numpy()
        positions_np = poses[0].numpy()
        quaternions_np = poses[1].numpy()
        enabled_np = enabled_array.numpy()
        safety_tolerances_np = safety_tolerances.numpy()
        centers_np = centers.numpy()
        rotations_np = rotations.numpy()
        half_side_lengths_np = half_side_lengths.numpy()
        for index, prim_path in enumerate(prim_paths):
            self.collision_objects[prim_path] = MirrorOrientedBoundingBox(
                center=centers_np[index],
                rotation=rotations_np[index],
                half_side_length=half_side_lengths_np[index],
                scale=scales_np[index],
                safety_tolerance=safety_tolerances_np[index],
                pose=(positions_np[index], quaternions_np[index]),
                enabled=enabled_np[index],
            )

    def update_obstacle_transforms(
        self,
        prim_paths: list[str],
        poses: tuple[wp.array, wp.array],
    ):
        positions_np = poses[0].numpy()
        quaternions_np = poses[1].numpy()
        for index, prim_path in enumerate(prim_paths):
            self.collision_objects[prim_path].pose = (positions_np[index], quaternions_np[index])

    def update_obstacle_enables(
        self,
        prim_paths: list[str],
        enabled_array: wp.array,
    ):
        enabled_np = enabled_array.numpy()
        for index, prim_path in enumerate(prim_paths):
            self.collision_objects[prim_path].enabled = enabled_np[index]

    def update_obstacle_scales(
        self,
        prim_paths: list[str],
        scales: wp.array,
    ):
        scales_np = scales.numpy()
        for index, prim_path in enumerate(prim_paths):
            self.collision_objects[prim_path].scale = scales_np[index]

    def update_sphere_properties(
        self,
        prim_paths: list[str],
        radii: wp.array | None,
    ):
        radii_np = radii.numpy() if radii is not None else None
        for index, prim_path in enumerate(prim_paths):
            if radii_np is not None:
                self.collision_objects[prim_path].radius = radii_np[index]

    def update_cube_properties(
        self,
        prim_paths: list[str],
        sizes: wp.array | None,
    ):
        sizes_np = sizes.numpy() if sizes is not None else None
        for index, prim_path in enumerate(prim_paths):
            if sizes_np is not None:
                self.collision_objects[prim_path].size = sizes_np[index]

    def update_cone_properties(
        self,
        prim_paths: list[str],
        axes: list[Literal["X", "Y", "Z"]] | None,
        radii: wp.array | None,
        lengths: wp.array | None,
    ):
        radii_np = radii.numpy() if radii is not None else None
        lengths_np = lengths.numpy() if lengths is not None else None
        for index, prim_path in enumerate(prim_paths):
            if axes is not None:
                self.collision_objects[prim_path].axis = axes[index]
            if radii_np is not None:
                self.collision_objects[prim_path].radius = radii_np[index]
            if lengths_np is not None:
                self.collision_objects[prim_path].length = lengths_np[index]

    def update_plane_properties(
        self,
        prim_paths: list[str],
        axes: list[Literal["X", "Y", "Z"]] | None,
        lengths: wp.array | None,
        widths: wp.array | None,
    ):
        lengths_np = lengths.numpy() if lengths is not None else None
        widths_np = widths.numpy() if widths is not None else None
        for index, prim_path in enumerate(prim_paths):
            if axes is not None:
                self.collision_objects[prim_path].axis = axes[index]
            if lengths_np is not None:
                self.collision_objects[prim_path].length = lengths_np[index]
            if widths_np is not None:
                self.collision_objects[prim_path].width = widths_np[index]

    def update_capsule_properties(
        self,
        prim_paths: list[str],
        axes: list[Literal["X", "Y", "Z"]] | None,
        radii: wp.array | None,
        lengths: wp.array | None,
    ):
        radii_np = radii.numpy() if radii is not None else None
        lengths_np = lengths.numpy() if lengths is not None else None
        for index, prim_path in enumerate(prim_paths):
            if axes is not None:
                self.collision_objects[prim_path].axis = axes[index]
            if radii_np is not None:
                self.collision_objects[prim_path].radius = radii_np[index]
            if lengths_np is not None:
                self.collision_objects[prim_path].length = lengths_np[index]

    def update_cylinder_properties(
        self,
        prim_paths: list[str],
        axes: list[Literal["X", "Y", "Z"]] | None,
        radii: wp.array | None,
        lengths: wp.array | None,
    ):
        radii_np = radii.numpy() if radii is not None else None
        lengths_np = lengths.numpy() if lengths is not None else None
        for index, prim_path in enumerate(prim_paths):
            if axes is not None:
                self.collision_objects[prim_path].axis = axes[index]
            if radii_np is not None:
                self.collision_objects[prim_path].radius = radii_np[index]
            if lengths_np is not None:
                self.collision_objects[prim_path].length = lengths_np[index]

    def update_mesh_properties(
        self,
        prim_paths: list[str],
        points: list[wp.array] | None,
        face_vertex_indices: list[wp.array] | None,
        face_vertex_counts: list[wp.array] | None,
        normals: list[wp.array] | None,
    ):
        for index, prim_path in enumerate(prim_paths):
            if points is not None:
                self.collision_objects[prim_path].points = points[index]
            if face_vertex_indices is not None:
                self.collision_objects[prim_path].face_vertex_indices = face_vertex_indices[index]
            if face_vertex_counts is not None:
                self.collision_objects[prim_path].face_vertex_counts = face_vertex_counts[index]
            if normals is not None:
                self.collision_objects[prim_path].normals = normals[index]

    def update_triangulated_mesh_properties(
        self,
        prim_paths: list[str],
        points: list[wp.array] | None,
        face_vertex_indices: list[wp.array] | None,
    ):
        for index, prim_path in enumerate(prim_paths):
            if points is not None:
                self.collision_objects[prim_path].points = points[index]
            if face_vertex_indices is not None:
                self.collision_objects[prim_path].face_vertex_indices = face_vertex_indices[index]

    def update_oriented_bounding_box_properties(
        self,
        prim_paths: list[str],
        centers: wp.array | None,
        rotations: wp.array | None,
        half_side_lengths: wp.array | None,
    ):
        centers_np = centers.numpy() if centers is not None else None
        rotations_np = rotations.numpy() if rotations is not None else None
        half_side_lengths_np = half_side_lengths.numpy() if half_side_lengths is not None else None
        for index, prim_path in enumerate(prim_paths):
            if centers_np is not None:
                self.collision_objects[prim_path].center = centers_np[index]
            if rotations_np is not None:
                self.collision_objects[prim_path].rotation = rotations_np[index]
            if half_side_lengths_np is not None:
                self.collision_objects[prim_path].half_side_length = half_side_lengths_np[index]
