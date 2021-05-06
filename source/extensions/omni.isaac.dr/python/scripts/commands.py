from pxr import Gf, Usd, UsdGeom, Sdf, Vt
import omni.isaac.DrSchema as DrSchema
import omni.kit
import omni.usd


class CreateColorComponentCommand(omni.kit.commands.Command):
    """Commands class to create a color randomization component.

        Typical usage example:

        .. code-block:: python

            result, prim = omni.kit.commands.execute(
                "CreateColorComponentCommand",
                prim_paths=["/World/Cube", "/World/Cube1"],
                first_color_range=(0.0, 0.0, 0.0),
                second_color_range=(1.0, 1.0, 1.0),
                roughness_range=(0.0, 1.0),
                metallic_range=(0.0, 1.0),
                duration=1.0,
                include_children=False,
            )
    """

    def __init__(
        self,
        path=None,
        prim_paths=[],
        first_color_range=(0.0, 0.0, 0.0),
        second_color_range=(1.0, 1.0, 1.0),
        roughness_range=(0.0, 1.0),
        metallic_range=(0.0, 1.0),
        duration=0.0,
        include_children=False,
        seed=12345,
    ):
        self._path = path
        self._prim_paths = prim_paths
        self._first_color_range = first_color_range
        self._second_color_range = second_color_range
        self._roughness_range = roughness_range
        self._metallic_range = metallic_range
        self._duration = duration
        self._include_children = include_children
        self._seed = seed

    def do(self):
        """Create a color randomization component"""
        stage = omni.usd.get_context().get_stage()
        default_prim_path = str(stage.GetDefaultPrim().GetPath())
        if self._path is None:
            self._path = omni.usd.get_stage_next_free_path(stage, default_prim_path + "/color_component", False)
        prim = DrSchema.ColorComponent.Define(stage, Sdf.Path(self._path))
        path_split = self._path.split("/")
        prim.CreateCompNameAttr().Set(str(path_split[len(path_split) - 1]))
        # Set attributes for DR color component
        rel_paths = prim.CreatePrimPathsRel()
        for path in self._prim_paths:
            rel_paths.AddTarget(path)
        prim.CreateFirstColorAttr().Set(
            (float(self._first_color_range[0]), float(self._first_color_range[1]), float(self._first_color_range[2]))
        )
        prim.CreateSecondColorAttr().Set(
            (float(self._second_color_range[0]), float(self._second_color_range[1]), float(self._second_color_range[2]))
        )
        prim.CreateRoughnessAttr().Set((float(self._roughness_range[0]), float(self._roughness_range[1])))
        prim.CreateMetallicAttr().Set(((float(self._metallic_range[0]), float(self._metallic_range[1]))))
        prim.CreateDurationAttr().Set(self._duration)
        prim.CreateIncludeChildrenAttr().Set(bool(self._include_children))
        prim.CreateSeedAttr().Set(int(self._seed))
        return prim


