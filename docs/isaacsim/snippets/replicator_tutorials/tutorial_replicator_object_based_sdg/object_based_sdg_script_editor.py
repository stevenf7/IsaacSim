# SPDX-FileCopyrightText: Copyright (c) 2023-2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
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

import asyncio
import os
import random
import time
from itertools import chain

import carb.settings
import numpy as np
import omni.kit.app
import omni.replicator.core as rep
import omni.timeline
import omni.usd
from isaacsim.core.experimental.utils.semantics import add_labels, remove_all_labels, upgrade_prim_semantics_to_labels
from isaacsim.storage.native import get_assets_root_path
from omni.kit.viewport.utility import get_active_viewport
from omni.physx import get_physx_interface, get_physx_scene_query_interface
from pxr import Gf, PhysxSchema, Sdf, Usd, UsdGeom, UsdPhysics


def add_colliders(root_prim: Usd.Prim) -> None:
    """Enable collisions on the asset (without rigid body dynamics the asset will be static)."""
    for desc_prim in Usd.PrimRange(root_prim):
        if desc_prim.IsA(UsdGeom.Mesh) or desc_prim.IsA(UsdGeom.Gprim):
            if not desc_prim.HasAPI(UsdPhysics.CollisionAPI):
                collision_api = UsdPhysics.CollisionAPI.Apply(desc_prim)
            else:
                collision_api = UsdPhysics.CollisionAPI(desc_prim)
            collision_api.CreateCollisionEnabledAttr(True)
            if not desc_prim.HasAPI(PhysxSchema.PhysxCollisionAPI):
                physx_collision_api = PhysxSchema.PhysxCollisionAPI.Apply(desc_prim)
            else:
                physx_collision_api = PhysxSchema.PhysxCollisionAPI(desc_prim)
            physx_collision_api.CreateContactOffsetAttr(0.001)
            physx_collision_api.CreateRestOffsetAttr(0.0)
        if desc_prim.IsA(UsdGeom.Mesh):
            if not desc_prim.HasAPI(UsdPhysics.MeshCollisionAPI):
                mesh_collision_api = UsdPhysics.MeshCollisionAPI.Apply(desc_prim)
            else:
                mesh_collision_api = UsdPhysics.MeshCollisionAPI(desc_prim)
            mesh_collision_api.CreateApproximationAttr().Set("convexHull")


def create_collision_box_walls(
    stage: Usd.Stage,
    path: str,
    width: float,
    depth: float,
    height: float,
    thickness: float = 0.5,
    visible: bool = False,
) -> None:
    """Create a collision box area wrapping the given working area with origin at (0, 0, 0)."""
    walls = [
        ("floor", (0, 0, (height + thickness) / -2.0), (width, depth, thickness)),
        ("ceiling", (0, 0, (height + thickness) / 2.0), (width, depth, thickness)),
        ("left_wall", ((width + thickness) / -2.0, 0, 0), (thickness, depth, height)),
        ("right_wall", ((width + thickness) / 2.0, 0, 0), (thickness, depth, height)),
        ("front_wall", (0, (depth + thickness) / 2.0, 0), (width, thickness, height)),
        ("back_wall", (0, (depth + thickness) / -2.0, 0), (width, thickness, height)),
    ]
    for name, location, size in walls:
        prim = stage.DefinePrim(f"{path}/{name}", "Cube")
        scale = (size[0] / 2.0, size[1] / 2.0, size[2] / 2.0)
        rep.functional.modify.pose(prim, position_value=location, scale_value=scale)
        add_colliders(prim)
        if not visible:
            UsdGeom.Imageable(prim).MakeInvisible()


def get_random_transform_values(
    loc_min=(0, 0, 0), loc_max=(1, 1, 1), rot_min=(0, 0, 0), rot_max=(360, 360, 360), scale_min_max=(0.1, 1.0)
):
    """Create random transformation values for location, rotation, and scale."""
    location = (
        random.uniform(loc_min[0], loc_max[0]),
        random.uniform(loc_min[1], loc_max[1]),
        random.uniform(loc_min[2], loc_max[2]),
    )
    rotation = (
        random.uniform(rot_min[0], rot_max[0]),
        random.uniform(rot_min[1], rot_max[1]),
        random.uniform(rot_min[2], rot_max[2]),
    )
    scale = tuple([random.uniform(scale_min_max[0], scale_min_max[1])] * 3)
    return location, rotation, scale


