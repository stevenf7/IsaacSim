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
from typing import Optional, Tuple, List
from pxr import Usd, UsdGeom, Gf, Sdf, UsdPhysics, PhysxSchema
from omni.isaac.core.utils.constants import AXES_INDICES
from omni.isaac.core.utils.prims import get_prim_at_path, get_prim_path, is_prim_path_valid
from omni.isaac.core.utils.carb import set_carb_setting
from omni.isaac.core.utils.stage import get_current_stage, get_stage_units, traverse_stage


class PhysicsContext(object):
    """Provides high level functions to deal with a physics scene and its settings. This will create a 
           a PhysicsScene prim at the specified prim path in case there is no PhysicsScene present in the current
           stage. 
           If there is a PhysicsScene present, it will discard the prim_path specified and sets the
           default settings on the current PhysicsScene found.

        Args:
            physics_dt (Optional[float], optional): specifies the physics_dt of the simulation. Defaults to None.
            prim_path (Optional[str], optional): specifies the prim path to create a PhysicsScene at, 
                                                 only in the case where no PhysicsScene already defined. 
                                                 Defaults to "/World/physicsScene".

        Raises:
            Exception: If prim_path is not absolute.
            Exception: if prim_path already exists and its type is not a PhysicsScene.
        """

    def __init__(self, physics_dt: Optional[float] = None, prim_path: str = "/World/physicsScene") -> None:
        self._prim_path = prim_path
        if not Sdf.Path(self._prim_path).IsAbsolutePath():
            raise Exception(f"Input prim path is not absolute: {self._path}")
        # check if there is a current physics scene defined already in the scene
        current_physics_prim = self.get_current_physics_scene_prim()
        self._physx_scene_api = None
        if current_physics_prim is None:
            # creating a new physics scene
            if is_prim_path_valid(prim_path):
                raise Exception(f"A non physics scene prim already exists at: {self._prim_path}")
            self._physics_scene = self._create_new_physics_scene(prim_path=prim_path)
            if physics_dt is None:
                self.set_physics_dt(dt=1.0 / 60.0)
        else:
            # already exists a physics scene
            self._prim_path = get_prim_path(current_physics_prim)
            carb.log_info(f"Physics Scene at path `{self._prim_path}` is already defined - reusing it")
            self._physics_scene = UsdPhysics.Scene(current_physics_prim)
            self._physx_scene_api = PhysxSchema.PhysxSceneAPI(current_physics_prim)
        self._physx_interface = omni.physx.acquire_physx_interface()
        meters_per_unit = get_stage_units()
        self.set_gravity(value=-9.81 / meters_per_unit)
        self.enable_ccd(flag=True)
        self.enable_stablization(flag=True)
        self.enable_gpu_dynamics(flag=False)
        self.set_broadphase_type(broadcast_type="MBP")
        self.set_solver_type(solver_type="TGS")
        if physics_dt is not None:
            self.set_physics_dt(dt=physics_dt)
        return

    def __del__(self):
        return

    def get_current_physics_scene_prim(self) -> Optional[Usd.Prim]:
        """Used to return the PhysicsScene prim in stage by traversing the stage.

        Returns:
            Optional[Usd.Prim]: returns a PhysicsScene prim if found in current stage. Otherwise, None.
        """
        for prim in traverse_stage():
            if prim.HasAPI(PhysxSchema.PhysxSceneAPI):
                return prim
        return None

    def _create_new_physics_scene(self, prim_path: str):
        carb.log_info(f"Defining a new Physics Scene at path `{prim_path}`")
        stage = get_current_stage()
        scene = UsdPhysics.Scene.Define(stage, prim_path)
        self._physx_scene_api = PhysxSchema.PhysxSceneAPI.Apply(get_prim_at_path(prim_path))
        return scene

    def set_physics_dt(self, dt: float = 1.0 / 60.0, substeps: int = 1) -> None:
        """Sets the physics dt on the PhysicsScene

        Args:
            dt (float, optional): physics dt. Defaults to 1.0/60.0.
            substeps (int, optional): number of physics steps to run for before rendering a frame. Defaults to 1.

        Raises:
            Exception: If the prim path registered in context doesn't correspond to a valid prim path currently.
            ValueError: Physics dt must be a >= 0.
            ValueError: Physics dt must be a <= 1.0.
        """
        if not is_prim_path_valid(self._prim_path):
            raise Exception("The Physics Context's physics scene path is invalid, you need to reinit Physics Context")
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

    def get_physics_dt(self) -> float:
        """Returns the current physics dt.

        Raises:
            Exception: If the prim path registered in context doesn't correspond to a valid prim path currently.

        Returns:
            float: physics dt.
        """
        if not is_prim_path_valid(self._prim_path):
            raise Exception("The Physics Context's physics scene path is invalid, you need to reinit Physics Context")
        physics_hz = self._physx_scene_api.GetTimeStepsPerSecondAttr().Get()
        if physics_hz == 0:
            return 0.0
        else:
            return 1.0 / physics_hz

    def enable_ccd(self, flag: bool) -> None:
        """Enables a second broad phase after integration that makes it possible to prevent objects from tunneling
           through each other.

        Args:
            flag (bool): enables or diables ccd on the PhysicsScene

        Raises:
            Exception: If the prim path registered in context doesn't correspond to a valid prim path currently.
        """
        if not is_prim_path_valid(self._prim_path):
            raise Exception("The Physics Context's physics scene path is invalid, you need to reinit Physics Context")
        if self._physx_scene_api.GetEnableCCDAttr().Get() is None:
            self._physx_scene_api.CreateEnableCCDAttr(flag)
        else:
            self._physx_scene_api.GetEnableCCDAttr().Set(flag)
        return

    def is_ccd_enabled(self) -> bool:
        """Checks if ccd is enabled.

        Raises:
            Exception: If the prim path registered in context doesn't correspond to a valid prim path currently.

        Returns:
            bool: True if ccd is enabled, otherwise False.
        """
        if not is_prim_path_valid(self._prim_path):
            raise Exception("The Physics Context's physics scene path is invalid, you need to reinit Physics Context")
        return self._physx_scene_api.GetEnableCCDAttr().Get()

    def enable_stablization(self, flag: bool) -> None:
        """Enables additional stabilization pass in the solver.

        Args:
            flag (bool): enables or diables stabilization on the PhysicsScene

        Raises:
            Exception: If the prim path registered in context doesn't correspond to a valid prim path currently.
        """
        if not is_prim_path_valid(self._prim_path):
            raise Exception("The Physics Context's physics scene path is invalid, you need to reinit Physics Context")
        if self._physx_scene_api.GetEnableStabilizationAttr().Get() is None:
            self._physx_scene_api.CreateEnableStabilizationAttr(flag)
        else:
            self._physx_scene_api.GetEnableStabilizationAttr().Set(flag)
        return

    def is_stablization_enabled(self) -> bool:
        """Checks if stabilization is enabled.

        Raises:
            Exception: If the prim path registered in context doesn't correspond to a valid prim path currently.

        Returns:
            bool: True if stabilization is enabled, otherwise False.
        """
        if not is_prim_path_valid(self._prim_path):
            raise Exception("The Physics Context's physics scene path is invalid, you need to reinit Physics Context")
        return self._physx_scene_api.GetEnableStabilizationAttr().Get()

    def enable_gpu_dynamics(self, flag: bool) -> None:
        """Enables gpu dynamics pipeline, required for deformables for instance.

        Args:
            flag (bool): enables or diables gpu dynamics on the PhysicsScene

        Raises:
            Exception: If the prim path registered in context doesn't correspond to a valid prim path currently.
        """
        if not is_prim_path_valid(self._prim_path):
            raise Exception("The Physics Context's physics scene path is invalid, you need to reinit Physics Context")
        if self._physx_scene_api.GetEnableGPUDynamicsAttr().Get() is None:
            self._physx_scene_api.CreateEnableGPUDynamicsAttr(flag)
        else:
            self._physx_scene_api.GetEnableGPUDynamicsAttr().Set(flag)
        return

    def is_gpu_dynamics_enabled(self) -> bool:
        """Checks if Gpu Dynamics is enabled.

        Raises:
            Exception: If the prim path registered in context doesn't correspond to a valid prim path currently.

        Returns:
            bool: True if Gpu Dynamics is enabled, otherwise False.
        """
        if not is_prim_path_valid(self._prim_path):
            raise Exception("The Physics Context's physics scene path is invalid, you need to reinit Physics Context")
        return self._physx_scene_api.GetEnableGPUDynamicsAttr().Get()

    def set_broadphase_type(self, broadcast_type: str) -> None:
        """Broadcast phase algorithm used in simulation.

        Args:
            broadcast_type (str): type of broadcasting to be used, can be "MBP"

        Raises:
            Exception: If the prim path registered in context doesn't correspond to a valid prim path currently.
        """
        if not is_prim_path_valid(self._prim_path):
            raise Exception("The Physics Context's physics scene path is invalid, you need to reinit Physics Context")
        if self._physx_scene_api.GetBroadphaseTypeAttr().Get() is None:
            self._physx_scene_api.CreateBroadphaseTypeAttr(broadcast_type)
        else:
            self._physx_scene_api.GetBroadphaseTypeAttr().Set(broadcast_type)
        return

    def get_broadphase_type(self) -> str:
        """Gets current broadcast phase algorithm type.

        Raises:
            Exception: If the prim path registered in context doesn't correspond to a valid prim path currently.

        Returns:
            str: Broadcast phase algorithm used.
        """
        if not is_prim_path_valid(self._prim_path):
            raise Exception("The Physics Context's physics scene path is invalid, you need to reinit Physics Context")
        return self._physx_scene_api.GetBroadphaseTypeAttr().Get()

    def set_solver_type(self, solver_type: str) -> None:
        """solver used for simulation.

        Args:
            solver_type (str): can be "TGS" or "PGS". for references look at..

        Raises:
            Exception: If the prim path registered in context doesn't correspond to a valid prim path currently.
        """
        if not is_prim_path_valid(self._prim_path):
            raise Exception("The Physics Context's physics scene path is invalid, you need to reinit Physics Context")
        if self._physx_scene_api.GetSolverTypeAttr().Get() is None:
            self._physx_scene_api.CreateSolverTypeAttr(solver_type)
        else:
            self._physx_scene_api.GetSolverTypeAttr().Set(solver_type)
        return

    def get_solver_type(self) -> str:
        """Gets current solver type.

        Raises:
            Exception: If the prim path registered in context doesn't correspond to a valid prim path currently.

        Returns:
            str: solver used for simulation.
        """
        if not is_prim_path_valid(self._prim_path):
            raise Exception("The Physics Context's physics scene path is invalid, you need to reinit Physics Context")
        return self._physx_scene_api.GetSolverTypeAttr().Get()

    def set_gravity(self, value: float) -> None:
        """sets the gravity direction and magnitude.

        Args:
            value (float): gravity value to be used in simulation.

        Raises:
            Exception: If the prim path registered in context doesn't correspond to a valid prim path currently.
        """
        if not is_prim_path_valid(self._prim_path):
            raise Exception("The Physics Context's physics scene path is invalid, you need to reinit Physics Context")
        if value < 0:
            z_dir = -1
            magnitude = value * -1
        else:
            z_dir = 1
            magnitude = value
        up_axis = UsdGeom.GetStageUpAxis(get_current_stage())
        gravity_dir = Gf.Vec3f(0.0)
        gravity_dir[AXES_INDICES[up_axis]] = z_dir
        if self._physics_scene.GetGravityDirectionAttr().Get() is None:
            self._physics_scene.CreateGravityDirectionAttr(gravity_dir)
        else:
            self._physics_scene.GetGravityDirectionAttr().Set(gravity_dir)

        if self._physics_scene.GetGravityMagnitudeAttr().Get() is None:
            self._physics_scene.CreateGravityMagnitudeAttr(magnitude)
        else:
            self._physics_scene.GetGravityMagnitudeAttr().Set(magnitude)
        return

    def get_gravity(self) -> Tuple[List, float]:
        """Gets current gravity.

        Raises:
            Exception: If the prim path registered in context doesn't correspond to a valid prim path currently.

        Returns:
            Tuple[list, float]: returns a tuple, first element corresponds to the gravity direction vector and second element is the magnitude.
        """
        if not is_prim_path_valid(self._prim_path):
            raise Exception("The Physics Context's physics scene path is invalid, you need to reinit Physics Context")
        return (
            list(self._physics_scene.GetGravityDirectionAttr().Get()),
            self._physics_scene.GetGravityMagnitudeAttr().Get(),
        )

    def _step(self, current_time: float) -> None:
        self._physx_interface.update_simulation(elapsedStep=self.get_physics_dt(), currentTime=current_time)
        self._physx_interface.update_transformations(
            updateToFastCache=True, updateToUsd=True, updateVelocitiesToUsd=True, outputVelocitiesLocalSpace=False
        )
        return
