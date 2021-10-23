# Copyright (c) 2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#

# omniverse
import asyncio
import carb
import builtins
import omni.kit.app
from pxr import UsdGeom, Gf, Usd, Sdf, UsdPhysics, PhysxSchema
from omni.isaac.core.utils.carb import set_carb_setting
from omni.isaac.core.utils.stage import (
    create_new_stage,
    create_new_stage_async,
    get_current_stage,
    traverse_stage,
    set_stage_units,
)
from omni.isaac.core.utils.constants import AXES_INDICES


class SimulationContext:
    _instance = None
    _sim_context_initialized = False

    def __init__(self, physics_dt: float = None, stage_units_in_meters: float = None):
        if SimulationContext._sim_context_initialized:
            return
        SimulationContext._sim_context_initialized = True
        self._app = omni.kit.app.get_app_interface()
        # Acquire the running application interface
        self._framework = carb.get_framework()
        self._timeline = omni.timeline.get_timeline_interface()
        self._timeline.set_auto_update(True)
        self._physics_callback_functions = dict()
        self._stage_callback_functions = dict()
        self._timeline_callback_functions = dict()
        self._editor_callback_functions = dict()
        if builtins.ISAAC_LAUNCHED_FROM_TERMINAL is False:
            self.init_stage(physics_dt=physics_dt, stage_units_in_meters=stage_units_in_meters)
            self._setup_default_callback_fns()
        else:
            asyncio.ensure_future(
                self.init_stage_async(physics_dt=physics_dt, stage_units_in_meters=stage_units_in_meters)
            )
        self._stage_open_callback = (
            omni.usd.get_context().get_stage_event_stream().create_subscription_to_pop(self._stage_open_callback_fn)
        )
        return

    def __new__(cls, physics_dt: float = 1.0 / 60.0, stage_units_in_meters: float = 1.0):
        if SimulationContext._instance is None:
            SimulationContext._instance = object.__new__(cls)
        else:
            carb.log_warn("Simulation Context is defined already, returning the previously defined one")
        return SimulationContext._instance

    async def init_simulation_context_async(self):
        await omni.kit.app.get_app().next_update_async()
        self._setup_default_callback_fns()
        await omni.kit.app.get_app().next_update_async()
        return

    @classmethod
    def instance(cls):
        return SimulationContext._instance

    @classmethod
    def clear_instance(cls):
        SimulationContext._instance = None
        SimulationContext._sim_context_initialized = False
        return

    def __del__(self):
        """Destructor for object."""
        SimulationContext._instance = None
        SimulationContext._sim_context_initialized = False
        self.clear_all_callbacks()
        self._stage_open_callback = None
        return

    @property
    def app(self) -> omni.kit.app.IApp:
        """Returns: The Omniverse Toolkit application."""
        return self._app

    @property
    def current_time_step_index(self) -> int:
        return self._number_of_steps

    @property
    def current_time(self):
        return self._current_time

    @property
    def stage(self) -> Usd.Stage:
        """Returns: The current USD stage."""
        return get_current_stage()

    def get_physics_dt(self) -> float:
        if self.stage is None:
            raise Exception("There is no stage currently opened")
        return self._physics_scene.get_physics_dt()

    def is_playing(self) -> bool:
        """Returns: True if the simulator is playing."""
        return self._timeline.is_playing()

    def is_stopped(self) -> bool:
        """Returns: True if the simulator is stopped."""
        return self._timeline.is_stopped()

    def _physics_timer_callback_fn(self, step_size):
        self._current_time += step_size
        self._number_of_steps += 1
        return

    def _timeline_timer_callback_fn(self, event):
        if event.type == int(omni.timeline.TimelineEventType.STOP):
            self._current_time = 0
            self._number_of_steps = 0
        return

    def _stage_open_callback_fn(self, event):
        if event.type == int(omni.usd.StageEventType.OPENED):
            self._physics_callback_functions = dict()
            self._stage_callback_functions = dict()
            self._timeline_callback_functions = dict()
            self._editor_callback_functions = dict()
            SimulationContext.clear_instance()
            carb.log_warn(
                "A new stage was opened, World or Simulation Object are invalidated and you would need to initialize them again before using them."
            )
            self._stage_open_callback = None

        return

    def _setup_default_callback_fns(self):
        self._physics_timer_callback = self._physics_scene._physx_interface.subscribe_physics_step_events(
            self._physics_timer_callback_fn
        )
        self._event_timer_callback = self._timeline.get_timeline_event_stream().create_subscription_to_pop(
            self._timeline_timer_callback_fn
        )
        self._physics_callback_functions = dict()
        self._stage_callback_functions = dict()
        self._timeline_callback_functions = dict()
        self._editor_callback_functions = dict()
        self._timeline = omni.timeline.get_timeline_interface()
        self._timeline.set_auto_update(True)
        self._number_of_steps = 0
        self._current_time = 0
        return

    def start_simulation(self):
        if self.stage is None:
            raise Exception("There is no stage currently opened, init_stage needed before calling this func")
        self._physics_scene._physx_interface.start_simulation()
        self._physics_scene._physx_interface.force_load_physics_from_usd()
        return

    async def play_async(self):
        """Pauses the editor physics simulation"""
        self._timeline.play()
        await omni.kit.app.get_app().next_update_async()
        return

    def play(self) -> None:
        self._timeline.play()
        if builtins.ISAAC_LAUNCHED_FROM_TERMINAL is False:
            self.step(render=True)
        return

    async def pause_async(self):
        """Pauses the editor physics simulation"""
        self._timeline.pause()
        await omni.kit.app.get_app().next_update_async()
        return

    def pause(self):
        """Pauses the editor physics simulation"""
        self._timeline.pause()
        if builtins.ISAAC_LAUNCHED_FROM_TERMINAL is False:
            self.render()
        return

    async def stop_async(self):
        """Pauses the editor physics simulation"""
        self._timeline.stop()
        await omni.kit.app.get_app().next_update_async()
        return

    def stop(self):
        """Stops the editor physics simulation"""
        self._timeline.stop()
        if builtins.ISAAC_LAUNCHED_FROM_TERMINAL is False:
            self.render()
        return

    def init_stage(self, physics_dt=None, stage_units_in_meters=None) -> Usd.Stage:
        if get_current_stage() is None:
            create_new_stage()
            self.render()
            if stage_units_in_meters is None:
                set_stage_units(stage_units_in_meters=1.0)
                self.render()
        if stage_units_in_meters is not None:
            set_stage_units(stage_units_in_meters)
            self.render()
        self._physics_scene = PhysicsScene(physics_dt=physics_dt)
        self.render()
        return self.stage

    async def init_stage_async(self, physics_dt=None, stage_units_in_meters=None) -> Usd.Stage:
        if get_current_stage() is None:
            await create_new_stage_async()
            if stage_units_in_meters is None:
                set_stage_units(stage_units_in_meters=1.0)
                await omni.kit.app.get_app().next_update_async()
        if stage_units_in_meters is not None:
            set_stage_units(stage_units_in_meters)
            await omni.kit.app.get_app().next_update_async()
        self._physics_scene = PhysicsScene(physics_dt=physics_dt)
        await omni.kit.app.get_app().next_update_async()
        return self.stage

    def set_physics_dt(self, dt: float = 1.0 / 60.0, substeps: int = 1):
        if self.stage is None:
            raise Exception("There is no stage currently opened, init_stage needed before calling this func")
        self._physics_scene.set_physics_dt(dt, substeps)
        return

    def step(self, render=True):
        if self.stage is None:
            raise Exception("There is no stage currently opened, init_stage needed before calling this func")
        if render:
            self._app.update()
        else:
            if self.is_playing():
                self._physics_scene.step(current_time=self.current_time)
        return

    def render(self):
        set_carb_setting(carb.settings.get_settings(), "/app/player/playSimulations", False)
        self._app.update()
        set_carb_setting(carb.settings.get_settings(), "/app/player/playSimulations", True)
        return

    def add_physics_callback(self, callback_name, callback_fn):
        if self.stage is None:
            raise Exception("There is no stage currently opened, init_stage needed before calling this func")
        if callback_name in self._physics_callback_functions:
            carb.log_error(f"Physics callback `{callback_name}` already exists")
            return
        self._physics_callback_functions[
            callback_name
        ] = self._physics_scene._physx_interface.subscribe_physics_step_events(callback_fn)
        return

    def remove_physics_callback(self, callback_name):
        if callback_name in self._physics_callback_functions:
            del self._physics_callback_functions[callback_name]
        else:
            carb.log_error(f"Physics callback `{callback_name}` doesn't exist")
        return

    def physics_callback_exists(self, callback_name):
        if callback_name in self._physics_callback_functions:
            return True
        else:
            return False

    def clear_physics_callbacks(self):
        self._physics_callback_functions = dict()
        return

    def add_stage_callback(self, callback_name, callback_fn):
        if callback_name in self._stage_callback_functions:
            carb.log_error(f"Stage callback `{callback_name}` already exists")
            return
        self._stage_callback_functions[callback_name] = (
            omni.usd.get_context().get_stage_event_stream().create_subscription_to_pop(callback_fn)
        )
        return

    def remove_stage_callback(self, callback_name):
        if callback_name in self._stage_callback_functions:
            del self._stage_callback_functions[callback_name]
        else:
            carb.log_error(f"Stage callback `{callback_name}` doesn't exist")
        return

    def stage_callback_exists(self, callback_name):
        if callback_name in self._stage_callback_functions:
            return True
        else:
            return False

    def clear_stage_callbacks(self):
        self._stage_callback_functions = dict()
        return

    def add_timeline_callback(self, callback_name, callback_fn):
        if callback_name in self._timeline_callback_functions:
            carb.log_error(f"Timeline callback `{callback_name}` already exists")
            return
        self._timeline_callback_functions[
            callback_name
        ] = self._timeline.get_timeline_event_stream().create_subscription_to_pop(callback_fn)
        return

    def remove_timeline_callback(self, callback_name):
        if callback_name in self._timeline_callback_functions:
            del self._timeline_callback_functions[callback_name]
        else:
            carb.log_error(f"Timeline callback `{callback_name}` doesn't exist")
        return

    def timeline_callback_exists(self, callback_name):
        if callback_name in self._timeline_callback_functions:
            return True
        else:
            return False

    def clear_timeline_callbacks(self):
        self._timeline_callback_functions = dict()
        return

    def add_editor_callback(self, callback_name, callback_fn):
        if callback_name in self._editor_callback_functions:
            carb.log_error(f"Editor callback `{callback_name}` already exists")
            return
            # TODO: should we raise exception?
        self._editor_callback_functions[callback_name] = self.app.get_update_event_stream().create_subscription_to_pop(
            callback_fn
        )
        return

    def remove_editor_callback(self, callback_name):
        if callback_name in self._editor_callback_functions:
            del self._editor_callback_functions[callback_name]
        else:
            carb.log_error(f"Editor callback `{callback_name}` doesn't exist")
        return

    def editor_callback_exists(self, callback_name):
        if callback_name in self._editor_callback_functions:
            return True
        else:
            return False

    def clear_editor_callbacks(self):
        self._editor_callback_functions = dict()
        return

    def clear_all_callbacks(self):
        self._physics_callback_functions = dict()
        self._stage_callback_functions = dict()
        self._timeline_callback_functions = dict()
        self._editor_callback_functions = dict()
        return