def get_random_pose_on_sphere(origin, radius, camera_forward_axis=(0, 0, -1)):
    """Generate a random pose on a sphere looking at the origin."""
    origin = Gf.Vec3f(origin)
    camera_forward_axis = Gf.Vec3f(camera_forward_axis)
    theta = np.random.uniform(0, 2 * np.pi)
    phi = np.arcsin(np.random.uniform(-1, 1))
    x = radius * np.cos(theta) * np.cos(phi)
    y = radius * np.sin(phi)
    z = radius * np.sin(theta) * np.cos(phi)
    location = origin + Gf.Vec3f(x, y, z)
    direction = origin - location
    direction_normalized = direction.GetNormalized()
    rotation = Gf.Rotation(Gf.Vec3d(camera_forward_axis), Gf.Vec3d(direction_normalized))
    orientation = Gf.Quatf(rotation.GetQuat())
    return location, orientation


def set_render_products_updates(render_products, enabled, include_viewport=False):
    """Enable or disable the render products and viewport rendering."""
    for rp in render_products:
        rp.hydra_texture.set_updates_enabled(enabled)
    if include_viewport:
        get_active_viewport().updates_enabled = enabled


def apply_velocities_towards_target(prims, target=(0, 0, 0), strength_range=(0.1, 1.0)):
    """Apply velocities to prims directing them towards a target point."""
    for prim in prims:
        loc = prim.GetAttribute("xformOp:translate").Get()
        strength = random.uniform(strength_range[0], strength_range[1])
        velocity = (
            (target[0] - loc[0]) * strength,
            (target[1] - loc[1]) * strength,
            (target[2] - loc[2]) * strength,
        )
        prim.GetAttribute("physics:velocity").Set(velocity)


def apply_random_velocities(prims, linear_range=(-2.5, 2.5), angular_range=(-45, 45)):
    """Apply random linear and angular velocities to prims."""
    for prim in prims:
        lin_vel = (
            random.uniform(linear_range[0], linear_range[1]),
            random.uniform(linear_range[0], linear_range[1]),
            random.uniform(linear_range[0], linear_range[1]),
        )
        ang_vel = (
            random.uniform(angular_range[0], angular_range[1]),
            random.uniform(angular_range[0], angular_range[1]),
            random.uniform(angular_range[0], angular_range[1]),
        )
        prim.GetAttribute("physics:velocity").Set(lin_vel)
        prim.GetAttribute("physics:angularVelocity").Set(ang_vel)


