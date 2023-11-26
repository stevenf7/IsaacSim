# Copyright (c) 2023, NVIDIA CORPORATION. All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto. Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#

import omni.kit.test

################################################################################
### !!!IMPORTANT!!!
### The tests below are replicator alternative randomizer snippets from the docs.
### If you fix an issue here make sure to update the code in the docs as well
### The idea is that we can catch any api changes and update the docs appropriately
################################################################################


class TestRandomizerSnippets(omni.kit.test.AsyncTestCase):
    async def setUp(self):
        await omni.usd.get_context().new_stage_async()
        await omni.kit.app.get_app().next_update_async()

    async def tearDown(self):
        for _ in range(10):
            await omni.kit.app.get_app().next_update_async()
        # In some cases the test will end before the asset is loaded, in this case wait for assets to load
        while omni.usd.get_context().get_stage_loading_status()[2] > 0:
            await omni.kit.app.get_app().next_update_async()

    async def test_randomizing_a_light_source(self):
        import asyncio
        import os

        import numpy as np
        import omni.kit.commands
        import omni.replicator.core as rep
        import omni.usd
        from omni.isaac.core.utils.semantics import add_update_semantics
        from pxr import Gf, Sdf, UsdGeom

        omni.usd.get_context().new_stage()
        stage = omni.usd.get_context().get_stage()

        sphere = stage.DefinePrim("/World/Sphere", "Sphere")
        UsdGeom.Xformable(sphere).AddTranslateOp().Set((0.0, 1.0, 1.0))
        add_update_semantics(sphere, "sphere", "class")

        cube = stage.DefinePrim("/World/Cube", "Cube")
        UsdGeom.Xformable(cube).AddTranslateOp().Set((0.0, -2.0, 2.0))
        add_update_semantics(cube, "cube", "class")

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

        async def run_randomizations_async(num_frames, lights, write_data=True, delay=0):
            if write_data:
                writer = rep.WriterRegistry.get("BasicWriter")
                out_dir = os.getcwd() + "/_out_rand_lights"
                print(f"Writing data to {out_dir}..")
                writer.initialize(output_dir=out_dir, rgb=True)
                rp = rep.create.render_product("/OmniverseKit_Persp", (512, 512))
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
                if delay > 0:
                    await asyncio.sleep(delay)

        num_frames = 10
        lights = sphere_lights(10)
        # asyncio.ensure_future(run_randomizations_async(num_frames=num_frames, lights=lights, delay=0.2))
        await run_randomizations_async(num_frames=num_frames, lights=lights, delay=0.2)

    async def test_randomizing_textures(self):
        import asyncio
        import os

        import numpy as np
        import omni.replicator.core as rep
        import omni.usd
        from omni.isaac.core.utils.nucleus import get_assets_root_path
        from omni.isaac.core.utils.semantics import add_update_semantics, get_semantics
        from pxr import Gf, Sdf, UsdGeom, UsdShade

        omni.usd.get_context().new_stage()
        stage = omni.usd.get_context().get_stage()
        dome_light = stage.DefinePrim("/World/DomeLight", "DomeLight")
        dome_light.CreateAttribute("inputs:intensity", Sdf.ValueTypeNames.Float).Set(1000.0)

        sphere = stage.DefinePrim("/World/Sphere", "Sphere")
        UsdGeom.Xformable(sphere).AddTranslateOp().Set((0.0, 0.0, 1.0))
        add_update_semantics(sphere, "sphere", "class")

        num_cubes = 10
        for _ in range(num_cubes):
            prim_type = "Cube"
            next_free_path = omni.usd.get_stage_next_free_path(stage, f"/World/{prim_type}", False)
            cube = stage.DefinePrim(next_free_path, prim_type)
            UsdGeom.Xformable(cube).AddTranslateOp().Set(
                (np.random.uniform(-3.5, 3.5), np.random.uniform(-3.5, 3.5), 1)
            )
            scale_rand = np.random.uniform(0.25, 0.5)
            UsdGeom.Xformable(cube).AddScaleOp().Set((scale_rand, scale_rand, scale_rand))
            add_update_semantics(cube, "cube", "class")

        plane_path = "/World/Plane"
        omni.kit.commands.execute("CreateMeshPrimWithDefaultXform", prim_path=plane_path, prim_type="Plane")
        plane_prim = stage.GetPrimAtPath(plane_path)
        plane_prim.CreateAttribute("xformOp:scale", Sdf.ValueTypeNames.Double3, False).Set(Gf.Vec3d(10, 10, 1))

        def get_shapes():
            stage = omni.usd.get_context().get_stage()
            shapes = []
            for prim in stage.Traverse():
                sem_dict = get_semantics(prim)
                sem_values = sem_dict.values()
                if ("class", "cube") in sem_values or ("class", "sphere") in sem_values:
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

        async def run_randomizations_async(num_frames, materials, textures, write_data=True, delay=0):
            if write_data:
                writer = rep.WriterRegistry.get("BasicWriter")
                out_dir = os.getcwd() + "/_out_rand_textures"
                print(f"Writing data to {out_dir}..")
                writer.initialize(output_dir=out_dir, rgb=True)
                rp = rep.create.render_product("/OmniverseKit_Persp", (512, 512))
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
                if delay > 0:
                    await asyncio.sleep(delay)

            # Reassign the initial materials
            for shape, mat in initial_materials.items():
                if mat:
                    UsdShade.MaterialBindingAPI(shape).Bind(mat, UsdShade.Tokens.strongerThanDescendants)
                else:
                    UsdShade.MaterialBindingAPI(shape).UnbindAllBindings()

        assets_root_path = get_assets_root_path()
        textures = [
            assets_root_path + "/NVIDIA/Materials/vMaterials_2/Ground/textures/aggregate_exposed_diff.jpg",
            assets_root_path + "/NVIDIA/Materials/vMaterials_2/Ground/textures/gravel_track_ballast_diff.jpg",
            assets_root_path
            + "/NVIDIA/Materials/vMaterials_2/Ground/textures/gravel_track_ballast_multi_R_rough_G_ao.jpg",
            assets_root_path + "/NVIDIA/Materials/vMaterials_2/Ground/textures/rough_gravel_rough.jpg",
        ]

        num_frames = 10
        # asyncio.ensure_future(run_randomizations_async(num_frames, materials, textures, delay=0.2))
        await run_randomizations_async(num_frames, materials, textures, delay=0.2)

    async def test_chained_randomizations(self):
        import asyncio
        import itertools
        import os

        import numpy as np
        import omni.replicator.core as rep
        import omni.usd
        from omni.isaac.core.utils.nucleus import get_assets_root_path
        from pxr import Gf, Usd, UsdGeom, UsdLux

        # https://stackoverflow.com/questions/9600801/evenly-distributing-n-points-on-a-sphere
        # https://arxiv.org/pdf/0912.4540.pdf
        def next_point_on_sphere(idx, num_points, radius=1, origin=(0, 0, 0)):
            offset = 2.0 / num_points
            inc = np.pi * (3.0 - np.sqrt(5.0))
            z = ((idx * offset) - 1) + (offset / 2)
            phi = ((idx + 1) % num_points) * inc
            r = np.sqrt(1 - pow(z, 2))
            y = np.cos(phi) * r
            x = np.sin(phi) * r
            return [(x * radius) + origin[0], (y * radius) + origin[1], (z * radius) + origin[2]]

        assets_root_path = get_assets_root_path()
        FORKLIFT_PATH = assets_root_path + "/Isaac/Props/Forklift/forklift.usd"
        PALLET_PATH = assets_root_path + "/Isaac/Props/Pallet/pallet.usd"
        BIN_PATH = assets_root_path + "/Isaac/Props/KLT_Bin/small_KLT_visual.usd"

        omni.usd.get_context().new_stage()
        stage = omni.usd.get_context().get_stage()

        dome_light = UsdLux.DomeLight.Define(stage, "/World/Lights/DomeLight")
        dome_light.GetIntensityAttr().Set(1000)

        forklift_prim = stage.DefinePrim("/World/Forklift", "Xform")
        forklift_prim.GetReferences().AddReference(FORKLIFT_PATH)
        if not forklift_prim.GetAttribute("xformOp:translate"):
            UsdGeom.Xformable(forklift_prim).AddTranslateOp()
        forklift_prim.GetAttribute("xformOp:translate").Set((-4.5, -4.5, 0))

        pallet_prim = stage.DefinePrim("/World/Pallet", "Xform")
        pallet_prim.GetReferences().AddReference(PALLET_PATH)
        if not pallet_prim.GetAttribute("xformOp:translate"):
            UsdGeom.Xformable(pallet_prim).AddTranslateOp()
        if not pallet_prim.GetAttribute("xformOp:rotateXYZ"):
            UsdGeom.Xformable(pallet_prim).AddRotateXYZOp()

        bin_prim = stage.DefinePrim("/World/Bin", "Xform")
        bin_prim.GetReferences().AddReference(BIN_PATH)
        if not bin_prim.GetAttribute("xformOp:translate"):
            UsdGeom.Xformable(bin_prim).AddTranslateOp()
        if not bin_prim.GetAttribute("xformOp:rotateXYZ"):
            UsdGeom.Xformable(bin_prim).AddRotateXYZOp()

        cam = stage.DefinePrim("/World/Camera", "Camera")
        if not cam.GetAttribute("xformOp:translate"):
            UsdGeom.Xformable(cam).AddTranslateOp()
        if not cam.GetAttribute("xformOp:orient"):
            UsdGeom.Xformable(cam).AddOrientOp()

        async def run_randomizations_async(
            num_frames, dome_light, dome_textures, pallet_prim, bin_prim, write_data=True, delay=0
        ):
            if write_data:
                writer = rep.WriterRegistry.get("BasicWriter")
                out_dir = os.getcwd() + "/_out_rand_sphere_scan"
                print(f"Writing data to {out_dir}..")
                writer.initialize(output_dir=out_dir, rgb=True)
                rp_persp = rep.create.render_product("/OmniverseKit_Persp", (512, 512), name="PerspView")
                rp_cam = rep.create.render_product(str(cam.GetPath()), (512, 512), name="SphereView")
                writer.attach([rp_cam, rp_persp])

            textures_cycle = itertools.cycle(dome_textures)

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
                rand_transl_x = np.random.uniform(
                    -pallet_size[0] / 2 + bin_size[0] / 2, pallet_size[0] / 2 - bin_size[0] / 2
                )
                rand_transl_y = np.random.uniform(
                    -pallet_size[1] / 2 + bin_size[1] / 2, pallet_size[1] / 2 - bin_size[1] / 2
                )

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
                cam.GetAttribute("xformOp:translate").Set(Gf.Vec3d(*cam_pos))

                eye = Gf.Vec3d(*cam_pos)
                target = Gf.Vec3d(*bin_pos)
                up_axis = Gf.Vec3d(0, 0, 1)
                look_at_quatd = Gf.Matrix4d().SetLookAt(eye, target, up_axis).GetInverse().ExtractRotation().GetQuat()
                cam.GetAttribute("xformOp:orient").Set(Gf.Quatf(look_at_quatd))

                if write_data:
                    await rep.orchestrator.step_async(rt_subframes=4)
                else:
                    await omni.kit.app.get_app().next_update_async()
                if delay > 0:
                    await asyncio.sleep(delay)

        num_frames = 90
        dome_textures = [
            assets_root_path + "/NVIDIA/Assets/Skies/Cloudy/champagne_castle_1_4k.hdr",
            assets_root_path + "/NVIDIA/Assets/Skies/Clear/evening_road_01_4k.hdr",
            assets_root_path + "/NVIDIA/Assets/Skies/Clear/mealie_road_4k.hdr",
            assets_root_path + "/NVIDIA/Assets/Skies/Clear/qwantani_4k.hdr",
        ]
        # asyncio.ensure_future(
        #     run_randomizations_async(num_frames, dome_light, dome_textures, pallet_prim, bin_prim, delay=0.2)
        # )
        await run_randomizations_async(num_frames, dome_light, dome_textures, pallet_prim, bin_prim, delay=0.2)
