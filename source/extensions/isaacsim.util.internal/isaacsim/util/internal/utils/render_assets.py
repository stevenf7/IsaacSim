# Copyright (c) 2021-2023, NVIDIA CORPORATION. All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto. Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#

import io
import os
import re
from itertools import product

import numpy as np
import omni.client
import omni.usd
from isaacsim.core.utils.prims import is_prim_path_valid
from isaacsim.sensors.camera import Camera
from isaacsim.util.internal.utils import file_utils
from omni.client import create_folder, write_file
from omni.isaac.core import World
from omni.isaac.core.utils.bounds import compute_aabb, create_bbox_cache, recompute_extents
from omni.isaac.core.utils.numpy.rotations import euler_angles_to_quats
from omni.isaac.core.utils.stage import add_reference_to_stage, create_new_stage, open_stage, save_stage
from omni.isaac.nucleus import get_assets_root_path, is_file
from PIL import Image
from pxr import Gf, Usd, UsdGeom
from scipy.spatial.transform import Rotation


class AssetRenderer:
    def __init__(self):
        self._world = None
        self._default_scene = get_assets_root_path() + "/Projects/Environments/AssetRenderer/default_scene.usd"

    def create_image(self, job_config, reposition_camera=True, force_create_scene=False):
        if not self.init_scene(job_config, force_create_scene):
            return False
        if reposition_camera:
            if not self.reposition_camera():
                return False
        self.render_and_save_image(job_config)
        self._world.clear_instance()
        return True

    def init_scene(self, job_config, force_create_scene):

        # Default values
        if "environment_path" not in job_config:
            job_config["environment_path"] = self._default_scene

        # We have to reuse or create the scene
        if "scene_path" in job_config:
            scene_usd_path = job_config["scene_path"]

            # That file exists
            try:
                has_scene = is_file(scene_usd_path)
            except Exception as e:
                has_scene = False

            if not has_scene or force_create_scene:
                success = self._create_stage(job_config)
                save_stage(scene_usd_path, save_and_reload_in_place=True)
                if not success:
                    return False
            else:
                open_stage(scene_usd_path)
                self.init_world_and_camera_sensor(job_config)

        else:
            if not self._create_stage(job_config):
                return False

        return True

    def init_world_and_camera_sensor(self, job_config):
        self._world = World(stage_units_in_meters=1.0, physics_dt=1.0 / 60.0, rendering_dt=1.0 / 60.0)
        self._asset = self._world.stage.GetPrimAtPath("/World/AssetXform/Asset")
        self._create_and_initialize_camera(job_config["resolution"])

    def _create_stage(self, job_config):

        # Clear out everything, we build this from scratch for every scene right now (can be optimized)
        create_new_stage()

        # Make reference paths relative if possible
        env_path = job_config["environment_path"]
        asset_path = job_config["asset_path"]

        if "scene_path" in job_config:
            scenes_dir = file_utils.dirname(job_config["scene_path"])
            env_path = file_utils.relpath(env_path, scenes_dir)
            asset_path = file_utils.relpath(asset_path, scenes_dir)
            save_stage(job_config["scene_path"], save_and_reload_in_place=True)

        # Add the references
        add_reference_to_stage(env_path, "/World/Environment")
        self._add_asset(asset_path)

        # Camera
        self.init_world_and_camera_sensor(job_config)

        # Now that we've saved, we can calculate the AABB of the asset (path may be relative)
        if not self._place_asset_on_ground():
            return False

        return self.reposition_camera()

    def _add_asset(self, asset_usd_path):
        xform_path = "/World/AssetXform"
        asset_path = xform_path + "/Asset"
        self._asset_xform = UsdGeom.Xform.Define(omni.usd.get_context().get_stage(), xform_path)

        self._asset = add_reference_to_stage(asset_usd_path, asset_path)

    def _place_asset_on_ground(self):
        aabb = self._get_asset_aabb()
        translate = self._asset_xform.AddTranslateOp()

        # Essentially infinite, something went wrong
        if np.any(np.abs(aabb) > 1e37):
            print("ERROR : Unable to find AABB of asset")
            return False

        # Offset asset vertically so it's on the ground
        asset_offset = np.array([0.0, 0.0, -aabb[2]])
        translate.Set(Gf.Vec3f(asset_offset[0], asset_offset[1], asset_offset[2]))

        return True

    def _create_and_initialize_camera(self, resolution):
        capture_camera_path = "/World/capture_camera"

        creating = not is_prim_path_valid(capture_camera_path)
        if creating:
            self._camera = Camera(
                prim_path="/World/capture_camera",
                position=np.array([0.0, 0.0, 0.0]),
                frequency=-1,
                resolution=resolution,
                orientation=euler_angles_to_quats(np.array([0.0, 0.0, 180.0]), degrees=True),
            )

        else:
            self._camera = Camera(
                prim_path="/World/capture_camera",
                frequency=-1,
                resolution=resolution,
            )

        self._camera.set_clipping_range(0.001, self._camera.get_clipping_range()[1])
        self._camera.initialize()

        # Get the existing xform ops
        ops = AssetRenderer.get_standard_xform_ops(self._camera._camera_prim)
        self._translate_op, self._orient_op, self._scale_op = ops

        if creating:
            # Camera starts looking down -Z with Y up
            # First we rotate 90 around Z, then 90 around Y giving us -X forward Z up
            rotation = Gf.Rotation(Gf.Vec3d(0.0, 0.0, 1.0), 90.0)
            rotation *= Gf.Rotation(Gf.Vec3d(0.0, 1.0, 0.0), 90.0)

            # Next pitch down and rotate 45 degrees around the Z
            rotation *= Gf.Rotation(Gf.Vec3d(0.0, 1.0, 0.0), -(90.0 - 54.73561))
            rotation *= Gf.Rotation(Gf.Vec3d(0.0, 0.0, 1.0), 45.0)

            # Camera now points in desired direction, positioned at origin
            self._quat = Gf.Quatd(rotation.GetQuat())
            self._camera_pos = Gf.Vec3d(0.0, 0.0, 0.0)

            self._translate_op.Set(self._camera_pos)
            self._orient_op.Set(self._quat)
            self._scale_op.Set((1, 1, 1))

        else:
            self._quat = self._orient_op.Get()
            self._camera_pos = self._translate_op.Get()

    def get_standard_xform_ops(prim):
        xformable = UsdGeom.Xformable(prim)
        xform_ops = xformable.GetOrderedXformOps()

        # Check if there are exactly three ops
        if len(xform_ops) != 3:
            raise Exception(f"Expected three Xform ops in this order: translate, orient, scale.")

        # Ensure the order is translate, orient, scale
        if (
            xform_ops[0].GetOpType() != UsdGeom.XformOp.TypeTranslate
            or xform_ops[1].GetOpType() != UsdGeom.XformOp.TypeOrient
            or xform_ops[2].GetOpType() != UsdGeom.XformOp.TypeScale
        ):
            raise Exception(f"Expected three Xform ops in this order: translate, orient, scale.")

        return tuple(xform_ops)

    def reposition_camera(self):

        # Get our asset's AABB, but ignore the bits below ground (can only happen when manually placed)
        aabb = self._get_asset_aabb()

        # Essentially infinite, something went wrong
        if np.any(np.abs(aabb) > 1e37):
            print("ERROR : Unable to find AABB of asset")
            return False

        aabb[2] = max(aabb[2], 0.0)

        center = 0.5 * (aabb[3:] + aabb[:3])
        half_extents = 0.5 * (aabb[3:] - aabb[:3])

        # Get the 8 corners of the AABB
        signs = np.array(list(product([1, -1], repeat=3)))
        v = center[None, :] + signs * half_extents[None, :]

        # Get AABB in camera space of the world AABB corners
        pos, rot = self._camera.get_world_pose(camera_axes="usd")
        rot = Rotation.from_quat(rot[[1, 2, 3, 0]])
        v_camera = rot.inv().apply(v)
        camera_aabb = np.array([v_camera.min(axis=0), v_camera.max(axis=0)]).flatten()
        camera_aabb_center = 0.5 * (camera_aabb[:3] + camera_aabb[3:])
        camera_aabb_extents = camera_aabb[3:] - camera_aabb[:3]

        # Transform AABB center into world space, this is where the camera will point
        final_center = rot.apply(camera_aabb_center)

        # Start at the maximum Z of the camera AABB, then calculate distance to fully fit AABB in the image
        dist = camera_aabb[5]
        dist += self._camera.get_focal_length() * max(
            camera_aabb_extents[0] / self._camera.get_horizontal_aperture(),
            camera_aabb_extents[1] / self._camera.get_vertical_aperture(),
        )

        # Position camera
        camera_dir = self._quat.Transform(Gf.Vec3d(0.0, 0.0, -1.0))
        camera_pos = -float(dist) * camera_dir
        camera_pos += Gf.Vec3d(final_center[0], final_center[1], final_center[2])

        self._translate_op.Set(camera_pos)
        self._camera.initialize()

        return True

    def render_and_save_image(self, job_config):

        image_path = job_config["image_path"]

        self._world.reset()
        self._camera.initialize()

        # Run the sim for things to settle and to render
        self._world.play()
        for _ in range(100):  # range(job_config["simulation_steps"]):
            self._world.render()
        self._world.stop()

        # Grab the camera frame and save it to omniverse path
        data = self._camera.get_rgba()[..., :3]

        img = Image.fromarray(data, "RGB")

        match = re.match(r"^(omniverse://)(.+)/([^/]+)$", image_path)

        if match is None or len(match.groups()) != 3:
            raise Exception("Bad image_path (" + image_path + ")")

        protocol, path, _ = match.groups()

        create_folder(protocol + path)

        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        buffer.seek(0)
        data = buffer.getvalue()

        result = write_file(image_path, data)

        print(f"Saved image to {image_path}")

        if result != omni.client.Result.OK:
            raise Exception("Error writing image")

    def _get_asset_aabb(self):
        asset_path = "/World/AssetXform/Asset"

        # Recompute all the extents
        for prim in Usd.PrimRange(self._asset):
            if prim.IsA(UsdGeom.Boundable):
                recompute_extents(UsdGeom.Boundable(prim))

        return compute_aabb(create_bbox_cache(), asset_path, include_children=True)
