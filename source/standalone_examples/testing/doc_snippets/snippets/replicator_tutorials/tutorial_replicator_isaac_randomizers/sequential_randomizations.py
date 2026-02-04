# SPDX-FileCopyrightText: Copyright (c) 2024-2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
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
import itertools
import os

import numpy as np
import omni.replicator.core as rep
import omni.usd
from isaacsim.storage.native import get_assets_root_path_async
from pxr import Gf, Usd, UsdGeom, UsdLux


# Fibonacci sphere algorithm: https://arxiv.org/pdf/0912.4540
def next_point_on_sphere(idx, num_points, radius=1, origin=(0, 0, 0)):
    offset = 2.0 / num_points
    inc = np.pi * (3.0 - np.sqrt(5.0))
    z = ((idx * offset) - 1) + (offset / 2)
    phi = ((idx + 1) % num_points) * inc
    r = np.sqrt(1 - pow(z, 2))
    y = np.cos(phi) * r
    x = np.sin(phi) * r
    return [(x * radius) + origin[0], (y * radius) + origin[1], (z * radius) + origin[2]]


async def run_randomizations_async(
    num_frames, forklift_path, pallet_path, bin_path, dome_textures, write_data, delay=None
):
    assets_root_path = await get_assets_root_path_async()

    await omni.usd.get_context().new_stage_async()
    stage = omni.usd.get_context().get_stage()

    dome_light = UsdLux.DomeLight.Define(stage, "/World/Lights/DomeLight")
    dome_light.GetIntensityAttr().Set(1000)

    forklift_prim = stage.DefinePrim("/World/Forklift", "Xform")
    forklift_prim.GetReferences().AddReference(assets_root_path + forklift_path)
    if not forklift_prim.GetAttribute("xformOp:translate"):
        UsdGeom.Xformable(forklift_prim).AddTranslateOp()
    forklift_prim.GetAttribute("xformOp:translate").Set((-4.5, -4.5, 0))

    pallet_prim = stage.DefinePrim("/World/Pallet", "Xform")
    pallet_prim.GetReferences().AddReference(assets_root_path + pallet_path)
    if not pallet_prim.GetAttribute("xformOp:translate"):
        UsdGeom.Xformable(pallet_prim).AddTranslateOp()
    if not pallet_prim.GetAttribute("xformOp:rotateXYZ"):
        UsdGeom.Xformable(pallet_prim).AddRotateXYZOp()

    bin_prim = stage.DefinePrim("/World/Bin", "Xform")
    bin_prim.GetReferences().AddReference(assets_root_path + bin_path)
    if not bin_prim.GetAttribute("xformOp:translate"):
        UsdGeom.Xformable(bin_prim).AddTranslateOp()
    if not bin_prim.GetAttribute("xformOp:rotateXYZ"):
        UsdGeom.Xformable(bin_prim).AddRotateXYZOp()

    view_cam = stage.DefinePrim("/World/Camera", "Camera")
    if not view_cam.GetAttribute("xformOp:translate"):
        UsdGeom.Xformable(view_cam).AddTranslateOp()
    if not view_cam.GetAttribute("xformOp:orient"):
        UsdGeom.Xformable(view_cam).AddOrientOp()

    dome_textures_full = [assets_root_path + tex for tex in dome_textures]
    textures_cycle = itertools.cycle(dome_textures_full)

    if write_data:
        out_dir = os.path.join(os.getcwd(), "_out_rand_sphere_scan")
        print(f"Writing data to {out_dir}..")
        backend = rep.backends.get("DiskBackend")
        backend.initialize(output_dir=out_dir)
        writer = rep.WriterRegistry.get("BasicWriter")
        writer.initialize(backend=backend, rgb=True)
        persp_cam = rep.functional.create.camera(position=(5, 5, 5), look_at=(0, 0, 0), name="PerspCamera")
        rp_persp = rep.create.render_product(persp_cam, (512, 512), name="PerspView")
        rp_view = rep.create.render_product(view_cam, (512, 512), name="SphereView")
        writer.attach([rp_view, rp_persp])

    bb_cache = UsdGeom.BBoxCache(time=Usd.TimeCode.Default(), includedPurposes=[UsdGeom.Tokens.default_])
    pallet_size = bb_cache.ComputeWorldBound(pallet_prim).GetRange().GetSize()
    pallet_length = pallet_size.GetLength()
    bin_size = bb_cache.ComputeWorldBound(bin_prim).GetRange().GetSize()

    for i in range(num_frames):
        # Set next background texture every nth frame and run an app update
        if i % 5 == 0:
            dome_light.GetTextureFileAttr().Set(next(textures_cycle))
            await omni.kit.app.get_app().next_update_async()

        # Randomize pallet pose
        pallet_prim.GetAttribute("xformOp:translate").Set(
            Gf.Vec3d(np.random.uniform(-1.5, 1.5), np.random.uniform(-1.5, 1.5), 0)
        )
        rand_z_rot = np.random.uniform(-90, 90)
        pallet_prim.GetAttribute("xformOp:rotateXYZ").Set(Gf.Vec3d(0, 0, rand_z_rot))
        pallet_tf_mat = omni.usd.get_world_transform_matrix(pallet_prim)
        pallet_rot = pallet_tf_mat.ExtractRotation()
        pallet_pos = pallet_tf_mat.ExtractTranslation()

        # Randomize bin position on top of the rotated pallet area making sure the bin is fully on the pallet
        rand_transl_x = np.random.uniform(-pallet_size[0] / 2 + bin_size[0] / 2, pallet_size[0] / 2 - bin_size[0] / 2)
        rand_transl_y = np.random.uniform(-pallet_size[1] / 2 + bin_size[1] / 2, pallet_size[1] / 2 - bin_size[1] / 2)

        # Adjust bin position to account for the random rotation of the pallet
        rand_z_rot_rad = np.deg2rad(rand_z_rot)
        rot_adjusted_transl_x = rand_transl_x * np.cos(rand_z_rot_rad) - rand_transl_y * np.sin(rand_z_rot_rad)
        rot_adjusted_transl_y = rand_transl_x * np.sin(rand_z_rot_rad) + rand_transl_y * np.cos(rand_z_rot_rad)
        bin_prim.GetAttribute("xformOp:translate").Set(
            Gf.Vec3d(
                pallet_pos[0] + rot_adjusted_transl_x,
                pallet_pos[1] + rot_adjusted_transl_y,
                pallet_pos[2] + pallet_size[2] + bin_size[2] / 2,
            )
        )
        # Keep bin rotation aligned with pallet
        bin_prim.GetAttribute("xformOp:rotateXYZ").Set(pallet_rot.GetAxis() * pallet_rot.GetAngle())

        # Get next camera position on a sphere looking at the bin with a randomized distance
        rand_radius = np.random.normal(3, 0.5) * pallet_length
        bin_pos = omni.usd.get_world_transform_matrix(bin_prim).ExtractTranslation()
        cam_pos = next_point_on_sphere(i, num_points=num_frames, radius=rand_radius, origin=bin_pos)
        view_cam.GetAttribute("xformOp:translate").Set(Gf.Vec3d(*cam_pos))

        eye = Gf.Vec3d(*cam_pos)
        target = Gf.Vec3d(*bin_pos)
        up_axis = Gf.Vec3d(0, 0, 1)
        look_at_quatd = Gf.Matrix4d().SetLookAt(eye, target, up_axis).GetInverse().ExtractRotation().GetQuat()
        view_cam.GetAttribute("xformOp:orient").Set(Gf.Quatf(look_at_quatd))

        if write_data:
            await rep.orchestrator.step_async(rt_subframes=4, delta_time=0.0)
        else:
            await omni.kit.app.get_app().next_update_async()
        # Optional delay between frames to better visualize the randomization in the viewport
        if delay is not None and delay > 0:
            await asyncio.sleep(delay)

    # Wait for the data to be written to disk and cleanup writer and render products
    if write_data:
        await rep.orchestrator.wait_until_complete_async()
        writer.detach()
        rp_persp.destroy()
        rp_view.destroy()


NUM_FRAMES = 90
FORKLIFT_PATH = "/Isaac/Props/Forklift/forklift.usd"
PALLET_PATH = "/Isaac/Props/Pallet/pallet.usd"
BIN_PATH = "/Isaac/Props/KLT_Bin/small_KLT_visual.usd"
DOME_TEXTURES = [
    "/NVIDIA/Assets/Skies/Cloudy/champagne_castle_1_4k.hdr",
    "/NVIDIA/Assets/Skies/Clear/evening_road_01_4k.hdr",
    "/NVIDIA/Assets/Skies/Clear/mealie_road_4k.hdr",
    "/NVIDIA/Assets/Skies/Clear/qwantani_4k.hdr",
]
asyncio.ensure_future(
    run_randomizations_async(
        NUM_FRAMES, FORKLIFT_PATH, PALLET_PATH, BIN_PATH, DOME_TEXTURES, write_data=True, delay=0.2
    )
)
