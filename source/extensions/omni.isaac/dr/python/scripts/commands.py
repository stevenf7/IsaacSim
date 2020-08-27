from pxr import Gf, Usd, UsdGeom, Sdf
import omni.isaac.DrSchema as DrSchema
import omni.kit
import omni.kit.ui
import omni.usd


class CreateColorComponentCommand(omni.kit.commands.Command):
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
            self._path = omni.kit.utils.get_stage_next_free_path(stage, default_prim_path + "/color_component", False)
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
        prim.CreateDurationAttr().Set(float(self._duration))
        prim.CreateIncludeChildrenAttr().Set(bool(self._include_children))
        prim.CreateSeedAttr().Set(int(self._seed))
        return prim


class CreateMovementComponentCommand(omni.kit.commands.Command):
    def __init__(
        self,
        path=None,
        prim_paths=[],
        min_range=(0.0, 0.0, 0.0),
        max_range=(100.0, 100.0, 100.0),
        target_position=None,
        target_paths=None,
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
        self._duration = duration
        self._include_children = include_children
        self._seed = seed

    def do(self):
        """Create a movement randomization component, if target position or paths are specified the object will point towards that target"""
        stage = omni.usd.get_context().get_stage()
        default_prim_path = str(stage.GetDefaultPrim().GetPath())
        if self._path is None:
            self._path = omni.kit.utils.get_stage_next_free_path(
                stage, default_prim_path + "/movement_component", False
            )
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
        prim.CreateDurationAttr().Set(float(self._duration))
        prim.CreateIncludeChildrenAttr().Set(bool(self._include_children))
        prim.CreateSeedAttr().Set(int(self._seed))
        return prim


class CreateRotationComponentCommand(omni.kit.commands.Command):
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
            self._path = omni.kit.utils.get_stage_next_free_path(
                stage, default_prim_path + "/rotation_component", False
            )
        prim = DrSchema.RotationComponent.Define(stage, Sdf.Path(self._path))
        prim.CreateCompNameAttr().Set(str(self._path))

        # Set attributes for DR rotation component
        rel_paths = prim.CreatePrimPathsRel()
        for path in self._prim_paths:
            rel_paths.AddTarget(path)
        prim.CreateXRangeAttr().Set((float(self._min_range[0]), float(self._max_range[0])))
        prim.CreateYRangeAttr().Set((float(self._min_range[1]), float(self._max_range[1])))
        prim.CreateZRangeAttr().Set((float(self._min_range[2]), float(self._max_range[2])))
        prim.CreateDurationAttr().Set(float(self._duration))
        prim.CreateIncludeChildrenAttr().Set(bool(self._include_children))
        prim.CreateSeedAttr().Set(int(self._seed))
        return prim


class CreateScaleComponentCommand(omni.kit.commands.Command):
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
            self._path = omni.kit.utils.get_stage_next_free_path(stage, default_prim_path + "/scale_component", False)
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
        prim.CreateDurationAttr().Set(float(self._duration))
        prim.CreateIncludeChildrenAttr().Set(bool(self._include_children))
        prim.CreateSeedAttr().Set(int(self._seed))
        return prim


class CreateLightComponentCommand(omni.kit.commands.Command):
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
            self._path = omni.kit.utils.get_stage_next_free_path(stage, default_prim_path + "/light_component", False)
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
        prim.CreateDurationAttr().Set(float(self._duration))
        prim.CreateIncludeChildrenAttr().Set(bool(self._include_children))
        prim.CreateSeedAttr().Set(int(self._seed))
        return prim


class CreateTextureComponentCommand(omni.kit.commands.Command):
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
            self._path = omni.kit.utils.get_stage_next_free_path(stage, default_prim_path + "/texture_component", False)
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
        prim.CreateDurationAttr().Set(float(self._duration))
        prim.CreateSeedAttr().Set(int(self._seed))
        return prim


class CreateMaterialComponentCommand(omni.kit.commands.Command):
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
            self._path = omni.kit.utils.get_stage_next_free_path(
                stage, default_prim_path + "/material_component", False
            )
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
        prim.CreateDurationAttr().Set(float(self._duration))
        prim.CreateSeedAttr().Set(int(self._seed))
        return prim


class CreateMeshComponentCommand(omni.kit.commands.Command):
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
            self._path = omni.kit.utils.get_stage_next_free_path(stage, default_prim_path + "/mesh_component", False)
        prim = DrSchema.MeshComponent.Define(stage, Sdf.Path(self._path))
        path_split = self._path.split("/")
        prim.CreateCompNameAttr().Set(str(path_split[len(path_split) - 1]))

        rel_paths = prim.CreatePrimPathsRel()
        for path in self._prim_paths:
            rel_paths.AddTarget(path)
        prim.CreateMeshListAttr().Set(str(",").join(self._mesh_list))
        prim.CreateNumMeshRangeAttr().Set(Gf.Vec2i(self._mesh_range[0], self._mesh_range[1]))
        prim.CreateDurationAttr().Set(float(self._duration))
        prim.CreateIncludeChildrenAttr().Set(bool(self._include_children))
        prim.CreateSeedAttr().Set(int(self._seed))
        return prim


class CreateVisibilityComponentCommand(omni.kit.commands.Command):
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
            self._path = omni.kit.utils.get_stage_next_free_path(
                stage, default_prim_path + "/visibility_component", False
            )
        prim = DrSchema.VisibilityComponent.Define(stage, Sdf.Path(self._path))
        path_split = self._path.split("/")
        prim.CreateCompNameAttr().Set(str(path_split[len(path_split) - 1]))

        # Set attributes for DR visibility component
        rel_paths = prim.CreatePrimPathsRel()
        for path in self._prim_paths:
            rel_paths.AddTarget(path)
        prim.CreateNumVisibleRangeAttr().Set(Gf.Vec2i(int(self._num_visible_range[0]), int(self._num_visible_range[1])))
        prim.CreateDurationAttr().Set(float(self._duration))
        prim.CreateIncludeChildrenAttr().Set(bool(self._include_children))
        prim.CreateSeedAttr().Set(int(self._seed))
        return prim


omni.kit.commands.register(CreateColorComponentCommand)
omni.kit.commands.register(CreateMovementComponentCommand)
omni.kit.commands.register(CreateRotationComponentCommand)
omni.kit.commands.register(CreateScaleComponentCommand)
omni.kit.commands.register(CreateLightComponentCommand)
omni.kit.commands.register(CreateTextureComponentCommand)
omni.kit.commands.register(CreateMaterialComponentCommand)
omni.kit.commands.register(CreateMeshComponentCommand)
omni.kit.commands.register(CreateVisibilityComponentCommand)