class CreateMovementComponentCommand(omni.kit.commands.Command):
    """Commands class to create a movement randomization component.

        Typical usage example:

        .. code-block:: python

            result, prim = omni.kit.commands.execute(
                "CreateMovementComponentCommand",
                prim_paths=["/World/Cube", "/World/Cube1"],
                min_range=(0.0, 0.0, 0.0),
                max_range=(100.0, 100.0, 100.0),
                duration=1.0,
                include_children=False,
            )
    """

    def __init__(
        self,
        path=None,
        prim_paths=[],
        min_range=(0.0, 0.0, 0.0),
        max_range=(100.0, 100.0, 100.0),
        target_position=None,
        target_paths=None,
        polygon_points=[],
        draw_polygon=False,
        target_points=[],
        lookat_target_points=[],
        enable_sequential_behavior=False,
        duration=0.0,
        include_children=False,
        seed=12345,
    ):
        self._path = path
        self._prim_paths = prim_paths
        self._min_range = min_range
        self._max_range = max_range
        self._target_position = target_position
        self._target_paths = target_paths
        self._polygon_points = polygon_points
        self._draw_polygon = draw_polygon
        self._target_points = target_points
        self._lookat_target_points = lookat_target_points
        self._enable_sequential_behavior = enable_sequential_behavior
        self._duration = duration
        self._include_children = include_children
        self._seed = seed

    def do(self):
        """Create a movement randomization component, if target position or paths are specified the object will point towards that target"""
        stage = omni.usd.get_context().get_stage()
        default_prim_path = str(stage.GetDefaultPrim().GetPath())
        if self._path is None:
            self._path = omni.usd.get_stage_next_free_path(stage, default_prim_path + "/movement_component", False)
        prim = DrSchema.MovementComponent.Define(stage, Sdf.Path(self._path))
        prim.CreateCompNameAttr().Set(str(self._path))

        # Set attributes for DR movement component
        rel_paths = prim.CreatePrimPathsRel()
        for path in self._prim_paths:
            rel_paths.AddTarget(path)
        prim.CreateXRangeAttr().Set((float(self._min_range[0]), float(self._max_range[0])))
        prim.CreateYRangeAttr().Set((float(self._min_range[1]), float(self._max_range[1])))
        prim.CreateZRangeAttr().Set((float(self._min_range[2]), float(self._max_range[2])))
        if self._target_position is not None or self._target_paths is not None:
            prim.CreateEnableLookAtTargetAttr().Set(bool(True))
        else:
            prim.CreateEnableLookAtTargetAttr().Set(bool(False))
        target_rel_paths = prim.CreateLookAtTargetPathsRel()
        # if multiple targets are specified, the average of all positions is taken
        if self._target_paths is not None:
            for path in self._target_paths:
                target_rel_paths.AddTarget(path)
        # if no target prim is specified, this value used as the target, if a prim is specified this acts like an offset.
        if self._target_position is not None:
            prim.CreateLookAtTargetOffsetAttr().Set(self._target_position)
        prim.CreateDurationAttr().Set(self._duration)
        prim.CreateIncludeChildrenAttr().Set(bool(self._include_children))
        prim.CreateSeedAttr().Set(int(self._seed))
        prim.CreatePolygonPointsAttr().Set(self._polygon_points)
        prim.CreateDrawPolygonAttr().Set(self._draw_polygon)
        prim.CreateTargetPointsAttr().Set(self._target_points)
        prim.CreateLookAtTargetPointsAttr().Set(self._lookat_target_points)
        prim.CreateEnableSequentialBehaviorAttr().Set(self._enable_sequential_behavior)
        return prim


class CreateRotationComponentCommand(omni.kit.commands.Command):
    """Commands class to create a rotation randomization component.

        Typical usage example:

        .. code-block:: python

            result, prim = omni.kit.commands.execute(
                "CreateRotationComponentCommand",
                prim_paths=["/World/Cube", "/World/Cube1"],
                min_range=(0.0, 0.0, 0.0),
                max_range=(360.0, 360.0, 360.0),
                duration=1.0,
                include_children=False,
            )
    """

    def __init__(
        self,
        path=None,
        prim_paths=[],
        min_range=(0.0, 0.0, 0.0),
        max_range=(360.0, 360.0, 360.0),
        duration=0.0,
        include_children=False,
        seed=12345,
    ):
        self._path = path
        self._prim_paths = prim_paths
        self._min_range = min_range
        self._max_range = max_range
        self._duration = duration
        self._include_children = include_children
        self._seed = seed

    def do(self):
        """Create a rotation randomization component"""
        stage = omni.usd.get_context().get_stage()
        default_prim_path = str(stage.GetDefaultPrim().GetPath())
        if self._path is None:
            self._path = omni.usd.get_stage_next_free_path(stage, default_prim_path + "/rotation_component", False)
        prim = DrSchema.RotationComponent.Define(stage, Sdf.Path(self._path))
        prim.CreateCompNameAttr().Set(str(self._path))

        # Set attributes for DR rotation component
        rel_paths = prim.CreatePrimPathsRel()
        for path in self._prim_paths:
            rel_paths.AddTarget(path)
        prim.CreateXRangeAttr().Set((float(self._min_range[0]), float(self._max_range[0])))
        prim.CreateYRangeAttr().Set((float(self._min_range[1]), float(self._max_range[1])))
        prim.CreateZRangeAttr().Set((float(self._min_range[2]), float(self._max_range[2])))
        prim.CreateDurationAttr().Set(self._duration)
        prim.CreateIncludeChildrenAttr().Set(bool(self._include_children))
        prim.CreateSeedAttr().Set(int(self._seed))
        return prim