class PhysicsScene:
    def __init__(self, physics_dt=None, prim_path: str = "/World/physicsScene"):
        stage = get_current_stage()
        self._path = prim_path
        if not Sdf.Path(self._path).IsAbsolutePath():
            raise Exception(f"Input prim path is not absolute: {self._path}")
        current_physics_prim = self.get_current_physics_scene_prim()
        self._physx_scene_api = None
        if builtins.ISAAC_LAUNCHED_FROM_TERMINAL is False:
            # TODO check if this import succeeds?
            import omni.kit.loop._loop as omni_loop

            self._loop_runner = omni_loop.acquire_loop_interface()
        else:
            self._loop_runner = None
        if current_physics_prim is None:
            # creating a new physics scene
            prim = stage.GetPrimAtPath(prim_path)
            if prim.IsValid():
                raise Exception(f"A non physics scene prim already exists at: {self._path}")
            self.create_new_physics_scene(prim_path=prim_path)
            if physics_dt is None:
                self.set_physics_dt(dt=1.0 / 60.0)
        else:
            carb.log_info(
                f"Physics Scene at path `{current_physics_prim.GetPath().pathString}` is already defined - reusing it"
            )
            self._physx_scene_api = PhysxSchema.PhysxSceneAPI(current_physics_prim)

        self._physx_interface = omni.physx.acquire_physx_interface()
        # TODO: should we always set these settings? even if a physics scene is defined?
        self.set_physics_scene_settings()
        if physics_dt is not None:
            self.set_physics_dt(dt=physics_dt)
        return

    def __del__(self):
        """Destructor for object."""
        return

    def get_current_physics_scene_prim(self):
        if get_current_stage() is None:
            raise Exception("There is no stage currently opened, init_stage needed before calling this func")
        for prim in traverse_stage():
            if prim.HasAPI(PhysxSchema.PhysxSceneAPI):
                return prim
        return None

    def create_new_physics_scene(self, prim_path):
        if get_current_stage() is None:
            raise Exception("There is no stage currently opened, init_stage needed before calling this func")
        stage = get_current_stage()
        meters_per_unit = UsdGeom.GetStageMetersPerUnit(stage)
        up_axis = UsdGeom.GetStageUpAxis(stage)
        gravity_dir = Gf.Vec3f(0.0)
        gravity_dir[AXES_INDICES[up_axis]] = -1.0
        carb.log_info(f"Defining a new Physics Scene at path `{prim_path}`")
        scene = UsdPhysics.Scene.Define(stage, prim_path)
        prim = stage.GetPrimAtPath(prim_path)
        self._physx_scene_api = PhysxSchema.PhysxSceneAPI.Apply(prim)
        scene.CreateGravityDirectionAttr().Set(gravity_dir)
        scene.CreateGravityMagnitudeAttr().Set(9.81 / meters_per_unit)
        return

    def set_physics_dt(self, dt: float = 1.0 / 60.0, substeps: int = 1):
        """Specify the physics step size to use when simulating,

        Note:
            A physics scene has to be in the stage for this to do anything.

        Keyword Arguments:
            dt {float} -- The physics time-step. (default: {1.0/60.0})
            substeps {int} -- The number of physics time-steps to simulate. (default: {1})
        """
        # if no stage or no change in physics timestep, exit.
        if get_current_stage() is None:
            return
        # if physics substeps is not valid, make default = 1.
        if substeps is None or substeps <= 1:
            substeps = 1
        if dt == 0:
            self._physx_scene_api.GetTimeStepsPerSecondAttr().Set(0)
            min_steps = 0
        else:
            steps_per_second = int(1.0 / dt)
            min_steps = int(steps_per_second / substeps)
            self._physx_scene_api.GetTimeStepsPerSecondAttr().Set(steps_per_second)
        # TODO Is there a better way to do this or atleast reset this to the original values on close
        if builtins.ISAAC_LAUNCHED_FROM_TERMINAL is False:
            set_carb_setting(carb.settings.get_settings(), "/app/runLoops/main/rateLimitEnabled", True)
            set_carb_setting(carb.settings.get_settings(), "persistent/simulation/minFrameRate", min_steps)
            set_carb_setting(carb.settings.get_settings(), "/app/runLoops/main/rateLimitFrequency", min_steps)
            if self._loop_runner is not None:
                self._loop_runner.set_runner_dt(dt)
        return

    def set_physics_scene_settings(
        self,
        enable_ccd: bool = True,
        enable_stablization: bool = True,
        enable_gpu_dynamics: bool = False,
        broadphase_type: str = "MBP",
        solver_type: str = "TGS",
    ):
        # TODO: handle the case where a physics scene is already defined and we need to change values and not create
        if get_current_stage() is None:
            raise Exception("There is no stage currently opened, init_stage needed before calling this func")
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

    def step(self, current_time):
        if get_current_stage() is None:
            raise Exception("There is no stage currently opened, init_stage needed before calling this func")
        self._physx_interface.update_simulation(elapsedStep=self.get_physics_dt(), currentTime=current_time)
        self._physx_interface.update_transformations(
            updateToFastCache=True, updateToUsd=True, updateVelocitiesToUsd=True, outputVelocitiesLocalSpace=False
        )
        return

    def get_physics_dt(self):
        if get_current_stage() is None:
            raise Exception("There is no stage currently opened, init_stage needed before calling this func")
        return 1.0 / self._physx_scene_api.GetTimeStepsPerSecondAttr().Get()
