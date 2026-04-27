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
import os

import numpy as np
import omni.replicator.core as rep
import omni.usd
from isaacsim.core.experimental.utils.semantics import add_labels, get_labels
from isaacsim.storage.native import get_assets_root_path_async
from pxr import Gf, Sdf, UsdGeom, UsdShade

omni.usd.get_context().new_stage()
stage = omni.usd.get_context().get_stage()
dome_light = stage.DefinePrim("/World/DomeLight", "DomeLight")
dome_light.CreateAttribute("inputs:intensity", Sdf.ValueTypeNames.Float).Set(1000.0)

sphere = stage.DefinePrim("/World/Sphere", "Sphere")
UsdGeom.Xformable(sphere).AddTranslateOp().Set((0.0, 0.0, 1.0))
add_labels(sphere, labels=["sphere"], taxonomy="class")

num_cubes = 10
for _ in range(num_cubes):
    prim_type = "Cube"
    next_free_path = omni.usd.get_stage_next_free_path(stage, f"/World/{prim_type}", False)
    cube = stage.DefinePrim(next_free_path, prim_type)
    UsdGeom.Xformable(cube).AddTranslateOp().Set((np.random.uniform(-3.5, 3.5), np.random.uniform(-3.5, 3.5), 1))
    scale_rand = np.random.uniform(0.25, 0.5)
    UsdGeom.Xformable(cube).AddScaleOp().Set((scale_rand, scale_rand, scale_rand))
    add_labels(cube, labels=["cube"], taxonomy="class")

plane_path = "/World/Plane"
omni.kit.commands.execute("CreateMeshPrimWithDefaultXform", prim_path=plane_path, prim_type="Plane")
plane_prim = stage.GetPrimAtPath(plane_path)
plane_prim.CreateAttribute("xformOp:scale", Sdf.ValueTypeNames.Double3, False).Set(Gf.Vec3d(10, 10, 1))


def get_shapes():
    stage = omni.usd.get_context().get_stage()
    shapes = []
    for prim in stage.Traverse():
        labels = get_labels(prim)
        if class_labels := labels.get("class"):
            if "cube" in class_labels or "sphere" in class_labels:
                shapes.append(prim)
    return shapes


shapes = get_shapes()


def create_omnipbr_material(mtl_url, mtl_name, mtl_path):
    stage = omni.usd.get_context().get_stage()
    omni.kit.commands.execute("CreateMdlMaterialPrim", mtl_url=mtl_url, mtl_name=mtl_name, mtl_path=mtl_path)
    material_prim = stage.GetPrimAtPath(mtl_path)
    shader = UsdShade.Shader(omni.usd.get_shader_from_material(material_prim, get_prim=True))

    # Add value inputs
    shader.CreateInput("diffuse_color_constant", Sdf.ValueTypeNames.Color3f)
    shader.CreateInput("reflection_roughness_constant", Sdf.ValueTypeNames.Float)
    shader.CreateInput("metallic_constant", Sdf.ValueTypeNames.Float)

    # Add texture inputs
    shader.CreateInput("diffuse_texture", Sdf.ValueTypeNames.Asset)
    shader.CreateInput("reflectionroughness_texture", Sdf.ValueTypeNames.Asset)
    shader.CreateInput("metallic_texture", Sdf.ValueTypeNames.Asset)

    # Add other attributes
    shader.CreateInput("project_uvw", Sdf.ValueTypeNames.Bool)

    # Add texture scale and rotate
    shader.CreateInput("texture_scale", Sdf.ValueTypeNames.Float2)
    shader.CreateInput("texture_rotate", Sdf.ValueTypeNames.Float)

    material = UsdShade.Material(material_prim)
    return material


def create_materials(num):
    MDL = "OmniPBR.mdl"
    mtl_name, _ = os.path.splitext(MDL)
    MAT_PATH = "/World/Looks"
    materials = []
    for _ in range(num):
        prim_path = omni.usd.get_stage_next_free_path(stage, f"{MAT_PATH}/{mtl_name}", False)
        mat = create_omnipbr_material(mtl_url=MDL, mtl_name=mtl_name, mtl_path=prim_path)
        materials.append(mat)
    return materials


materials = create_materials(len(shapes))


async def run_randomizations_async(num_frames, materials, write_data, delay=None):
    assets_root_path = await get_assets_root_path_async()
    textures = [
        assets_root_path + "/NVIDIA/Materials/vMaterials_2/Ground/textures/aggregate_exposed_diff.jpg",
        assets_root_path + "/NVIDIA/Materials/vMaterials_2/Ground/textures/gravel_track_ballast_diff.jpg",
        assets_root_path + "/NVIDIA/Materials/vMaterials_2/Ground/textures/gravel_track_ballast_multi_R_rough_G_ao.jpg",
        assets_root_path + "/NVIDIA/Materials/vMaterials_2/Ground/textures/rough_gravel_rough.jpg",
    ]

    if write_data:
        out_dir = os.path.join(os.getcwd(), "_out_rand_textures")
        print(f"Writing data to {out_dir}..")
        backend = rep.backends.get("DiskBackend")
        backend.initialize(output_dir=out_dir)
        writer = rep.WriterRegistry.get("BasicWriter")
        writer.initialize(backend=backend, rgb=True)
        cam = rep.functional.create.camera(position=(5, 5, 5), look_at=(0, 0, 0), name="Camera")
        rp = rep.create.render_product(cam, resolution=(512, 512))
        writer.attach(rp)

    # Apply the new materials and store the initial ones to reassign later
    initial_materials = {}
    for i, shape in enumerate(shapes):
        cur_mat, _ = UsdShade.MaterialBindingAPI(shape).ComputeBoundMaterial()
        initial_materials[shape] = cur_mat
        UsdShade.MaterialBindingAPI(shape).Bind(materials[i], UsdShade.Tokens.strongerThanDescendants)

    for _ in range(num_frames):
        for mat in materials:
            shader = UsdShade.Shader(omni.usd.get_shader_from_material(mat, get_prim=True))
            diffuse_texture = np.random.choice(textures)
            shader.GetInput("diffuse_texture").Set(diffuse_texture)
            project_uvw = np.random.choice([True, False], p=[0.9, 0.1])
            shader.GetInput("project_uvw").Set(bool(project_uvw))
            texture_scale = np.random.uniform(0.1, 1)
            shader.GetInput("texture_scale").Set((texture_scale, texture_scale))
            texture_rotate = np.random.uniform(0, 45)
            shader.GetInput("texture_rotate").Set(texture_rotate)

        if write_data:
            await rep.orchestrator.step_async(rt_subframes=4)
        else:
            await omni.kit.app.get_app().next_update_async()

        # Optional delay between frames to better visualize the randomization in the viewport
        if delay is not None and delay > 0:
            await asyncio.sleep(delay)

    # Wait for the data to be written to disk and cleanup writer and render product
    if write_data:
        await rep.orchestrator.wait_until_complete_async()
        writer.detach()
        rp.destroy()

    # Reassign the initial materials
    for shape, mat in initial_materials.items():
        if mat:
            UsdShade.MaterialBindingAPI(shape).Bind(mat, UsdShade.Tokens.strongerThanDescendants)
        else:
            UsdShade.MaterialBindingAPI(shape).UnbindAllBindings()


num_frames = 10
asyncio.ensure_future(run_randomizations_async(num_frames, materials, write_data=True, delay=0.2))