class CreateScaleComponentCommand(omni.kit.commands.Command):
    """Commands class to create a scale randomization component.

        Typical usage example:

        .. code-block:: python

            result, prim = omni.kit.commands.execute(
                "CreateScaleComponentCommand",
                prim_paths=["/World/Cube", "/World/Cube1"],
                min_range=(1.0, 1.0, 1.0),
                max_range=(5.0, 5.0, 5.0),
                duration=1.0,
                include_children=False,
            )
    """

    def __init__(
        self,
        path=None,
        prim_paths=[],
        min_range=(1.0, 1.0, 1.0),
        max_range=(5.0, 5.0, 5.0),
        uniform_scaling=False,
        duration=0.0,
        include_children=False,
        seed=12345,
    ):
        self._path = path
        self._prim_paths = prim_paths
        self._min_range = min_range
        self._max_range = max_range
        self._uniform_scaling = uniform_scaling
        self._duration = duration
        self._include_children = include_children
        self._seed = seed

    def do(self):
        """Create a scale randomization component"""
        stage = omni.usd.get_context().get_stage()
        default_prim_path = str(stage.GetDefaultPrim().GetPath())
        if self._path is None:
            self._path = omni.usd.get_stage_next_free_path(stage, default_prim_path + "/scale_component", False)
        prim = DrSchema.ScaleComponent.Define(stage, Sdf.Path(self._path))
        prim.CreateCompNameAttr().Set(str(self._path))

        # Set attributes for DR scale component
        rel_paths = prim.CreatePrimPathsRel()
        for path in self._prim_paths:
            rel_paths.AddTarget(path)
        prim.CreateXRangeAttr().Set((float(self._min_range[0]), float(self._max_range[0])))
        prim.CreateYRangeAttr().Set((float(self._min_range[1]), float(self._max_range[1])))
        prim.CreateZRangeAttr().Set((float(self._min_range[2]), float(self._max_range[2])))
        prim.CreateEnableUniformAttr().Set(bool(self._uniform_scaling))
        prim.CreateDurationAttr().Set(self._duration)
        prim.CreateIncludeChildrenAttr().Set(bool(self._include_children))
        prim.CreateSeedAttr().Set(int(self._seed))
        return prim


