#!/usr/bin/env python
# Copyright (c) 2020, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.


"""Helper class for creating domain randomization components.
"""

import omni
import omni.isaac.DrSchema as DrSchema
from omni.isaac.dr import _dr
from pxr import Gf, Sdf


class DomainRandomization:
    def __init__(self):
        self.dr = _dr.acquire_dr_interface()

    def randomize_once(self):
        self.dr.randomize_once()

    def toggle_manual_mode(self):
        self.dr.toggle_manual_mode()

    def create_color_comp(
        self,
        prim_paths=[],
        first_color_range=(0.0, 0.0, 0.0),
        second_color_range=(1.0, 1.0, 1.0),
        roughness_range=(0.0, 1.0),
        metallic_range=(0.0, 1.0),
        duration=0.0,
        include_children=False,
    ):
        """Create a color randomization component"""
        stage = omni.usd.get_context().get_stage()
        default_prim_path = str(stage.GetDefaultPrim().GetPath())
        path = omni.kit.utils.get_stage_next_free_path(stage, default_prim_path + "/color_component", False)
        prim = DrSchema.ColorComponent.Define(stage, Sdf.Path(path))
        path_split = path.split("/")
        prim.CreateCompNameAttr().Set(str(path_split[len(path_split) - 1]))

        # Set attributes for DR color component
        rel_paths = prim.CreatePrimPathsRel()
        for path in prim_paths:
            rel_paths.AddTarget(path)
        prim.CreateFirstColorAttr().Set(
            (float(first_color_range[0]), float(first_color_range[1]), float(first_color_range[2]))
        )
        prim.CreateSecondColorAttr().Set(
            (float(second_color_range[0]), float(second_color_range[1]), float(second_color_range[2]))
        )
        prim.CreateRoughnessAttr().Set((float(roughness_range[0]), float(roughness_range[1])))
        prim.CreateMetallicAttr().Set(((float(metallic_range[0]), float(metallic_range[1]))))
        prim.CreateDurationAttr().Set(float(duration))
        prim.CreateIncludeChildrenAttr().Set(bool(include_children))
        return prim

    def create_movement_comp(
        self,
        prim_paths=[],
        min_range=(0.0, 0.0, 0.0),
        max_range=(100.0, 100.0, 100.0),
        target_position=None,
        target_paths=None,
        duration=0.0,
        include_children=False,
    ):
        """Create a movement randomization component, if target position or paths are specified the object will point towards that target"""
        stage = omni.usd.get_context().get_stage()
        default_prim_path = str(stage.GetDefaultPrim().GetPath())
        path = omni.kit.utils.get_stage_next_free_path(stage, default_prim_path + "/movement_component", False)
        prim = DrSchema.MovementComponent.Define(stage, Sdf.Path(path))
        prim.CreateCompNameAttr().Set(str(path))

        # Set attributes for DR movement component
        rel_paths = prim.CreatePrimPathsRel()
        for path in prim_paths:
            rel_paths.AddTarget(path)
        prim.CreateXRangeAttr().Set((float(min_range[0]), float(max_range[0])))
        prim.CreateYRangeAttr().Set((float(min_range[1]), float(max_range[1])))
        prim.CreateZRangeAttr().Set((float(min_range[2]), float(max_range[2])))
        if target_position is not None or target_paths is not None:
            prim.CreateEnableLookAtTargetAttr().Set(bool(True))
        else:
            prim.CreateEnableLookAtTargetAttr().Set(bool(False))
        target_rel_paths = prim.CreateLookAtTargetPathsRel()
        # if multiple targets are specified, the average of all positions is taken
        if target_paths is not None:
            for path in target_paths:
                target_rel_paths.AddTarget(path)
        # if no target prim is specified, this value used as the target, if a prim is specified this acts like an offset.
        if target_position is not None:
            prim.CreateLookAtTargetOffsetAttr().Set(target_position)
        prim.CreateDurationAttr().Set(float(duration))
        prim.CreateIncludeChildrenAttr().Set(bool(include_children))
        return prim

    def create_rotation_comp(
        self,
        prim_paths=[],
        min_range=(0.0, 0.0, 0.0),
        max_range=(360.0, 360.0, 360.0),
        duration=0.0,
        include_children=False,
    ):
        """Create a rotation randomization component"""
        stage = omni.usd.get_context().get_stage()
        default_prim_path = str(stage.GetDefaultPrim().GetPath())
        path = omni.kit.utils.get_stage_next_free_path(stage, default_prim_path + "/rotation_component", False)
        prim = DrSchema.RotationComponent.Define(stage, Sdf.Path(path))
        prim.CreateCompNameAttr().Set(str(path))

        # Set attributes for DR rotation component
        rel_paths = prim.CreatePrimPathsRel()
        for path in prim_paths:
            rel_paths.AddTarget(path)
        prim.CreateXRangeAttr().Set((float(min_range[0]), float(max_range[0])))
        prim.CreateYRangeAttr().Set((float(min_range[1]), float(max_range[1])))
        prim.CreateZRangeAttr().Set((float(min_range[2]), float(max_range[2])))
        prim.CreateDurationAttr().Set(float(duration))
        prim.CreateIncludeChildrenAttr().Set(bool(include_children))
        return prim

    def create_scale_comp(
        self, prim_paths=[], min_range=(1.0, 1.0, 1.0), max_range=(5.0, 5.0, 5.0), duration=0.0, include_children=False
    ):
        """Create a scale randomization component"""
        stage = omni.usd.get_context().get_stage()
        default_prim_path = str(stage.GetDefaultPrim().GetPath())
        path = omni.kit.utils.get_stage_next_free_path(stage, default_prim_path + "/scale_component", False)
        prim = DrSchema.ScaleComponent.Define(stage, Sdf.Path(path))
        prim.CreateCompNameAttr().Set(str(path))

        # Set attributes for DR scale component
        rel_paths = prim.CreatePrimPathsRel()
        for path in prim_paths:
            rel_paths.AddTarget(path)
        prim.CreateXRangeAttr().Set((float(min_range[0]), float(max_range[0])))
        prim.CreateYRangeAttr().Set((float(min_range[1]), float(max_range[1])))
        prim.CreateZRangeAttr().Set((float(min_range[2]), float(max_range[2])))
        prim.CreateDurationAttr().Set(float(duration))
        prim.CreateIncludeChildrenAttr().Set(bool(include_children))
        return prim

    def create_light_comp(
        self,
        light_paths=[],
        first_color_range=(0.0, 0.0, 0.0),
        second_color_range=(1.0, 1.0, 1.0),
        intensity_range=(40000.0, 70000.0),
        temperature_range=(1500.0, 6500.0),
        enable_temperature=True,
        duration=0.0,
        include_children=False,
    ):
        """Create a light randomization component"""

        stage = omni.usd.get_context().get_stage()
        default_prim_path = str(stage.GetDefaultPrim().GetPath())
        path = omni.kit.utils.get_stage_next_free_path(stage, default_prim_path + "/light_component", False)
        prim = DrSchema.LightComponent.Define(stage, Sdf.Path(path))
        prim.CreateCompNameAttr().Set(str(path))

        # Set attributes for DR light component
        rel_paths = prim.CreatePrimPathsRel()
        for path in light_paths:
            rel_paths.AddTarget(path)
        prim.CreateFirstColorAttr().Set(
            (float(first_color_range[0]), float(first_color_range[1]), float(first_color_range[2]))
        )
        prim.CreateSecondColorAttr().Set(
            (float(second_color_range[0]), float(second_color_range[1]), float(second_color_range[2]))
        )
        prim.CreateIntensityRangeAttr().Set((float(intensity_range[0]), float(intensity_range[1])))
        prim.CreateTemperatureRangeAttr().Set((float(temperature_range[0]), float(temperature_range[1])))
        prim.CreateEnableTemperatureAttr().Set(bool(enable_temperature))
        prim.CreateDurationAttr().Set(float(duration))
        prim.CreateIncludeChildrenAttr().Set(bool(include_children))
        return prim

    def create_texture_comp(
        self,
        prim_paths=[],
        enable_project_uvw=False,
        texture_list=[],
        ignored_class_list=[],
        grouped_class_list=[],
        duration=0.0,
        include_children=False,
    ):
        """Create a texture randomization component"""

        stage = omni.usd.get_context().get_stage()
        default_prim_path = str(stage.GetDefaultPrim().GetPath())
        path = omni.kit.utils.get_stage_next_free_path(stage, default_prim_path + "/texture_component", False)
        prim = DrSchema.TextureComponent.Define(stage, Sdf.Path(path))
        path_split = path.split("/")
        prim.CreateCompNameAttr().Set(str(path_split[len(path_split) - 1]))

        # Set attributes for DR texture component
        rel_paths = prim.CreatePrimPathsRel()
        for path in prim_paths:
            rel_paths.AddTarget(path)
        prim.CreateEnableProjectUVWAttr().Set(bool(enable_project_uvw))
        prim.CreateTextureListAttr().Set(str(",").join(texture_list))
        prim.CreateIgnoredClassAttr().Set(str(",").join(ignored_class_list))
        prim.CreateGroupedClassAttr().Set(str(",").join(grouped_class_list))
        prim.CreateIncludeChildrenAttr().Set(bool(include_children))
        prim.CreateDurationAttr().Set(float(duration))
        return prim

    def create_material_comp(
        self,
        prim_paths=[],
        material_list=[],
        ignored_class_list=[],
        grouped_class_list=[],
        loaded_material_paths=[],
        duration=0.0,
        include_children=False,
    ):
        """Create a material randomization component"""

        stage = omni.usd.get_context().get_stage()
        default_prim_path = str(stage.GetDefaultPrim().GetPath())
        path = omni.kit.utils.get_stage_next_free_path(stage, default_prim_path + "/material_component", False)
        prim = DrSchema.MaterialComponent.Define(stage, Sdf.Path(path))
        path_split = path.split("/")
        prim.CreateCompNameAttr().Set(str(path_split[len(path_split) - 1]))

        # Set attributes for DR material component
        rel_paths = prim.CreatePrimPathsRel()
        for path in prim_paths:
            rel_paths.AddTarget(path)
        prim.CreateMaterialListAttr().Set(str(",").join(material_list))
        prim.CreateIgnoredClassAttr().Set(str(",").join(ignored_class_list))
        prim.CreateGroupedClassAttr().Set(str(",").join(grouped_class_list))
        mat_paths = prim.CreateLoadedMaterialPrimPathsRel()
        for path in loaded_material_paths:
            mat_paths.AddTarget(path)
        prim.CreateIncludeChildrenAttr().Set(bool(include_children))
        prim.CreateDurationAttr().Set(float(duration))
        return prim

    def create_visibility_comp(self, prim_paths=[], num_visible_range=(1, 1), duration=0.0, include_children=False):
        """Create a material randomization component"""
        stage = omni.usd.get_context().get_stage()
        default_prim_path = str(stage.GetDefaultPrim().GetPath())
        path = omni.kit.utils.get_stage_next_free_path(stage, default_prim_path + "/visibility_component", False)
        prim = DrSchema.VisibilityComponent.Define(stage, Sdf.Path(path))
        path_split = path.split("/")
        prim.CreateCompNameAttr().Set(str(path_split[len(path_split) - 1]))

        # Set attributes for DR visibility component
        rel_paths = prim.CreatePrimPathsRel()
        for path in prim_paths:
            rel_paths.AddTarget(path)
        prim.CreateNumVisibleRangeAttr().Set(Gf.Vec2i(int(num_visible_range[0]), int(num_visible_range[1])))
        prim.CreateDurationAttr().Set(float(duration))
        prim.CreateIncludeChildrenAttr().Set(bool(include_children))
        return prim

    def create_mesh_comp(
        self, path=None, prim_paths=[], mesh_list=[], mesh_range=(1, 1), duration=0.0, include_children=False
    ):
        """Create a mesh randomization component"""
        stage = omni.usd.get_context().get_stage()
        default_prim_path = str(stage.GetDefaultPrim().GetPath())
        if path is None:
            path = omni.kit.utils.get_stage_next_free_path(stage, default_prim_path + "/mesh_component", False)
        prim = DrSchema.MeshComponent.Define(stage, Sdf.Path(path))
        path_split = path.split("/")
        prim.CreateCompNameAttr().Set(str(path_split[len(path_split) - 1]))

        rel_paths = prim.CreatePrimPathsRel()
        for path in prim_paths:
            rel_paths.AddTarget(path)
        prim.CreateMeshListAttr().Set(str(",").join(mesh_list))
        prim.CreateNumMeshRangeAttr().Set(Gf.Vec2i(mesh_range[0], mesh_range[1]))
        prim.CreateDurationAttr().Set(float(duration))
        prim.CreateIncludeChildrenAttr().Set(bool(include_children))
        return prim
