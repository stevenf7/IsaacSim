# Copyright (c) 2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.

import numpy as np

from scene.asset import Asset


class Object(Asset):
    """ For managing an Xform asset in Isaac Sim. """

    def __init__(self, sim_app, sim_context, ref, path, camera, group, prefix="obj", can_move=True):
        """ Construct Object. """

        self.ref = ref
        label = self.ref[self.ref.rfind("/") + 1 : self.ref.rfind(".")].replace("-", "_")

        super().__init__(sim_app, sim_context, path, camera, label, group, prefix, can_move)

        self.load_asset()

    def place_in_scene(self):
        """ Scale, rotate, and translate asset. """

        # Get asset dimensions
        min_bound, max_bound = self.get_bounds()
        offset = (max_bound + min_bound) / 2
        size = max_bound - min_bound

        # Get asset scale
        obj_size_is_enabled = self.sample("obj_size_enabled")
        if obj_size_is_enabled:
            obj_size = self.sample("obj_size")
            max_size = max(size)
            scale = obj_size / max_size
        else:
            scale = self.sample("obj_scale")

        # Scale asset
        scale = np.array([scale, scale, scale])
        self.scale(scale)

        # Get asset coord and rotation
        self.coord = self.get_initial_coord()
        self.rotation = self.get_initial_rotation()

        # Rotate asset
        self.rotate(self.rotation)

        # Place and center asset
        offset *= scale
        radians = np.radians(self.rotation)
        rotation_offset = np.zeros((3))
        rotation_offset[0] = offset[0] * np.cos(radians[1]) * np.cos(radians[2])
        rotation_offset[1] = offset[1] * np.cos(radians[2]) * np.cos(radians[0])
        rotation_offset[2] = offset[2] * np.cos(radians[0]) * np.cos(radians[1])

        self.coord = self.coord - rotation_offset

        self.translate(self.coord)

    def load_asset(self):
        """ Create asset from object parameters. """

        from omni.isaac.core.utils import prims

        # Create object
        self.asset = prims.create_prim(self.path, "Xform", usd_path=self.ref, semantic_label=self.label)
        self.asset_path = str(self.asset.GetPrimPath())

        self.add_material()

    def get_bounds(self):
        """ Compute min and max bounds of an asset. """

        from pxr import Gf, Usd, UsdGeom

        def recompute_extents(mesh_prim: UsdGeom.Mesh):
            mesh_prim.GetExtentAttr().Set(mesh_prim.ComputeExtent(mesh_prim.GetPointsAttr().Get()))

        sub_model_min_bounds = []
        sub_model_max_bounds = []
        for sub_prim in Usd.PrimRange(self.asset):
            if sub_prim.IsA(UsdGeom.Mesh):
                mesh_prim = UsdGeom.Mesh(sub_prim)

                recompute_extents(mesh_prim)

                bound = mesh_prim.ComputeWorldBound(Usd.TimeCode.Default(), "default").GetBox()
                sub_model_min_bound = np.array(bound.GetMin())
                sub_model_max_bound = np.array(bound.GetMax())

                translation = sub_prim.GetAttribute("xformOp:translate").Get()

                if translation:
                    translation = np.array(translation)

                    sub_model_min_bound += translation
                    sub_model_max_bound += translation

                sub_model_min_bounds.append(sub_model_min_bound)
                sub_model_max_bounds.append(sub_model_max_bound)

        if len(sub_model_min_bounds) > 0:
            min_bound = np.min(sub_model_min_bounds, axis=0)
            max_bound = np.max(sub_model_max_bounds, axis=0)
        else:
            bbox_cache = UsdGeom.BBoxCache(Usd.TimeCode.Default(), includedPurposes=[UsdGeom.Tokens.default_])
            bbox_cache.Clear()  # might not be needed

            total_bound = Gf.BBox3d()
            bound = bbox_cache.ComputeWorldBound(self.asset)
            bound = Gf.BBox3d.Combine(total_bound, Gf.BBox3d(bound.ComputeAlignedRange())).GetBox()

            min_bound = np.array(bound.GetMin())
            max_bound = np.array(bound.GetMax())

        return min_bound, max_bound

    def add_material(self):
        """ Add material to asset, if needed. """

        from pxr import UsdShade

        material = self.sample(self.concat("material"))
        color = self.sample(self.concat("color"))
        texture = self.sample(self.concat("texture"))
        texture_tile_scale = self.sample(self.concat("texture_tile_scale"))
        texture_rot = self.sample(self.concat("texture_rot"))
        reflectance = self.sample(self.concat("reflectance"))
        metallic = self.sample(self.concat("metallicness"))

        mtl_prim_path = None
        if self.is_given(material):
            # Load a material
            mtl_prim_path = self.load_material_from_nucleus(material)
        elif self.is_given(color) or self.is_given(texture):
            # Load a new material
            mtl_prim_path = self.create_material()

        if mtl_prim_path:
            # Update material properties and assign to asset
            mtl_prim = self.update_material(
                mtl_prim_path, color, texture, texture_tile_scale, texture_rot, reflectance, metallic
            )
            UsdShade.MaterialBindingAPI(self.asset).Bind(mtl_prim, UsdShade.Tokens.strongerThanDescendants)

    def load_material_from_nucleus(self, material):
        """ Create material from Nucleus path. """

        import omni
        from pxr import Sdf

        mtl_url = self.sample("nucleus_server") + material
        left_index = material.rfind("/") + 1 if "/" in material else 0
        right_index = material.rfind(".") if "." in material else -1
        mtl_name = material[left_index:right_index].replace("-", "_")
        mtl_prim_path = Sdf.Path("/Looks/" + mtl_name)

        omni.kit.commands.execute("CreateMdlMaterialPrim", mtl_url=mtl_url, mtl_name=mtl_name, mtl_path=mtl_prim_path)

        return mtl_prim_path

    def create_material(self):
        """ Create a OmniPBR material with provided properties and assign to asset. """

        import omni
        from pxr import Sdf

        mtl_created_list = []
        omni.kit.commands.execute(
            "CreateAndBindMdlMaterialFromLibrary",
            mdl_name="OmniPBR.mdl",
            mtl_name="OmniPBR",
            mtl_created_list=mtl_created_list,
        )
        mtl_prim_path = Sdf.Path(mtl_created_list[0])

        return mtl_prim_path

    def update_material(self, mtl_prim_path, color, texture, texture_tile_scale, texture_rot, reflectance, metallic):
        """ Update properties of an existing material. """

        import omni
        from pxr import Sdf, UsdShade

        mtl_prim = UsdShade.Material(self.stage.GetPrimAtPath(mtl_prim_path))

        if self.is_given(color):
            color = tuple(color / 255)
            omni.usd.create_material_input(mtl_prim, "diffuse_color_constant", color, Sdf.ValueTypeNames.Color3f)
            omni.usd.create_material_input(mtl_prim, "diffuse_tint", color, Sdf.ValueTypeNames.Color3f)

        if self.is_given(texture):
            texture = self.sample("nucleus_server") + texture
            omni.usd.create_material_input(mtl_prim, "diffuse_texture", texture, Sdf.ValueTypeNames.Asset)

        if self.is_given(texture_tile_scale):
            texture_tile_scale = 1 / texture_tile_scale
            omni.usd.create_material_input(
                mtl_prim, "texture_scale", (texture_tile_scale, texture_tile_scale), Sdf.ValueTypeNames.Float2
            )

        if self.is_given(texture_rot):
            omni.usd.create_material_input(mtl_prim, "texture_rotate", texture_rot, Sdf.ValueTypeNames.Float)

        if self.is_given(reflectance):
            roughness = 1 - reflectance
            omni.usd.create_material_input(
                mtl_prim, "reflection_roughness_constant", roughness, Sdf.ValueTypeNames.Float
            )
        if self.is_given(metallic):
            omni.usd.create_material_input(mtl_prim, "metallic_constant", metallic, Sdf.ValueTypeNames.Float)

        return mtl_prim

    def add_physics(self):
        """ Make asset a rigid body to enable gravity and collision. """

        from omni.physx.scripts import utils
        from pxr import UsdPhysics

        if self.sample("obj_physics"):
            utils.setRigidBody(self.asset, "convexHull", False)
            # Set mass to 1 kg
            mass_api = UsdPhysics.MassAPI.Apply(self.asset)
            mass_api.CreateMassAttr(1)
            self.physics = True
