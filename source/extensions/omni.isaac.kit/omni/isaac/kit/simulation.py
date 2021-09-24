# Copyright (c) 2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#

# python
import time
import asyncio
import numpy as np

# omniverse
import carb
from omni.isaac.kit import global_vars
import omni.kit.app
from pxr import UsdGeom, Gf, Usd, Sdf, UsdPhysics, PhysxSchema
from omni.isaac.kit.utils import set_carb_setting
from omni.isaac.kit.constants import AXES_INDICES


class SimulationContext:
    def __init__(self, physics_dt: float = 1.0 / 60.0, stage_units_in_meters: float = 1.0):
        # Only import custom loop runner if we create this object
        # TODO: customization for the physics
        self.set_stage_units(stage_units_in_meters)
        self._physics_scene = PhysicsScene(physics_dt=physics_dt)
        # Acquire the running application interface
        self._app = omni.kit.app.get_app_interface()
        # Acquire interfaces to extensions from Omniverse Toolkit
        self._framework = carb.get_framework()
        self._timeline = omni.timeline.get_timeline_interface()
        self.set_camera_view()
        # Turn auto-update on for timeline
        self._timeline.set_auto_update(True)
        self._physics_callback_functions = dict()
        self._physics_timer_callback = self._physics_scene._physx_interface.subscribe_physics_step_events(
            self._physics_timer_callback_fn
        )
        self._event_timer_callback = self._timeline.get_timeline_event_stream().create_subscription_to_pop(
            self._timeline_timer_callback_fn
        )
        self._stage_callback_functions = dict()
        self._timeline_callback_functions = dict()
        self._editor_callback_functions = dict()
        self._number_of_steps = 0
        self._current_async_task = None
        self._extension_manager = omni.kit.app.get_app().get_extension_manager()
        self._async_tasks = []
        self._current_time = 0
        return

    def __del__(self):
        """Destructor for object."""
        self._physics_callback_functions = dict()
        self._stage_callback_functions = dict()
        self._timeline_callback_functions = dict()
        self._editor_callback_functions = dict()
        pass

    @property
    def app(self) -> omni.kit.app.IApp:
        """Returns: The Omniverse Toolkit application."""
        return self._app

    @property
    def time_step_index(self) -> int:
        return self._number_of_steps

    @property
    def time(self):
        return self._current_time

    @property
    def stage(self) -> Usd.Stage:
        """Returns: The current USD stage."""
        return omni.usd.get_context().get_stage()

    @property
    def is_playing(self) -> bool:
        """Returns: True if the simulator is playing."""
        return self._timeline.is_playing()

    @property
    def is_stopped(self) -> bool:
        """Returns: True if the simulator is stopped."""
        return self._timeline.is_stopped()

    # TODO: check why you need a simulate before and after

    def _physics_timer_callback_fn(self, step_size):
        self._current_time += step_size
        self._number_of_steps += 1
        return

    def _timeline_timer_callback_fn(self, event):
        if event.type == int(omni.timeline.TimelineEventType.STOP):
            self._current_time = 0
            self._number_of_steps = 0
        return

    def start_simulation(self):
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
        self._app.update()
        return

    def set_camera_view(self, eye=None, target=None, vel=0.05):
        """[summary]

        Args:
            eye (list, optional): [description]. Defaults to [1.5, 1.5, 1.5].
            target (list, optional): [description]. Defaults to [0.01, 0.01, 0.01].
            vel (float, optional): [description]. Defaults to 0.05.
        """
        meters_per_unit = UsdGeom.GetStageMetersPerUnit(self.stage)
        if eye is None:
            eye = np.array([1.5, 1.5, 1.5]) / meters_per_unit
        if target is None:
            target = np.array([0.01, 0.01, 0.01]) / meters_per_unit
        vel = vel / meters_per_unit
        self._viewport = omni.kit.viewport.get_default_viewport_window()
        self._viewport.set_camera_position("/OmniverseKit_Persp", eye[0], eye[1], eye[2], True)
        self._viewport.set_camera_target("/OmniverseKit_Persp", target[0], target[1], target[2], True)
        self._viewport.set_camera_move_velocity(vel)
        return

    async def pause_async(self):
        """Pauses the editor physics simulation"""
        self._timeline.pause()
        await omni.kit.app.get_app().next_update_async()
        return

    def pause(self):
        """Pauses the editor physics simulation"""
        self._timeline.pause()
        self._app.update()
        return

    async def stop_async(self):
        """Pauses the editor physics simulation"""
        self._timeline.stop()
        await omni.kit.app.get_app().next_update_async()
        return

    def stop(self):
        """Stops the editor physics simulation"""
        self._timeline.stop()
        self._app.update()
        return

    async def create_new_stage_async(self, stage_units_in_meters: float = 1.0) -> Usd.Stage:
        await omni.usd.get_context().new_stage_async()
        await omni.kit.app.get_app().next_update_async()
        self.set_stage_units(stage_units_in_meters)
        self._physics_scene = PhysicsScene(self._physics_scene._current_physics_dt)
        self._physics_callback_functions = dict()
        self._physics_timer_callback = self._physics_scene._physx_interface.subscribe_physics_step_events(
            self._physics_timer_callback_fn
        )
        self._event_timer_callback = self._timeline.get_timeline_event_stream().create_subscription_to_pop(
            self._timeline_timer_callback_fn
        )
        await omni.kit.app.get_app().next_update_async()
        self._timeline = omni.timeline.get_timeline_interface()
        # Turn auto-update on for timeline
        self._timeline.set_auto_update(True)
        self.set_camera_view()
        return

    def create_new_stage(self, stage_units_in_meters: float = 1.0) -> Usd.Stage:
        # Create a blank new stage
        # This sleep prevents a deadlock in certain cases.
        new_stage_task = asyncio.ensure_future(omni.usd.get_context().new_stage_async())
        while not new_stage_task.done():
            time.sleep(0.001)
            self._app.update()
        # Update the app
        # TODO: add logging
        self._app.update()
        self.set_stage_units(stage_units_in_meters)
        self._physics_scene = PhysicsScene(self._physics_scene._current_physics_dt)
        self._physics_callback_functions = dict()
        self._physics_timer_callback = self._physics_scene._physx_interface.subscribe_physics_step_events(
            self._physics_timer_callback_fn
        )
        self._event_timer_callback = self._timeline.get_timeline_event_stream().create_subscription_to_pop(
            self._timeline_timer_callback_fn
        )
        self.set_camera_view()
        return self.stage

    def add_usd_reference(self, usd_path, prim_path) -> Usd.Prim:
        prim = self.stage.DefinePrim(prim_path, "Xform")
        prim.GetReferences().AddReference(usd_path)
        return prim

    def set_physics_dt(self, dt: float = 1.0 / 60.0, substeps: int = 1):
        self._physics_scene.set_physics_dt(dt, substeps)
        return

    def step(self, render=True):
        if render:
            self._app.update()
        else:
            self._physics_scene.step(current_time=self.time)
        return

    def render(self):
        set_carb_setting(carb.settings.get_settings(), "/app/player/playSimulations", False)
        self._app.update()
        set_carb_setting(carb.settings.get_settings(), "/app/player/playSimulations", True)

    def add_physics_callback(self, callback_name, callback_fn):
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

    def clear_editor_callbacks(self):
        self._editor_callback_functions = dict()
        return

    def set_stage_units(self, stage_units_in_meters):
        UsdGeom.SetStageMetersPerUnit(self.stage, stage_units_in_meters)
        return

    def get_extension_id(self, extension_name: str) -> str:
        """Get extension id for a loaded extension
            Args:
                extension_name (str): name of the extension

            Returns:
                str: Full extension id
        """
        return self._extension_manager.get_enabled_extension_id(extension_name)

    def get_extension_path(self, ext_id: str) -> str:
        """Get extension path for a loaded extension
            Args:
                extension_name (str): name of the extension

            Returns:
                str: Path to loaded extension root directory
        """
        return self._extension_manager.get_extension_path(ext_id)

    def enable_extension(self, extension_name: str) -> bool:
        """Load an extension
            Args:
                extension_name (str): name of the extension

            Returns:
                bool: True if extension could be loaded, False otherwise
        """
        return self._extension_manager.set_extension_enabled_immediate(extension_name, True)


