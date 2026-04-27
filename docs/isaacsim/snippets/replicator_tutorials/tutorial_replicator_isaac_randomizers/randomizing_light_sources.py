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
import omni.kit.commands
import omni.replicator.core as rep
import omni.usd
from isaacsim.core.experimental.utils.semantics import add_labels
from pxr import Gf, Sdf, UsdGeom

omni.usd.get_context().new_stage()
stage = omni.usd.get_context().get_stage()

sphere = stage.DefinePrim("/World/Sphere", "Sphere")
UsdGeom.Xformable(sphere).AddTranslateOp().Set((0.0, 1.0, 1.0))
add_labels(sphere, labels=["sphere"], taxonomy="class")

cube = stage.DefinePrim("/World/Cube", "Cube")
UsdGeom.Xformable(cube).AddTranslateOp().Set((0.0, -2.0, 2.0))
add_labels(cube, labels=["cube"], taxonomy="class")

plane_path = "/World/Plane"
omni.kit.commands.execute("CreateMeshPrimWithDefaultXform", prim_path=plane_path, prim_type="Plane")
plane_prim = stage.GetPrimAtPath(plane_path)
plane_prim.CreateAttribute("xformOp:scale", Sdf.ValueTypeNames.Double3, False).Set(Gf.Vec3d(10, 10, 1))


def sphere_lights(num):
    lights = []
    for i in range(num):
        # "CylinderLight", "DiskLight", "DistantLight", "DomeLight", "RectLight", "SphereLight"
        prim_type = "SphereLight"
        next_free_path = omni.usd.get_stage_next_free_path(stage, f"/World/{prim_type}", False)
        light_prim = stage.DefinePrim(next_free_path, prim_type)
        UsdGeom.Xformable(light_prim).AddTranslateOp().Set((0.0, 0.0, 0.0))
        UsdGeom.Xformable(light_prim).AddRotateXYZOp().Set((0.0, 0.0, 0.0))
        UsdGeom.Xformable(light_prim).AddScaleOp().Set((1.0, 1.0, 1.0))
        light_prim.CreateAttribute("inputs:enableColorTemperature", Sdf.ValueTypeNames.Bool).Set(True)
        light_prim.CreateAttribute("inputs:colorTemperature", Sdf.ValueTypeNames.Float).Set(6500.0)
        light_prim.CreateAttribute("inputs:radius", Sdf.ValueTypeNames.Float).Set(0.5)
        light_prim.CreateAttribute("inputs:intensity", Sdf.ValueTypeNames.Float).Set(30000.0)
        light_prim.CreateAttribute("inputs:color", Sdf.ValueTypeNames.Color3f).Set((1.0, 1.0, 1.0))
        light_prim.CreateAttribute("inputs:exposure", Sdf.ValueTypeNames.Float).Set(0.0)
        light_prim.CreateAttribute("inputs:diffuse", Sdf.ValueTypeNames.Float).Set(1.0)
        light_prim.CreateAttribute("inputs:specular", Sdf.ValueTypeNames.Float).Set(1.0)
        lights.append(light_prim)
    return lights


async def run_randomizations_async(num_frames, lights, write_data, delay=None):
    if write_data:
        out_dir = os.path.join(os.getcwd(), "_out_rand_lights")
        print(f"Writing data to {out_dir}..")
        backend = rep.backends.get("DiskBackend")
        backend.initialize(output_dir=out_dir)
        writer = rep.WriterRegistry.get("BasicWriter")
        writer.initialize(backend=backend, rgb=True)
        cam = rep.functional.create.camera(position=(5, 5, 5), look_at=(0, 0, 0), name="Camera")
        rp = rep.create.render_product(cam, resolution=(512, 512))
        writer.attach(rp)

    for _ in range(num_frames):
        for light in lights:
            light.GetAttribute("xformOp:translate").Set(
                (np.random.uniform(-5, 5), np.random.uniform(-5, 5), np.random.uniform(4, 6))
            )
            scale_rand = np.random.uniform(0.5, 1.5)
            light.GetAttribute("xformOp:scale").Set((scale_rand, scale_rand, scale_rand))
            light.GetAttribute("inputs:colorTemperature").Set(np.random.normal(4500, 1500))
            light.GetAttribute("inputs:intensity").Set(np.random.normal(25000, 5000))
            light.GetAttribute("inputs:color").Set(
                (np.random.uniform(0.1, 0.9), np.random.uniform(0.1, 0.9), np.random.uniform(0.1, 0.9))
            )

        if write_data:
            await rep.orchestrator.step_async(rt_subframes=16)
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


num_frames = 10
lights = sphere_lights(10)
asyncio.ensure_future(run_randomizations_async(num_frames=num_frames, lights=lights, write_data=True, delay=0.2))