async def run_example_async(config: dict) -> None:
    """Run the object-based SDG example asynchronously."""
    assets_root_path = get_assets_root_path()
    stage = None

    # ENVIRONMENT
    env_url = config.get("env_url", "")
    if env_url:
        env_path = env_url if env_url.startswith("omniverse://") else assets_root_path + env_url
        omni.usd.get_context().open_stage(env_path)
        stage = omni.usd.get_context().get_stage()
        for prim in stage.Traverse():
            upgrade_prim_semantics_to_labels(prim, include_descendants=True)
            remove_all_labels(prim, include_descendants=True)
    else:
        omni.usd.get_context().new_stage()
        stage = omni.usd.get_context().get_stage()
        rep.functional.create.xform(name="World")
        rep.functional.create.distant_light(intensity=400.0, rotation=(0, 60, 0), name="DistantLight")

    working_area_size = config.get("working_area_size", (3, 3, 3))
    working_area_min = (working_area_size[0] / -2, working_area_size[1] / -2, working_area_size[2] / -2)
    working_area_max = (working_area_size[0] / 2, working_area_size[1] / 2, working_area_size[2] / 2)

    create_collision_box_walls(
        stage, "/World/CollisionWalls", working_area_size[0], working_area_size[1], working_area_size[2]
    )

    rep.functional.physics.create_physics_scene("/PhysicsScene", timeStepsPerSecond=60)
    physx_scene = PhysxSchema.PhysxSceneAPI.Apply(stage.GetPrimAtPath("/PhysicsScene"))

    # TRAINING ASSETS
    labeled_assets_and_properties = config.get("labeled_assets_and_properties", [])
    floating_labeled_prims = []
    falling_labeled_prims = []
    labeled_prims = []
    rep.functional.create.scope(name="Labeled", parent="/World")
    for obj in labeled_assets_and_properties:
        obj_url = obj.get("url", "")
        label = obj.get("label", "unknown")
        count = obj.get("count", 1)
        floating = obj.get("floating", False)
        scale_min_max = obj.get("randomize_scale", (1, 1))
        for i in range(count):
            rand_loc, rand_rot, rand_scale = get_random_transform_values(
                loc_min=working_area_min, loc_max=working_area_max, scale_min_max=scale_min_max
            )
            asset_path = obj_url if obj_url.startswith("omniverse://") else assets_root_path + obj_url
            prim = rep.functional.create.reference(
                usd_path=asset_path,
                parent="/World/Labeled",
                name=label,
                position=rand_loc,
                rotation=rand_rot,
                scale=rand_scale,
            )
            add_colliders(prim)
            rep.functional.physics.apply_rigid_body(prim, disableGravity=floating)
            add_labels(prim, labels=[label], taxonomy="class")
            if floating:
                floating_labeled_prims.append(prim)
            else:
                falling_labeled_prims.append(prim)
    labeled_prims = floating_labeled_prims + falling_labeled_prims

    # DISTRACTORS
    shape_distractors_types = config.get("shape_distractors_types", ["capsule", "cone", "cylinder", "sphere", "cube"])
    shape_distractors_scale_min_max = config.get("shape_distractors_scale_min_max", (0.02, 0.2))
    shape_distractors_num = config.get("shape_distractors_num", 350)
    shape_distractors = []
    floating_shape_distractors = []
    falling_shape_distractors = []
    for i in range(shape_distractors_num):
        rand_loc, rand_rot, rand_scale = get_random_transform_values(
            loc_min=working_area_min, loc_max=working_area_max, scale_min_max=shape_distractors_scale_min_max
        )
        rand_shape = random.choice(shape_distractors_types)
        prim_path = omni.usd.get_stage_next_free_path(stage, f"/World/Distractors/{rand_shape}", False)
        prim = stage.DefinePrim(prim_path, rand_shape.capitalize())
        rep.functional.modify.pose(prim, position_value=rand_loc, rotation_value=rand_rot, scale_value=rand_scale)
        disable_gravity = random.choice([True, False])
        add_colliders(prim)
        rep.functional.physics.apply_rigid_body(prim, disableGravity=disable_gravity)
        if disable_gravity:
            floating_shape_distractors.append(prim)
        else:
            falling_shape_distractors.append(prim)
        shape_distractors.append(prim)

    mesh_distactors_urls = config.get("mesh_distractors_urls", [])
    mesh_distactors_scale_min_max = config.get("mesh_distractors_scale_min_max", (0.1, 2.0))
    mesh_distactors_num = config.get("mesh_distractors_num", 10)
    mesh_distractors = []
    floating_mesh_distractors = []
    falling_mesh_distractors = []
    for i in range(mesh_distactors_num):
        rand_loc, rand_rot, rand_scale = get_random_transform_values(
            loc_min=working_area_min, loc_max=working_area_max, scale_min_max=mesh_distactors_scale_min_max
        )
        mesh_url = random.choice(mesh_distactors_urls)
        prim_name = os.path.basename(mesh_url).split(".")[0]
        asset_path = mesh_url if mesh_url.startswith("omniverse://") else assets_root_path + mesh_url
        prim = rep.functional.create.reference(
            usd_path=asset_path,
            parent="/World/Distractors",
            name=prim_name,
            position=rand_loc,
            rotation=rand_rot,
            scale=rand_scale,
        )
        disable_gravity = random.choice([True, False])
        add_colliders(prim)
        rep.functional.physics.apply_rigid_body(prim, disableGravity=disable_gravity)
        if disable_gravity:
            floating_mesh_distractors.append(prim)
        else:
            falling_mesh_distractors.append(prim)
        mesh_distractors.append(prim)
        upgrade_prim_semantics_to_labels(prim, include_descendants=True)
        remove_all_labels(prim, include_descendants=True)

    # REPLICATOR
    rep.set_global_seed(42)
    random.seed(42)
    rep.orchestrator.set_capture_on_play(False)
    carb.settings.get_settings().set("rtx/post/dlss/execMode", 2)

    cameras = []
    num_cameras = config.get("num_cameras", 1)
    camera_properties_kwargs = config.get("camera_properties_kwargs", {})
    rep.functional.create.scope(name="Cameras", parent="/World")
    for i in range(num_cameras):
        cam_prim = rep.functional.create.camera(parent="/World/Cameras", name="cam", **camera_properties_kwargs)
        cameras.append(cam_prim)

    camera_colliders = []
    camera_collider_radius = config.get("camera_collider_radius", 0)
    if camera_collider_radius > 0:
        for cam in cameras:
            cam_path = cam.GetPath()
            cam_collider = stage.DefinePrim(f"{cam_path}/CollisionSphere", "Sphere")
            cam_collider.GetAttribute("radius").Set(camera_collider_radius)
            rep.functional.physics.apply_collider(cam_collider)
            collision_api = UsdPhysics.CollisionAPI(cam_collider)
            collision_api.GetCollisionEnabledAttr().Set(False)
            UsdGeom.Imageable(cam_collider).MakeInvisible()
            camera_colliders.append(cam_collider)

    await omni.kit.app.get_app().next_update_async()

    render_products = []
    resolution = config.get("resolution", (640, 480))
    for cam in cameras:
        rp = rep.create.render_product(cam.GetPath(), resolution)
        render_products.append(rp)

    disable_render_products_between_captures = config.get("disable_render_products_between_captures", True)
    if disable_render_products_between_captures:
        set_render_products_updates(render_products, False, include_viewport=False)

    writer_type = config.get("writer_type", None)
    writer_kwargs = config.get("writer_kwargs", {})
    if out_dir := writer_kwargs.get("output_dir"):
        if not os.path.isabs(out_dir):
            out_dir = os.path.join(os.getcwd(), out_dir)
            writer_kwargs["output_dir"] = out_dir
        print(f"[SDG] Writing data to: {out_dir}")
    if writer_type is not None and len(render_products) > 0:
        writer = rep.writers.get(writer_type)
        writer.initialize(**writer_kwargs)
        writer.attach(render_products)

    # RANDOMIZERS
    def on_overlap_hit(hit) -> bool:
        prim = omni.usd.get_context().get_stage().GetPrimAtPath(str(hit.rigid_body))
        if prim not in camera_colliders:
            rand_vel = (random.uniform(-2, 2), random.uniform(-2, 2), random.uniform(4, 8))
            prim.GetAttribute("physics:velocity").Set(rand_vel)
        return True

    overlap_area_thickness = 0.1
    overlap_area_origin = (0, 0, (-working_area_size[2] / 2) + (overlap_area_thickness / 2))
    overlap_area_extent = (
        working_area_size[0] / 2 * 0.99,
        working_area_size[1] / 2 * 0.99,
        overlap_area_thickness / 2 * 0.99,
    )

    def on_physics_step(dt: float) -> None:
        get_physx_scene_query_interface().overlap_box(
            carb.Float3(overlap_area_extent),
            carb.Float3(overlap_area_origin),
            carb.Float4(0, 0, 0, 1),
            on_overlap_hit,
            False,
        )

    physx_sub = get_physx_interface().subscribe_physics_step_events(on_physics_step)

    camera_distance_to_target_min_max = config.get("camera_distance_to_target_min_max", (0.1, 0.5))
    camera_look_at_target_offset = config.get("camera_look_at_target_offset", 0.2)

    def randomize_camera_poses() -> None:
        for cam in cameras:
            target_asset = random.choice(labeled_prims)
            loc_offset = (
                random.uniform(-camera_look_at_target_offset, camera_look_at_target_offset),
                random.uniform(-camera_look_at_target_offset, camera_look_at_target_offset),
                random.uniform(-camera_look_at_target_offset, camera_look_at_target_offset),
            )
            target_loc = target_asset.GetAttribute("xformOp:translate").Get() + loc_offset
            distance = random.uniform(camera_distance_to_target_min_max[0], camera_distance_to_target_min_max[1])
            cam_loc, quat = get_random_pose_on_sphere(origin=target_loc, radius=distance)
            rep.functional.modify.pose(cam, position_value=cam_loc, rotation_value=quat)

    async def simulate_camera_collision_async(num_frames: int = 1) -> None:
        for cam_collider in camera_colliders:
            collision_api = UsdPhysics.CollisionAPI(cam_collider)
            collision_api.GetCollisionEnabledAttr().Set(True)
        if not timeline.is_playing():
            timeline.play()
        for _ in range(num_frames):
            await omni.kit.app.get_app().next_update_async()
        for cam_collider in camera_colliders:
            collision_api = UsdPhysics.CollisionAPI(cam_collider)
            collision_api.GetCollisionEnabledAttr().Set(False)

    with rep.trigger.on_custom_event(event_name="randomize_shape_distractor_colors"):
        shape_distractors_paths = [
            prim.GetPath() for prim in chain(floating_shape_distractors, falling_shape_distractors)
        ]
        shape_distractors_group = rep.create.group(shape_distractors_paths)
        with shape_distractors_group:
            rep.randomizer.color(colors=rep.distribution.uniform((0, 0, 0), (1, 1, 1)))

    with rep.trigger.on_custom_event(event_name="randomize_lights"):
        lights = rep.create.light(
            light_type="Sphere",
            color=rep.distribution.uniform((0, 0, 0), (1, 1, 1)),
            temperature=rep.distribution.normal(6500, 500),
            intensity=rep.distribution.normal(35000, 5000),
            position=rep.distribution.uniform(working_area_min, working_area_max),
            scale=rep.distribution.uniform(0.1, 1),
            count=3,
        )

    with rep.trigger.on_custom_event(event_name="randomize_dome_background"):
        dome_textures = [
            assets_root_path + "/NVIDIA/Assets/Skies/Indoor/autoshop_01_4k.hdr",
            assets_root_path + "/NVIDIA/Assets/Skies/Indoor/carpentry_shop_01_4k.hdr",
            assets_root_path + "/NVIDIA/Assets/Skies/Indoor/hotel_room_4k.hdr",
            assets_root_path + "/NVIDIA/Assets/Skies/Indoor/wooden_lounge_4k.hdr",
        ]
        dome_light = rep.create.light(light_type="Dome")
        with dome_light:
            rep.modify.attribute("inputs:texture:file", rep.distribution.choice(dome_textures))
            rep.randomizer.rotation()

    async def capture_with_motion_blur_and_pathtracing_async(
        duration: float = 0.05, num_samples: int = 8, spp: int = 64
    ) -> None:
        orig_physics_fps = physx_scene.GetTimeStepsPerSecondAttr().Get()
        target_physics_fps = 1 / duration * num_samples
        if target_physics_fps > orig_physics_fps:
            physx_scene.GetTimeStepsPerSecondAttr().Set(target_physics_fps)
        is_motion_blur_enabled = carb.settings.get_settings().get("/omni/replicator/captureMotionBlur")
        if not is_motion_blur_enabled:
            carb.settings.get_settings().set("/omni/replicator/captureMotionBlur", True)
        carb.settings.get_settings().set("/omni/replicator/pathTracedMotionBlurSubSamples", num_samples)
        prev_render_mode = carb.settings.get_settings().get("/rtx/rendermode")
        carb.settings.get_settings().set("/rtx/rendermode", "PathTracing")
        carb.settings.get_settings().set("/rtx/pathtracing/spp", spp)
        carb.settings.get_settings().set("/rtx/pathtracing/totalSpp", spp)
        carb.settings.get_settings().set("/rtx/pathtracing/optixDenoiser/enabled", 0)
        if not timeline.is_playing():
            timeline.play()
        await rep.orchestrator.step_async(delta_time=duration, pause_timeline=False)
        if target_physics_fps > orig_physics_fps:
            physx_scene.GetTimeStepsPerSecondAttr().Set(orig_physics_fps)
        carb.settings.get_settings().set("/omni/replicator/captureMotionBlur", is_motion_blur_enabled)
        carb.settings.get_settings().set("/rtx/rendermode", prev_render_mode)

    async def run_simulation_loop_async(duration: float) -> None:
        timeline = omni.timeline.get_timeline_interface()
        if not timeline.is_playing():
            timeline.play()
        elapsed_time = 0.0
        previous_time = timeline.get_current_time()
        while elapsed_time <= duration:
            await omni.kit.app.get_app().next_update_async()
            elapsed_time += timeline.get_current_time() - previous_time
            previous_time = timeline.get_current_time()

    # SDG
    num_frames = config.get("num_frames", 10)
    rt_subframes = config.get("rt_subframes", -1)
    sim_duration_between_captures = config.get("simulation_duration_between_captures", 0.025)

    rep.utils.send_og_event(event_name="randomize_shape_distractor_colors")
    rep.utils.send_og_event(event_name="randomize_dome_background")
    for _ in range(5):
        await omni.kit.app.get_app().next_update_async()

    timeline = omni.timeline.get_timeline_interface()
    timeline.set_start_time(0)
    timeline.set_end_time(1000000)
    timeline.set_looping(False)
    timeline.play()
    timeline.commit()
    await omni.kit.app.get_app().next_update_async()

    wall_time_start = time.perf_counter()

    for i in range(num_frames):
        if i % 3 == 0:
            randomize_camera_poses()
            if camera_colliders:
                await simulate_camera_collision_async(num_frames=4)
        if i % 10 == 0:
            apply_velocities_towards_target(list(chain(labeled_prims, shape_distractors, mesh_distractors)))
        if i % 5 == 0:
            rep.utils.send_og_event(event_name="randomize_lights")
        if i % 15 == 0:
            rep.utils.send_og_event(event_name="randomize_shape_distractor_colors")
        if i % 25 == 0:
            rep.utils.send_og_event(event_name="randomize_dome_background")
        if i % 17 == 0:
            apply_random_velocities(list(chain(floating_shape_distractors, floating_mesh_distractors)))

        if disable_render_products_between_captures:
            set_render_products_updates(render_products, True, include_viewport=False)

        print(f"[SDG] Capturing frame {i}/{num_frames}, at simulation time: {timeline.get_current_time():.2f}")
        if i % 5 == 0:
            await capture_with_motion_blur_and_pathtracing_async(duration=0.025, num_samples=8, spp=128)
        else:
            await rep.orchestrator.step_async(delta_time=0.0, rt_subframes=rt_subframes, pause_timeline=False)

        if disable_render_products_between_captures:
            set_render_products_updates(render_products, False, include_viewport=False)

        if sim_duration_between_captures > 0:
            await run_simulation_loop_async(sim_duration_between_captures)
        else:
            await omni.kit.app.get_app().next_update_async()

    await rep.orchestrator.wait_until_complete_async()

    wall_duration = time.perf_counter() - wall_time_start
    sim_duration = timeline.get_current_time()
    num_captures = num_frames * num_cameras
    print(
        f"[SDG] Captured {num_frames} frames, {num_captures} entries in {wall_duration:.2f} seconds.\n"
        f"\t Simulation duration: {sim_duration:.2f}\n"
    )

    physx_sub.unsubscribe()
    physx_sub = None
    await omni.kit.app.get_app().next_update_async()
    timeline.stop()


