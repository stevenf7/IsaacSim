# SPDX-FileCopyrightText: Copyright (c) 2021-2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
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

import io
import re
from itertools import product
from urllib.parse import urlparse

import numpy as np
import omni.usd
from isaacsim.core.api import World
from isaacsim.core.utils.bounds import compute_aabb, create_bbox_cache, recompute_extents
from isaacsim.core.utils.numpy.rotations import euler_angles_to_quats
from isaacsim.core.utils.prims import is_prim_path_valid
from isaacsim.core.utils.stage import (
    add_reference_to_stage,
    create_new_stage,
    get_current_stage,
    open_stage,
    save_stage,
)
from isaacsim.sensors.camera import Camera
from isaacsim.storage.native import get_assets_root_path, path_dirname, path_relative
from omni.client import create_folder, write_file
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
        stage = get_current_stage()
        # Only save the stage if we're not reusing an existing scene
        if not job_config.get("reuse_existing_scene", False):
            stage.Save()
        self.render_and_save_image(job_config)
        self._world.clear_instance()
        return True

    def init_scene(self, job_config, force_create_scene):

        # Default values
        if "environment_path" not in job_config:
            job_config["environment_path"] = self._default_scene
            print(f"Using default scene: {job_config['environment_path']}")

        # We have to reuse or create the scene
        if "scene_path" in job_config:
            scene_usd_path = job_config["scene_path"]
            print(f"Scene path: {scene_usd_path}")
            print(f"Force create scene: {force_create_scene}")

            # That file exists
            try:
                result, stat_info = omni.client.stat(scene_usd_path)
                has_scene = result == omni.client.Result.OK
                print(f"Scene file exists: {has_scene} (result: {result})")
                if has_scene and stat_info:
                    print(f"Scene file size: {stat_info.size}, flags: {stat_info.flags}")
            except Exception as e:
                has_scene = False
                print(f"Error checking scene file: {e}")

            if not has_scene or force_create_scene:
                print(f"Creating new stage (has_scene={has_scene}, force_create_scene={force_create_scene})")
                success = self._create_stage(job_config)
                # Only save the scene if we're not reusing an existing one
                if not job_config.get("reuse_existing_scene", False):
                    save_stage(scene_usd_path, save_and_reload_in_place=True)
                if not success:
                    return False
            else:
                # Reuse existing scene file
                print(f"Opening existing scene: {scene_usd_path}")
                open_stage(scene_usd_path)

                # Validate that the existing scene has the expected structure
                if not self._validate_existing_scene(scene_usd_path):
                    print(f"Existing scene {scene_usd_path} is invalid, recreating...")
                    success = self._create_stage(job_config)
                    # Only save the scene if we're not reusing an existing one
                    if not job_config.get("reuse_existing_scene", False):
                        save_stage(scene_usd_path, save_and_reload_in_place=True)
                    if not success:
                        return False
                else:
                    print(f"Reusing existing scene: {scene_usd_path}")
                    self.init_world_and_camera_sensor(job_config)

        else:
            if not self._create_stage(job_config):
                return False

        return True

    def _validate_existing_scene(self, scene_path):
        """Validate that an existing scene file has the expected structure.

        Args:
            scene_path: Path to the scene USD file.

        Returns:
            True if the scene is valid and can be reused, False otherwise.
        """
        try:
            stage = get_current_stage()
            if not stage:
                print(f"ERROR: No current stage found for {scene_path}")
                return False

            print(f"Validating scene: {scene_path}")

            # Check if the expected prims exist
            asset_prim = stage.GetPrimAtPath("/World/AssetXform/Asset")
            if not asset_prim or not asset_prim.IsValid():
                print(f"Warning: Asset prim not found in existing scene {scene_path}")
                return False
            else:
                print(f"Asset prim found and valid: /World/AssetXform/Asset")

                # Check what's actually under the Asset prim
                asset_children = list(asset_prim.GetChildren())
                if not asset_children:
                    print(f"Asset prim invalid: /World/AssetXform/Asset has no children.")
                    return False

            camera_prim = stage.GetPrimAtPath("/World/capture_camera")
            if not camera_prim or not camera_prim.IsValid():
                print(f"Warning: Camera prim not found in existing scene {scene_path}")
                return False
            else:
                print(f"Camera prim found and valid: /World/capture_camera")

            print(f"Scene validation successful for {scene_path}")
            return True
        except Exception as e:
            print(f"Error validating existing scene {scene_path}: {e}")
            return False

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
            scenes_dir = path_dirname(job_config["scene_path"])
            print(f"Scene directory: {scenes_dir}")
            print(f"Original asset path: {asset_path}")

            # Try to make paths relative, but fall back to absolute if it fails
            try:
                env_path_relative = path_relative(env_path, scenes_dir)
                asset_path_relative = path_relative(asset_path, scenes_dir)

                # Check if the relative paths actually exist
                result, _ = omni.client.stat(asset_path_relative)
                if result == omni.client.Result.OK:
                    asset_path = asset_path_relative
                    print(f"Using relative asset path: {asset_path}")
                else:
                    print(f"Relative asset path doesn't exist: {asset_path_relative}, using absolute: {asset_path}")

                result, _ = omni.client.stat(env_path_relative)
                if result == omni.client.Result.OK:
                    env_path = env_path_relative
                    print(f"Using relative env path: {env_path}")
                else:
                    print(f"Relative env path doesn't exist: {env_path_relative}, using absolute: {env_path}")

            except Exception as e:
                print(f"Error calculating relative paths: {e}, using absolute paths")
                print(f"Using absolute asset path: {asset_path}")
                print(f"Using absolute env path: {env_path}")

        # Add the references
        print(f"Adding environment reference: {env_path} -> /World/Environment")

        add_reference_to_stage(env_path, "/World/Environment")

        if not self._add_asset(asset_path):
            return False

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

        print(f"Adding asset reference: {asset_usd_path} -> {asset_path}")

        # Check if the asset file exists
        result, _ = omni.client.stat(asset_usd_path)
        if result == omni.client.Result.OK:
            self._asset = add_reference_to_stage(asset_usd_path, asset_path)
            stage = omni.usd.get_context().get_stage()
            asset_prim = stage.GetPrimAtPath(asset_path)
            if not asset_prim or not asset_prim.IsValid():
                print(f"ERROR: Failed to add asset reference. Prim at {asset_path} is not valid.")
                return False

            print(f"Asset reference added successfully. Prim exists: {asset_prim.IsValid()}")

            # Check if the Asset has valid children for rendering
            asset_children = list(asset_prim.GetChildren())
            if not asset_children:
                print(f"/World/AssetXform/Asset has no children")
                return False

            print(f"Asset prim has {len(asset_children)} children after adding reference")

        else:
            print(f"Asset file does not exist: {asset_usd_path}")
            return False

        return True

    def _place_asset_on_ground(self):
        aabb = self._get_asset_aabb()
        translate = self._asset_xform.AddTranslateOp()

        # Essentially infinite, something went wrong
        if aabb is None:
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
        self._camera.initialize(attach_rgb_annotator=False)

        # Get the existing xform ops
        ops = AssetRenderer.get_standard_xform_ops(self._camera._prim)
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
        if aabb is None:
            print("ERROR : Unable to find AABB of asset")
            return False

        aabb[2] = max(aabb[2], 0.0)

        center = 0.5 * (aabb[3:] + aabb[:3])
        half_extents = 0.5 * (aabb[3:] - aabb[:3])

        # Get the 8 corners of the AABB
        signs = np.array(list(product([1, -1], repeat=3)))
        v = center[None, :] + signs * half_extents[None, :]

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
        self._camera.initialize(attach_rgb_annotator=False)

        return True

    def render_and_save_image(self, job_config):

        image_path = job_config["image_path"]

        # Reinitialize World if needed
        try:
            self._world.reset()
        except AttributeError as e:
            if "'World' object has no attribute '_scene'" in str(e):
                print("Reinitializing World...")
                # Reinitialize the World after stage changes
                self.init_world_and_camera_sensor(job_config)
                self._world.reset()
                print("World reinitialized successfully")
            else:
                print(f"Error resetting world: {e}")
                raise e

        # Ensure camera is properly set up for rendering
        try:
            # Get fresh camera prim reference
            stage = get_current_stage()
            camera_prim = stage.GetPrimAtPath("/World/capture_camera")
            if not camera_prim or not camera_prim.IsValid():
                print("ERROR: Camera prim is not valid")
                raise Exception("Camera prim is not valid")

            self._camera.initialize(attach_rgb_annotator=True)
            print("Camera initialized successfully")

        except Exception as e:
            print(f"Error initializing camera: {e}")
            raise e

        # Run simulation to settle and render
        self._world.play()
        for _ in range(100):  # range(job_config["simulation_steps"]):
            self._world.render()
        self._world.stop()

        # Capture data
        try:
            data = self._camera.get_rgba()[..., :3]

            # Validate data dimensions and type
            if not isinstance(data, np.ndarray):
                raise Exception(f"Camera data is not numpy array: {type(data)}")

            if len(data.shape) != 3:
                raise Exception(f"Camera data has wrong shape: {data.shape}")

            if data.shape[2] < 3:
                raise Exception(f"Camera data has insufficient channels: {data.shape}")

        except Exception as e:
            print(f"Error capturing image data: {e}")

        img = Image.fromarray(data, "RGB")

        # Validate image before saving
        if img.size[0] <= 0 or img.size[1] <= 0:
            raise Exception(f"Invalid image size: {img.size}")

        print(f"Created image: size={img.size}, mode={img.mode}")

        # Parse image path and create directory if needed
        parsed = urlparse(image_path)
        if parsed.scheme and parsed.netloc:
            # Omniverse URL - create folder and save
            match = re.match(r"^(omniverse://)(.+)/([^/]+)$", image_path)
            if match is None or len(match.groups()) != 3:
                raise Exception("Bad image_path (" + image_path + ")")

            protocol, path, _ = match.groups()
            create_folder(protocol + path)

            # Save image to Omniverse
            buffer = io.BytesIO()
            img.save(buffer, format="PNG")
            buffer.seek(0)
            data = buffer.getvalue()

            result = write_file(image_path, data)
            if result != omni.client.Result.OK:
                raise Exception("Error writing image")
        else:
            # Local file path - create directory and save
            import os

            os.makedirs(os.path.dirname(image_path), exist_ok=True)

            # Save image to local file system
            img.save(image_path, format="PNG")

        print(f"Successfully saved image to {image_path}")

    def _get_asset_aabb(self):
        asset_path = "/World/AssetXform/Asset"

        # Get a fresh reference to the asset prim
        stage = get_current_stage()
        asset_prim = stage.GetPrimAtPath(asset_path)

        if not asset_prim or not asset_prim.IsValid():
            print(f"ERROR: Asset prim at {asset_path} is not valid")
            return None

        # Recompute all the extents
        for prim in Usd.PrimRange(asset_prim):
            if prim.IsA(UsdGeom.Boundable):
                try:
                    recompute_extents(UsdGeom.Boundable(prim))
                except Exception as e:
                    print(f"Error recomputing extents for {prim.GetPath()}: {e}")
                    return None

        return compute_aabb(create_bbox_cache(), asset_path, include_children=True)
