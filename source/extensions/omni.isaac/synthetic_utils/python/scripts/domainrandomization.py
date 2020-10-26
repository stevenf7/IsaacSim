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
import omni.kit.commands
from pxr import Gf, Sdf


class DomainRandomization:
    def __init__(self):
        from omni.isaac.dr import _dr

        self.dr = _dr.acquire_dr_interface()

    def randomize_once(self):
        """Randomizes the scene once. This is mainly executed while in manual mode."""
        self.dr.randomize_once()

    def toggle_manual_mode(self):
        """Toggles mode between manual and non-manual. In manual mode, user can control when scene randomization occur whereas in non-manual mode scene randomization is controlled via the duration parameter in various DR components."""
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
        seed=12345,
    ):
        """Create a color randomization component

        args:
            prim_paths (list(str)): List of path of prims to be used for randomization.
            first_color_range (tuple(float, float, float), optional): Specify the minimum R, G, B values. The scale is from 0 to 1.
            second_color_range (tuple(float, float, float), optional): Specify the maximum R, G, B values. The scale is from 0 to 1.
            roughness_range (tuple(float, float), optional): Specify the range for roughness property. The scale is from 0 to 1.
            metallic_range (tuple(float, float), optional): Specify the range for metallic property. The scale is from 0 to 1.
            duration (float, optional):  Time interval in seconds between subsequent randomization.
            include_children (bool, optional): Enable if only the child prims need to be included for randomization.
            seed (int, optional): Value to initialize the pseudorandom number generator.
        """
        stage = omni.usd.get_context().get_stage()
        default_prim_path = str(stage.GetDefaultPrim().GetPath())
        path = omni.kit.utils.get_stage_next_free_path(stage, default_prim_path + "/color_component", False)
        result, prim = omni.kit.commands.execute(
            "CreateColorComponentCommand",
            path=path,
            prim_paths=prim_paths,
            first_color_range=first_color_range,
            second_color_range=second_color_range,
            roughness_range=roughness_range,
            metallic_range=metallic_range,
            duration=duration,
            include_children=include_children,
            seed=seed,
        )
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
        seed=12345,
    ):
        """Create a movement randomization component, if target position or paths are specified the object will point towards that target

        args:
            prim_paths (list(str)): List of path of prims to be used for randomization.
            min_range (tuple(float, float, float), optional): Specify the minimum X, Y, Z values for movement along all three axes.
            max_range (tuple(float, float, float), optional): Specify the maximum X, Y, Z values for movement along all three axes.
            target_position (tuple(float, float, float), optional): If target prim is not specified, this value is used as the target to look at, if a prim is specified this acts like an offset.
            target_paths (list(str), optional): Specify path of the target prim to look at. If multiple target paths are specified, the average of all of their prim's location is used to determine target location to look at.
            duration (float, optional):  Time interval in seconds between subsequent randomization.
            include_children (bool, optional): Enable if only the child prims need to be included for randomization.
            seed (int, optional): Value to initialize the pseudorandom number generator.
        """
        stage = omni.usd.get_context().get_stage()
        default_prim_path = str(stage.GetDefaultPrim().GetPath())
        path = omni.kit.utils.get_stage_next_free_path(stage, default_prim_path + "/movement_component", False)
        result, prim = omni.kit.commands.execute(
            "CreateMovementComponentCommand",
            path=path,
            prim_paths=prim_paths,
            min_range=min_range,
            max_range=max_range,
            target_position=target_position,
            target_paths=target_paths,
            duration=duration,
            include_children=include_children,
            seed=seed,
        )
        return prim

    def create_rotation_comp(
        self,
        prim_paths=[],
        min_range=(0.0, 0.0, 0.0),
        max_range=(360.0, 360.0, 360.0),
        duration=0.0,
        include_children=False,
        seed=12345,
    ):
        """Create a rotation randomization component

        args:
            prim_paths (list(str)): List of path of prims to be used for randomization.
            min_range (tuple(float, float, float), optional): Specify the minimum X, Y, Z values for rotation along all three axes.
            max_range (tuple(float, float, float), optional): Specify the maximum X, Y, Z values for rotation along all three axes.
            duration (float, optional):  Time interval in seconds between subsequent randomization.
            include_children (bool, optional): Enable if only the child prims need to be included for randomization.
            seed (int, optional): Value to initialize the pseudorandom number generator.
        """
        stage = omni.usd.get_context().get_stage()
        default_prim_path = str(stage.GetDefaultPrim().GetPath())
        path = omni.kit.utils.get_stage_next_free_path(stage, default_prim_path + "/rotation_component", False)
        result, prim = omni.kit.commands.execute(
            "CreateRotationComponentCommand",
            path=path,
            prim_paths=prim_paths,
            min_range=min_range,
            max_range=max_range,
            duration=duration,
            include_children=include_children,
            seed=seed,
        )
        return prim

    def create_scale_comp(
        self,
        prim_paths=[],
        min_range=(1.0, 1.0, 1.0),
        max_range=(5.0, 5.0, 5.0),
        uniform_scaling=False,
        duration=0.0,
        include_children=False,
        seed=12345,
    ):
        """Create a scale randomization component

        args:
            prim_paths (list(str)): List of path of prims to be used for randomization.
            min_range (tuple(float, float, float), optional): Specify the minimum X, Y, Z values for scale along all three axes.
            max_range (tuple(float, float, float), optional): Specify the maximum X, Y, Z values for scale along all three axes.
            uniform_scaling (bool, optional): Enable it to scale uniformly along all three axes.
            duration (float, optional):  Time interval in seconds between subsequent randomization.
            include_children (bool, optional): Enable if only the child prims need to be included for randomization.
            seed (int, optional): Value to initialize the pseudorandom number generator.
        """
        stage = omni.usd.get_context().get_stage()
        default_prim_path = str(stage.GetDefaultPrim().GetPath())
        path = omni.kit.utils.get_stage_next_free_path(stage, default_prim_path + "/scale_component", False)
        result, prim = omni.kit.commands.execute(
            "CreateScaleComponentCommand",
            path=path,
            prim_paths=prim_paths,
            min_range=min_range,
            max_range=max_range,
            uniform_scaling=uniform_scaling,
            duration=duration,
            include_children=include_children,
            seed=seed,
        )
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
        seed=12345,
    ):
        """Create a light randomization component

        args:
            prim_paths (list(str)): List of path of prims to be used for randomization.
            first_color_range (tuple(float, float, float), optional): Specify the minimum R, G, B values. The scale is from 0 to 1.
            second_color_range (tuple(float, float, float), optional): Specify the maximum R, G, B values. The scale is from 0 to 1.
            intensity_range (tuple(float, float), optional): Specify the range for intensity property.
            temperature_range (tuple(float, float), optional): Specify the range for temperature property.
            enable_temperature (bool, optional): Enable if temperature property needs to randomized.
            duration (float, optional):  Time interval in seconds between subsequent randomization.
            include_children (bool, optional): Enable if only the child prims need to be included for randomization.
            seed (int, optional): Value to initialize the pseudorandom number generator.
        """

        stage = omni.usd.get_context().get_stage()
        default_prim_path = str(stage.GetDefaultPrim().GetPath())
        path = omni.kit.utils.get_stage_next_free_path(stage, default_prim_path + "/light_component", False)
        result, prim = omni.kit.commands.execute(
            "CreateLightComponentCommand",
            path=path,
            light_paths=light_paths,
            first_color_range=first_color_range,
            second_color_range=second_color_range,
            intensity_range=intensity_range,
            temperature_range=temperature_range,
            enable_temperature=enable_temperature,
            duration=duration,
            include_children=include_children,
            seed=seed,
        )
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
        seed=12345,
    ):
        """Create a texture randomization component

        args:
            prim_paths (list(str)): List of path of prims to be used for randomization.
            enable_project_uvw (bool, optional): Enable to all UVW texture mapping.
            texture_list (list(str), optional): List of texture files to be used for randomization.
            ignored_class_list (list(str), optional): List of class labels. Prim paths that contain these class labels will be ignored during randomization.
            grouped_class_list (list(str), optional): List of class labels. Prim paths that contain these class labels will be grouped with similar textures during randomization. 
            duration (float, optional):  Time interval in seconds between subsequent randomization.
            include_children (bool, optional): Enable if only the child prims of type Mesh need to be included for randomization.
            seed (int, optional): Value to initialize the pseudorandom number generator.
        """

        stage = omni.usd.get_context().get_stage()
        default_prim_path = str(stage.GetDefaultPrim().GetPath())
        path = omni.kit.utils.get_stage_next_free_path(stage, default_prim_path + "/texture_component", False)
        result, prim = omni.kit.commands.execute(
            "CreateTextureComponentCommand",
            path=path,
            prim_paths=prim_paths,
            enable_project_uvw=enable_project_uvw,
            texture_list=texture_list,
            ignored_class_list=ignored_class_list,
            grouped_class_list=grouped_class_list,
            duration=duration,
            include_children=include_children,
        )
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
        seed=12345,
    ):
        """Create a material randomization component

        args:
            prim_paths (list(str)): List of path of prims to be used for randomization.
            material_list (list(str), optional): List of material files(.mdl) to be used for randomization.
            ignored_class_list (list(str), optional): List of class labels. Prim paths that contain these class labels will be ignored during randomization.
            grouped_class_list (list(str), optional): List of class labels. Prim paths that contain these class labels will be grouped with similar textures during randomization. 
            duration (float, optional):  Time interval in seconds between subsequent randomization.
            include_children (bool, optional): Enable if only the child prims of type Mesh need to be included for randomization.
            seed (int, optional): Value to initialize the pseudorandom number generator.
        """

        stage = omni.usd.get_context().get_stage()
        default_prim_path = str(stage.GetDefaultPrim().GetPath())
        path = omni.kit.utils.get_stage_next_free_path(stage, default_prim_path + "/material_component", False)
        result, prim = omni.kit.commands.execute(
            "CreateMaterialComponentCommand",
            path=path,
            prim_paths=prim_paths,
            material_list=material_list,
            ignored_class_list=ignored_class_list,
            grouped_class_list=grouped_class_list,
            loaded_material_paths=loaded_material_paths,
            duration=duration,
            include_children=include_children,
            seed=seed,
        )
        return prim

    def create_mesh_comp(
        self, prim_paths=[], mesh_list=[], mesh_range=(1, 1), duration=0.0, include_children=False, seed=12345
    ):
        """Create a mesh randomization component

        args:
            prim_paths (list(str), optional): List of path of prims to be used for randomization.
            mesh_list (list(str), optional): List of mesh files(.usd) to be spawned.
            mesh_range (tuple(float, float), optional): Specify the range for number of mesh copies to spawn.
            duration (float, optional):  Time interval in seconds between subsequent randomization.
            include_children (bool, optional): Enable if only the child prims of type Mesh need to be included for randomization.
            seed (int, optional): Value to initialize the pseudorandom number generator.
        """
        stage = omni.usd.get_context().get_stage()
        default_prim_path = str(stage.GetDefaultPrim().GetPath())
        path = omni.kit.utils.get_stage_next_free_path(stage, default_prim_path + "/mesh_component", False)
        result, prim = omni.kit.commands.execute(
            "CreateMeshComponentCommand",
            path=path,
            prim_paths=prim_paths,
            mesh_list=mesh_list,
            mesh_range=mesh_range,
            duration=duration,
            include_children=include_children,
            seed=seed,
        )
        return prim

    def create_visibility_comp(
        self, prim_paths=[], num_visible_range=(1, 1), duration=0.0, include_children=False, seed=12345
    ):
        """Create a visibility randomization component

        args:
            prim_paths (list(str), optional): List of path of prims to be used for randomization.
            num_visible_range (tuple(float, float), optional): Specify the range for number of assets that needs to be visible.
            duration (float, optional):  Time interval in seconds between subsequent randomization.
            include_children (bool, optional): Enable if only the child prims of type Mesh need to be included for randomization.
            seed (int, optional): Value to initialize the pseudorandom number generator.
        """
        stage = omni.usd.get_context().get_stage()
        default_prim_path = str(stage.GetDefaultPrim().GetPath())
        path = omni.kit.utils.get_stage_next_free_path(stage, default_prim_path + "/visibility_component", False)
        result, prim = omni.kit.commands.execute(
            "CreateVisibilityComponentCommand",
            path=path,
            prim_paths=prim_paths,
            num_visible_range=num_visible_range,
            duration=duration,
            include_children=include_children,
            seed=seed,
        )
        return prim