config = {
    "env_url": "",
    "working_area_size": (5, 5, 3),
    "rt_subframes": 4,
    "num_frames": 10,
    "num_cameras": 2,
    "camera_collider_radius": 1.25,
    "disable_render_products_between_captures": False,
    "simulation_duration_between_captures": 0.05,
    "resolution": (640, 480),
    "camera_properties_kwargs": {
        "focal_length": 24.0,
        "focus_distance": 400,
        "f_stop": 0.0,
        "clipping_range": (0.01, 10000),
    },
    "camera_look_at_target_offset": 0.15,
    "camera_distance_to_target_min_max": (0.25, 0.75),
    "writer_type": "PoseWriter",
    "writer_kwargs": {
        "output_dir": "_out_obj_based_sdg_pose_writer",
        "format": None,
        "use_subfolders": False,
        "write_debug_images": True,
        "skip_empty_frames": False,
    },
    "labeled_assets_and_properties": [
        {
            "url": "/Isaac/Props/YCB/Axis_Aligned/008_pudding_box.usd",
            "label": "pudding_box",
            "count": 5,
            "floating": True,
            "scale_min_max": (0.85, 1.25),
        },
        {
            "url": "/Isaac/Props/YCB/Axis_Aligned_Physics/006_mustard_bottle.usd",
            "label": "mustard_bottle",
            "count": 7,
            "floating": False,
            "scale_min_max": (0.85, 3.25),
        },
    ],
    "shape_distractors_types": ["capsule", "cone", "cylinder", "sphere", "cube"],
    "shape_distractors_scale_min_max": (0.015, 0.15),
    "shape_distractors_num": 150,
    "mesh_distractors_urls": [
        "/Isaac/Environments/Simple_Warehouse/Props/SM_CardBoxD_04_1847.usd",
        "/Isaac/Environments/Simple_Warehouse/Props/SM_CardBoxA_01_414.usd",
        "/Isaac/Environments/Simple_Warehouse/Props/S_TrafficCone.usd",
    ],
    "mesh_distractors_scale_min_max": (0.35, 1.35),
    "mesh_distractors_num": 75,
}

asyncio.ensure_future(run_example_async(config))