class CreateTransformComponentCommand(omni.kit.commands.Command):
    """Commands class to create a transform randomization component.

        Typical usage example:

        .. code-block:: python

            result, prim = omni.kit.commands.execute(
                "CreateTransformComponentCommand",
                prim_paths=["/World/Cube", "/World/Cube1"],
                min_range=(0.0, 0.0, 0.0),
                max_range=(100.0, 100.0, 100.0),
                duration=1.0,
                include_children=False,
            )
    """

    def __init__(
        self,
        path=None,
        prim_paths=[],
        translate_min_range=(0.0, 0.0, 0.0),
        translate_max_range=(100.0, 100.0, 100.0),
        rotate_min_range=(0.0, 0.0, 0.0),
        rotate_max_range=(0.0, 0.0, 0.0),
        scale_min_range=(0.0, 0.0, 0.0),
        scale_max_range=(0.0, 0.0, 0.0),
        target_position=None,
        target_paths=None,
        polygon_points=[],
        draw_polygon=False,
        target_points=[],
        lookat_target_points=[],
        target_point_instancer_paths=None,
        enable_sequential_behavior=False,
        combine_random_range=False,
        duration=0.0,
        include_children=False,
        seed=12345,
    ):
        self._path = path
        self._prim_paths = prim_paths
        self._translate_min_range = translate_min_range
        self._translate_max_range = translate_max_range
        self._rotate_min_range = rotate_min_range
        self._rotate_max_range = rotate_max_range
        self._scale_min_range = scale_min_range
        self._scale_max_range = scale_max_range
        self._target_position = target_position
        self._target_paths = target_paths
        self._polygon_points = polygon_points
        self._draw_polygon = draw_polygon
        self._target_points = target_points
        self._lookat_target_points = lookat_target_points
        self._target_point_instancer_paths = target_point_instancer_paths
        self._enable_sequential_behavior = enable_sequential_behavior
        self._combine_random_range = combine_random_range
        self._duration = duration
        self._include_children = include_children
        self._seed = seed

    def do(self):
        """Create a transform randomization component, if target position or paths are specified the object will point towards that target"""
        stage = omni.usd.get_context().get_stage()
        default_prim_path = str(stage.GetDefaultPrim().GetPath())
        if self._path is None:
            self._path = omni.usd.get_stage_next_free_path(stage, default_prim_path + "/transform_component", False)
        prim = DrSchema.TransformComponent.Define(stage, Sdf.Path(self._path))
        prim.CreateCompNameAttr().Set(str(self._path))

        # Set attributes for DR transform component
        rel_paths = prim.CreatePrimPathsRel()
        for path in self._prim_paths:
            rel_paths.AddTarget(path)
        prim.CreateTranslateMinAttr().Set(
            (
                float(self._translate_min_range[0]),
                float(self._translate_min_range[1]),
                float(self._translate_min_range[2]),
            )
        )
        prim.CreateTranslateMaxAttr().Set(
            (
                float(self._translate_max_range[0]),
                float(self._translate_max_range[1]),
                float(self._translate_max_range[2]),
            )
        )
        prim.CreateRotateMinAttr().Set(
            (float(self._rotate_min_range[0]), float(self._rotate_min_range[1]), float(self._rotate_min_range[2]))
        )
        prim.CreateRotateMaxAttr().Set(
            (float(self._rotate_max_range[0]), float(self._rotate_max_range[1]), float(self._rotate_max_range[2]))
        )
        prim.CreateScaleMinAttr().Set(
            (float(self._scale_min_range[0]), float(self._scale_min_range[1]), float(self._scale_min_range[2]))
        )
        prim.CreateScaleMaxAttr().Set(
            (float(self._scale_max_range[0]), float(self._scale_max_range[1]), float(self._scale_max_range[2]))
        )
        if self._target_position is not None or self._target_paths is not None or len(self._lookat_target_points) > 0:
            prim.CreateEnableLookAtTargetAttr().Set(bool(True))
        else:
            prim.CreateEnableLookAtTargetAttr().Set(bool(False))
        target_rel_paths = prim.CreateLookAtTargetPathsRel()
        # if multiple targets are specified, the average of all positions is taken
        if self._target_paths is not None:
            for path in self._target_paths:
                target_rel_paths.AddTarget(path)
        # if no target prim is specified, this value used as the target, if a prim is specified this acts like an offset.
        if self._target_position is not None:
            prim.CreateLookAtTargetOffsetAttr().Set(self._target_position)
        target_point_instancer_rel_paths = prim.CreateTargetPointInstancersRel()
        if self._target_point_instancer_paths is not None:
            for path in self._target_point_instancer_paths:
                target_point_instancer_rel_paths.AddTarget(path)
        prim.CreateDurationAttr().Set(self._duration)
        prim.CreateIncludeChildrenAttr().Set(bool(self._include_children))
        prim.CreateSeedAttr().Set(int(self._seed))
        prim.CreatePolygonPointsAttr().Set(self._polygon_points)
        prim.CreateDrawPolygonAttr().Set(self._draw_polygon)
        prim.CreateTargetPointsAttr().Set(self._target_points)
        prim.CreateLookAtTargetPointsAttr().Set(self._lookat_target_points)
        prim.CreateEnableSequentialBehaviorAttr().Set(self._enable_sequential_behavior)
        prim.CreateCombineRandomRangeAttr().Set(self._combine_random_range)
        return prim