class PhysicsScene:
    def __init__(self, physics_dt, path: str = "/World/physicsScene"):
        self._stage = omni.usd.get_context().get_stage()
        self._path = path
        if not Sdf.Path(self._path).IsAbsolutePath():
            raise ValueError(f"Input prim path is not absolute: {self._path}")
        # check if path pre-exists
        prim = self._stage.GetPrimAtPath(path)
        # extract parameters from stage configuration
        meters_per_unit = UsdGeom.GetStageMetersPerUnit(self._stage)
        up_axis = UsdGeom.GetStageUpAxis(self._stage)
        # TODO: add logging
        # define gravity vector
        gravity_dir = Gf.Vec3f(0.0)
        gravity_dir[AXES_INDICES[up_axis]] = -1.0
        # add the physics scene
        if prim.IsValid():
            carb.log_info(f"Physics Scene at path `{self._path}` is already defined - reusing it")
            scene = UsdPhysics.Scene(prim)
        else:
            carb.log_info(f"Defining a new Physics Scene at path `{self._path}`")
            scene = UsdPhysics.Scene.Define(self._stage, self._path)
        prim = self._stage.GetPrimAtPath(path)
        if prim.HasAPI(PhysxSchema.PhysxSceneAPI):
            self._physx_scene_api = PhysxSchema.PhysxSceneAPI(prim)
        else:
            self._physx_scene_api = PhysxSchema.PhysxSceneAPI.Apply(prim)
        scene.CreateGravityDirectionAttr().Set(gravity_dir)
        scene.CreateGravityMagnitudeAttr().Set(9.81 / meters_per_unit)
        self._previous_physics_dt = None
        self._current_physics_dt = self._previous_physics_dt
        self._physx_interface = omni.physx.acquire_physx_interface()
        self._timeline = omni.timeline.get_timeline_interface()
        if global_vars.LAUNCHED_FROM_TERMINAL is False:
            # TODO check if this import succeeds?
            import omni.kit.loop._loop as omni_loop

            self._loop_runner = omni_loop.acquire_loop_interface()
        else:
            self._loop_runner = None
        self.set_physics_scene()
        self.set_physics_dt(dt=physics_dt)
        return

    def __del__(self):
        """Destructor for object."""
        pass

    def set_physics_dt(self, dt: float = 1.0 / 60.0, substeps: int = 1):
        """Specify the physics step size to use when simulating,

        Note:
            A physics scene has to be in the stage for this to do anything.

        Keyword Arguments:
            dt {float} -- The physics time-step. (default: {1.0/60.0})
            substeps {int} -- The number of physics time-steps to simulate. (default: {1})
        """
        # if no stage or no change in physics timestep, exit.
        if self._stage is None or dt == self._previous_physics_dt:
            return
        # if physics substeps is not valid, make default = 1.
        if substeps is None or substeps <= 1:
            substeps = 1
        # copy arguments to instance.
        self._previous_physics_dt = self._current_physics_dt
        self._current_physics_dt = dt
        steps_per_second = int(1.0 / dt)
        min_steps = int(steps_per_second / substeps)
        # set the steps per second, i.e. physics simulation frequency.
        self._physx_scene_api.GetTimeStepsPerSecondAttr().Set(steps_per_second)
        # set the min frame rate, i.e. frequency of substeps.
        # TODO Is there a better way to do this or atleast reset this to the original values on close
        if global_vars.LAUNCHED_FROM_TERMINAL is False:
            set_carb_setting(carb.settings.get_settings(), "/app/runLoops/main/rateLimitEnabled", True)
            set_carb_setting(carb.settings.get_settings(), "persistent/simulation/minFrameRate", min_steps)
            set_carb_setting(carb.settings.get_settings(), "/app/runLoops/main/rateLimitFrequency", min_steps)
            if self._loop_runner is not None:
                self._loop_runner.set_runner_dt(dt)

    def set_physics_scene(
        self,
        enable_ccd: bool = True,
        enable_stablization: bool = True,
        enable_gpu_dynamics: bool = False,
        broadphase_type: str = "MBP",
        solver_type: str = "TGS",
    ):
        # TODO: handle the case where a physics scene is already defined and we need to change values and not create
        self._physx_scene_api.CreateEnableCCDAttr(enable_ccd)
        self._physx_scene_api.CreateEnableStabilizationAttr(enable_stablization)
        self._physx_scene_api.CreateEnableGPUDynamicsAttr(enable_gpu_dynamics)
        self._physx_scene_api.CreateBroadphaseTypeAttr(broadphase_type)
        self._physx_scene_api.CreateSolverTypeAttr(solver_type)
        return

    def step(self, current_time):
        self._physx_interface.update_simulation(elapsedStep=self._current_physics_dt, currentTime=current_time)
        self._physx_interface.update_transformations(
            updateToFastCache=True, updateToUsd=True, updateVelocitiesToUsd=False, outputVelocitiesLocalSpace=False
        )
        return

    def get_physics_dt(self):
        return self._physx_scene_api.GetTimeStepsPerSecondAttr().Get()
