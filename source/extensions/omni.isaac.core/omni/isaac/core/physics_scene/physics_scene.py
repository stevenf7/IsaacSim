# Copyright (c) 2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#


import carb
import omni
from pxr import UsdGeom, Gf, Sdf, UsdPhysics, PhysxSchema
from omni.isaac.core.utils.constants import AXES_INDICES
from omni.isaac.core.utils.prims import get_prim_path
from omni.isaac.core.utils.carb import set_carb_setting
from omni.isaac.core.utils.stage import get_current_stage, traverse_stage


class PhysicsScene:
    def __init__(self, physics_dt=None, prim_path: str = "/World/physicsScene"):
        stage = get_current_stage()
        self._prim_path = prim_path
        if not Sdf.Path(self._prim_path).IsAbsolutePath():
            raise Exception(f"Input prim path is not absolute: {self._path}")
        current_physics_prim = self.get_current_physics_scene_prim()
        self._physx_scene_api = None

        if current_physics_prim is None:
            # creating a new physics scene
            prim = stage.GetPrimAtPath(prim_path)
            if prim.IsValid():
                raise Exception(f"A non physics scene prim already exists at: {self._prim_path}")
            self._physics_scene = self.create_new_physics_scene(prim_path=prim_path)
            if physics_dt is None:
                self.set_physics_dt(dt=1.0 / 60.0)
        else:
            self._prim_path = get_prim_path(current_physics_prim)
            carb.log_info(
                f"Physics Scene at path `{current_physics_prim.GetPath().pathString}` is already defined - reusing it"
            )
            self._physics_scene = UsdPhysics.Scene(current_physics_prim)
            self._physx_scene_api = PhysxSchema.PhysxSceneAPI(current_physics_prim)

        self._physx_interface = omni.physx.acquire_physx_interface()
        meters_per_unit = UsdGeom.GetStageMetersPerUnit(stage)
        self.set_physics_scene_settings(gravity_magnitude=9.81 / meters_per_unit)
        if physics_dt is not None:
            self.set_physics_dt(dt=physics_dt)
        return

    def __del__(self):
        """Destructor for object."""
        return

    def get_current_physics_scene_prim(self):
        for prim in traverse_stage():
            if prim.HasAPI(PhysxSchema.PhysxSceneAPI):
                return prim
        return None

    def create_new_physics_scene(self, prim_path):
        carb.log_info(f"Defining a new Physics Scene at path `{prim_path}`")
        stage = get_current_stage()
        scene = UsdPhysics.Scene.Define(stage, prim_path)
        prim = stage.GetPrimAtPath(prim_path)
        self._physx_scene_api = PhysxSchema.PhysxSceneAPI.Apply(prim)
        return scene

    def set_physics_dt(self, dt: float = 1.0 / 60.0, substeps: int = 1):
        """Specify the physics step size to use when simulating,

        Note:
            A physics scene has to be in the stage for this to do anything.

        Keyword Arguments:
            dt (float): The physics time-step. (default: 1.0/60.0)
            substeps (int): The number of physics time-steps to simulate. (default: 1)
        """
        if dt < 0:
            raise ValueError("physics dt cannot be <0")
        # if no stage or no change in physics timestep, exit.
        if get_current_stage() is None:
            return
        # if physics substeps is not valid, make default = 1.
        if substeps is None or substeps <= 1:
            substeps = 1
        if dt == 0:
            self._physx_scene_api.GetTimeStepsPerSecondAttr().Set(0)
            min_steps = 0
        elif dt > 1.0:
            raise ValueError("physics dt must be <= 1.0")
        else:
            steps_per_second = int(1.0 / dt)
            min_steps = int(steps_per_second / substeps)
            self._physx_scene_api.GetTimeStepsPerSecondAttr().Set(steps_per_second)

        set_carb_setting(carb.settings.get_settings(), "persistent/simulation/minFrameRate", min_steps)
        return

    def set_physics_scene_settings(
        self,
        enable_ccd: bool = True,
        enable_stablization: bool = True,
        enable_gpu_dynamics: bool = False,
        broadphase_type: str = "MBP",
        solver_type: str = "TGS",
        gravity_z_dir: float = -1.0,
        gravity_magnitude: float = 9.81,
    ):
        # TODO: handle the case where a physics scene is already defined and we need to change values and not create
        stage = get_current_stage()
        carb.log_info(
            "Setting Physics Scene Setting with z gravity value of: {}".format(gravity_z_dir * gravity_magnitude)
        )
        up_axis = UsdGeom.GetStageUpAxis(stage)
        gravity_dir = Gf.Vec3f(0.0)
        gravity_dir[AXES_INDICES[up_axis]] = gravity_z_dir
        if self._physics_scene.GetGravityDirectionAttr().Get() is None:
            self._physics_scene.CreateGravityDirectionAttr(gravity_dir)
        else:
            self._physics_scene.GetGravityDirectionAttr().Set(gravity_dir)

        if self._physics_scene.GetGravityMagnitudeAttr().Get() is None:
            self._physics_scene.CreateGravityMagnitudeAttr(gravity_magnitude)
        else:
            self._physics_scene.GetGravityMagnitudeAttr().Set(gravity_magnitude)

        if self._physx_scene_api.GetEnableCCDAttr().Get() is None:
            self._physx_scene_api.CreateEnableCCDAttr(enable_ccd)
        else:
            self._physx_scene_api.GetEnableCCDAttr().Set(enable_ccd)

        if self._physx_scene_api.GetEnableStabilizationAttr().Get() is None:
            self._physx_scene_api.CreateEnableStabilizationAttr(enable_stablization)
        else:
            self._physx_scene_api.GetEnableStabilizationAttr().Set(enable_stablization)

        if self._physx_scene_api.GetEnableGPUDynamicsAttr().Get() is None:
            self._physx_scene_api.CreateEnableGPUDynamicsAttr(enable_gpu_dynamics)
        else:
            self._physx_scene_api.GetEnableGPUDynamicsAttr().Set(enable_gpu_dynamics)

        if self._physx_scene_api.GetBroadphaseTypeAttr().Get() is None:
            self._physx_scene_api.CreateBroadphaseTypeAttr(broadphase_type)
        else:
            self._physx_scene_api.GetBroadphaseTypeAttr().Set(broadphase_type)

        if self._physx_scene_api.GetSolverTypeAttr().Get() is None:
            self._physx_scene_api.CreateSolverTypeAttr(solver_type)
        else:
            self._physx_scene_api.GetSolverTypeAttr().Set(solver_type)
        return

    def step(self, current_time: float):
        self._physx_interface.update_simulation(elapsedStep=self.get_physics_dt(), currentTime=current_time)
        self._physx_interface.update_transformations(
            updateToFastCache=True, updateToUsd=True, updateVelocitiesToUsd=True, outputVelocitiesLocalSpace=False
        )
        return

    def get_physics_dt(self) -> float:
        physics_hz = self._physx_scene_api.GetTimeStepsPerSecondAttr().Get()
        if physics_hz == 0:
            return 0.0
        else:
            return 1.0 / physics_hz