class CreateLightComponentCommand(omni.kit.commands.Command):
    """Commands class to create a light randomization component.

        Typical usage example:

        .. code-block:: python

            result, prim = omni.kit.commands.execute(
                "CreateLightComponentCommand",
                light_paths=["/World/RectLight"],
                first_color_range=(0.9, 0.9, 0.9),
                second_color_range=(1.0, 1.0, 1.0),
                intensity_range=(40000.0, 70000.0),
                temperature_range=(1500.0, 6500.0),
                enable_temperature=True,
                duration=1.0,
                include_children=False,
            )
    """

    def __init__(
        self,
        path=None,
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
        self._path = path
        self._light_paths = light_paths
        self._first_color_range = first_color_range
        self._second_color_range = second_color_range
        self._intensity_range = intensity_range
        self._temperature_range = temperature_range
        self._enable_temperature = enable_temperature
        self._duration = duration
        self._include_children = include_children
        self._seed = seed

    def do(self):
        """Create a light randomization component"""

        stage = omni.usd.get_context().get_stage()
        default_prim_path = str(stage.GetDefaultPrim().GetPath())
        if self._path is None:
            self._path = omni.usd.get_stage_next_free_path(stage, default_prim_path + "/light_component", False)
        prim = DrSchema.LightComponent.Define(stage, Sdf.Path(self._path))
        prim.CreateCompNameAttr().Set(str(self._path))

        # Set attributes for DR light component
        rel_paths = prim.CreatePrimPathsRel()
        for path in self._light_paths:
            rel_paths.AddTarget(path)
        prim.CreateFirstColorAttr().Set(
            (float(self._first_color_range[0]), float(self._first_color_range[1]), float(self._first_color_range[2]))
        )
        prim.CreateSecondColorAttr().Set(
            (float(self._second_color_range[0]), float(self._second_color_range[1]), float(self._second_color_range[2]))
        )
        prim.CreateIntensityRangeAttr().Set((float(self._intensity_range[0]), float(self._intensity_range[1])))
        prim.CreateTemperatureRangeAttr().Set((float(self._temperature_range[0]), float(self._temperature_range[1])))
        prim.CreateEnableTemperatureAttr().Set(bool(self._enable_temperature))
        prim.CreateDurationAttr().Set(self._duration)
        prim.CreateIncludeChildrenAttr().Set(bool(self._include_children))
        prim.CreateSeedAttr().Set(int(self._seed))
        return prim


class CreateTextureComponentCommand(omni.kit.commands.Command):
    """Commands class to create a texture randomization component.

        Typical usage example:

        .. code-block:: python

            texture_list = [
                <server_path> + "/texture1.png",
                <server_path> + "/texture2.png",
            ]
            result, prim = omni.kit.commands.execute(
                "CreateTextureComponentCommand",
                prim_paths=["/World/Room"],
                enable_project_uvw=False,
                texture_list=texture_list,
                duration=1.0,
                include_children=True,
            )
    """

    def __init__(
        self,
        path=None,
        prim_paths=[],
        enable_project_uvw=False,
        texture_list=[],
        ignored_class_list=[],
        grouped_class_list=[],
        duration=0.0,
        include_children=False,
        seed=12345,
    ):
        self._path = path
        self._prim_paths = prim_paths
        self._enable_project_uvw = enable_project_uvw
        self._texture_list = texture_list
        self._ignored_class_list = ignored_class_list
        self._grouped_class_list = grouped_class_list
        self._duration = duration
        self._include_children = include_children
        self._seed = seed

    def do(self):
        """Create a texture randomization component"""

        stage = omni.usd.get_context().get_stage()
        default_prim_path = str(stage.GetDefaultPrim().GetPath())
        if self._path is None:
            self._path = omni.usd.get_stage_next_free_path(stage, default_prim_path + "/texture_component", False)
        prim = DrSchema.TextureComponent.Define(stage, Sdf.Path(self._path))
        path_split = self._path.split("/")
        prim.CreateCompNameAttr().Set(str(path_split[len(path_split) - 1]))

        # Set attributes for DR texture component
        rel_paths = prim.CreatePrimPathsRel()
        for path in self._prim_paths:
            rel_paths.AddTarget(path)
        prim.CreateEnableProjectUVWAttr().Set(bool(self._enable_project_uvw))
        prim.CreateTextureListAttr().Set(str(",").join(self._texture_list))
        prim.CreateIgnoredClassAttr().Set(str(",").join(self._ignored_class_list))
        prim.CreateGroupedClassAttr().Set(str(",").join(self._grouped_class_list))
        prim.CreateIncludeChildrenAttr().Set(bool(self._include_children))
        prim.CreateDurationAttr().Set(self._duration)
        prim.CreateSeedAttr().Set(int(self._seed))
        return prim


class CreateMaterialComponentCommand(omni.kit.commands.Command):
    """Commands class to create a material randomization component.

        Typical usage example:

        .. code-block:: python

            material_list = [
                <server_path> + "/material1.mdl",
                <server_path> + "/material2.mdl",
            ]
            result, prim = omni.kit.commands.execute(
                "CreateMaterialComponentCommand",
                prim_paths=["/World/Room"],
                material_list=material_list,
                duration=1.0,
                include_children=True,
            )
    """

    def __init__(
        self,
        path=None,
        prim_paths=[],
        material_list=[],
        ignored_class_list=[],
        grouped_class_list=[],
        loaded_material_paths=[],
        duration=0.0,
        include_children=False,
        seed=12345,
    ):
        self._path = path
        self._prim_paths = prim_paths
        self._material_list = material_list
        self._ignored_class_list = ignored_class_list
        self._grouped_class_list = grouped_class_list
        self._loaded_material_paths = loaded_material_paths
        self._duration = duration
        self._include_children = include_children
        self._seed = seed

    def do(self):
        """Create a material randomization component"""

        stage = omni.usd.get_context().get_stage()
        default_prim_path = str(stage.GetDefaultPrim().GetPath())
        if self._path is None:
            self._path = omni.usd.get_stage_next_free_path(stage, default_prim_path + "/material_component", False)
        prim = DrSchema.MaterialComponent.Define(stage, Sdf.Path(self._path))
        path_split = self._path.split("/")
        prim.CreateCompNameAttr().Set(str(path_split[len(path_split) - 1]))

        # Set attributes for DR material component
        rel_paths = prim.CreatePrimPathsRel()
        for path in self._prim_paths:
            rel_paths.AddTarget(path)
        prim.CreateMaterialListAttr().Set(str(",").join(self._material_list))
        prim.CreateIgnoredClassAttr().Set(str(",").join(self._ignored_class_list))
        prim.CreateGroupedClassAttr().Set(str(",").join(self._grouped_class_list))
        mat_paths = prim.CreateLoadedMaterialPrimPathsRel()
        for path in self._loaded_material_paths:
            mat_paths.AddTarget(path)
        prim.CreateIncludeChildrenAttr().Set(bool(self._include_children))
        prim.CreateDurationAttr().Set(self._duration)
        prim.CreateSeedAttr().Set(int(self._seed))
        return prim


class CreateMeshComponentCommand(omni.kit.commands.Command):
    """Commands class to create a mesh randomization component.

        Typical usage example:

        .. code-block:: python

            mesh_list = [
                <server_path> + "/mesh1.mdl",
                <server_path> + "/mesh2.mdl",
            ]
            result, prim = omni.kit.commands.execute(
                "CreateMeshComponentCommand",
                mesh_list=mesh_list,
                mesh_range=[3, 5],
            )
    """

    def __init__(
        self,
        path=None,
        prim_paths=[],
        mesh_list=[],
        mesh_range=(1, 1),
        duration=0.0,
        include_children=False,
        seed=12345,
    ):
        self._path = path
        self._prim_paths = prim_paths
        self._mesh_list = mesh_list
        self._mesh_range = mesh_range
        self._duration = duration
        self._include_children = include_children
        self._seed = seed

    def do(self):
        """Create a mesh randomization component"""
        stage = omni.usd.get_context().get_stage()
        default_prim_path = str(stage.GetDefaultPrim().GetPath())
        if self._path is None:
            self._path = omni.usd.get_stage_next_free_path(stage, default_prim_path + "/mesh_component", False)
        prim = DrSchema.MeshComponent.Define(stage, Sdf.Path(self._path))
        path_split = self._path.split("/")
        prim.CreateCompNameAttr().Set(str(path_split[len(path_split) - 1]))

        rel_paths = prim.CreatePrimPathsRel()
        for path in self._prim_paths:
            rel_paths.AddTarget(path)
        prim.CreateMeshListAttr().Set(str(",").join(self._mesh_list))
        prim.CreateNumMeshRangeAttr().Set(Gf.Vec2i(self._mesh_range[0], self._mesh_range[1]))
        prim.CreateDurationAttr().Set(self._duration)
        prim.CreateIncludeChildrenAttr().Set(bool(self._include_children))
        prim.CreateSeedAttr().Set(int(self._seed))
        return prim


class CreateVisibilityComponentCommand(omni.kit.commands.Command):
    """Commands class to create a visibility randomization component.

        Typical usage example:

        .. code-block:: python

            result, prim = omni.kit.commands.execute(
                "CreateVisibilityComponentCommand",
                prim_paths=["/World/Cube", "/World/Cube1", "/World/Cube2", "/World/Cube3", "/World/Cube4"],
                num_visible_range=[1, 3],
                duration=1.0,
            )
    """

    def __init__(
        self, path=None, prim_paths=[], num_visible_range=(1, 1), duration=0.0, include_children=False, seed=12345
    ):
        self._path = path
        self._prim_paths = prim_paths
        self._num_visible_range = num_visible_range
        self._duration = duration
        self._include_children = include_children
        self._seed = seed

    def do(self):
        """Create a visibility randomization component"""
        stage = omni.usd.get_context().get_stage()
        default_prim_path = str(stage.GetDefaultPrim().GetPath())
        if self._path is None:
            self._path = omni.usd.get_stage_next_free_path(stage, default_prim_path + "/visibility_component", False)
        prim = DrSchema.VisibilityComponent.Define(stage, Sdf.Path(self._path))
        path_split = self._path.split("/")
        prim.CreateCompNameAttr().Set(str(path_split[len(path_split) - 1]))

        # Set attributes for DR visibility component
        rel_paths = prim.CreatePrimPathsRel()
        for path in self._prim_paths:
            rel_paths.AddTarget(path)
        prim.CreateNumVisibleRangeAttr().Set(Gf.Vec2i(int(self._num_visible_range[0]), int(self._num_visible_range[1])))
        prim.CreateDurationAttr().Set(self._duration)
        prim.CreateIncludeChildrenAttr().Set(bool(self._include_children))
        prim.CreateSeedAttr().Set(int(self._seed))
        return prim


class CreateAttributeComponentCommand(omni.kit.commands.Command):
    """Commands class to create a visibility randomization component.

        Typical usage example:

        .. code-block:: python

            result, prim = omni.kit.commands.execute(
                "CreateAttributeCommand",
                prim_paths=["/World/Cube", "/World/Cube1", "/World/Cube2", "/World/Cube3", "/World/Cube4"],
                duration=1.0,
            )
    """

    def __init__(self, path=None, prim_paths=[], custom_data=dict(), duration=0.0, include_children=False, seed=12345):
        self._path = path
        self._prim_paths = prim_paths
        self._custom_data = custom_data
        self._duration = duration
        self._include_children = include_children
        self._seed = seed

    def do(self):
        """Create a attribute randomization component"""
        stage = omni.usd.get_context().get_stage()
        default_prim_path = str(stage.GetDefaultPrim().GetPath())
        if self._path is None:
            self._path = omni.usd.get_stage_next_free_path(stage, default_prim_path + "/attribute_component", False)
        prim = DrSchema.AttributeComponent.Define(stage, Sdf.Path(self._path))
        path_split = self._path.split("/")
        prim.CreateCompNameAttr().Set(str(path_split[len(path_split) - 1]))
        usd_prim = stage.GetPrimAtPath(Sdf.Path(self._path))
        usd_prim.SetCustomData(self._custom_data)

        # Set attributes for DR attribute component
        rel_paths = prim.CreatePrimPathsRel()
        for path in self._prim_paths:
            rel_paths.AddTarget(path)
        prim.CreateDurationAttr().Set(self._duration)
        prim.CreateIncludeChildrenAttr().Set(bool(self._include_children))
        prim.CreateSeedAttr().Set(int(self._seed))
        return prim


omni.kit.commands.register_all_commands_in_module(__name__)
