# Copyright (c) 2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#

# omniverse
import carb
import builtins
import omni.kit.app
from pxr import Usd
from omni.isaac.core.utils.carb import set_carb_setting
from omni.isaac.core.utils.viewports import set_camera_view
from omni.isaac.core.utils.stage import create_new_stage, create_new_stage_async, get_current_stage, set_stage_units
from omni.isaac.core.physics_scene import PhysicsScene
import gc


class SimulationContext:
    _instance = None
    _sim_context_initialized = False

    def __init__(self, physics_dt: float = None, rendering_dt: float = None, stage_units_in_meters: float = 1.0):
        if SimulationContext._sim_context_initialized:
            return
        SimulationContext._sim_context_initialized = True
        self._app = omni.kit.app.get_app_interface()
        # Acquire the running application interface
        self._framework = carb.get_framework()
        self._initial_physics_dt = physics_dt
        self._initial_rendering_dt = rendering_dt
        self._stage_units_in_meters = stage_units_in_meters
        self._timeline = omni.timeline.get_timeline_interface()
        self._timeline.set_auto_update(True)
        self._physics_callback_functions = dict()
        self._stage_callback_functions = dict()
        self._timeline_callback_functions = dict()
        self._render_callback_functions = dict()
        self._loop_runner = None
        self._settings = carb.settings.get_settings()
        self._cached_rate_limit_enabled = self._settings.get_as_bool("/app/runLoops/main/rateLimitEnabled")
        self._cached_rate_limit_frequency = self._settings.get_as_int("/app/runLoops/main/rateLimitFrequency")
        self._cached_min_frame_rate = self._settings.get_as_int("persistent/simulation/minFrameRate")

        if builtins.ISAAC_LAUNCHED_FROM_TERMINAL is False:
            import omni.kit.loop._loop as omni_loop

            self._loop_runner = omni_loop.acquire_loop_interface()

            self.init_stage(
                physics_dt=physics_dt, rendering_dt=rendering_dt, stage_units_in_meters=stage_units_in_meters
            )
            self._setup_default_callback_fns()
            self._stage_open_callback = (
                omni.usd.get_context().get_stage_event_stream().create_subscription_to_pop(self._stage_open_callback_fn)
            )
        return

    def __new__(
        cls, physics_dt: float = 1.0 / 60.0, rendering_dt: float = 1.0 / 60.0, stage_units_in_meters: float = 1.0
    ):
        if SimulationContext._instance is None:
            SimulationContext._instance = object.__new__(cls)
        else:
            carb.log_info("Simulation Context is defined already, returning the previously defined one")
        return SimulationContext._instance

    async def init_simulation_context_async(self):
        await omni.kit.app.get_app().next_update_async()
        await self.init_stage_async(
            physics_dt=self._initial_physics_dt,
            rendering_dt=self._initial_rendering_dt,
            stage_units_in_meters=self._stage_units_in_meters,
        )
        await omni.kit.app.get_app().next_update_async()
        self._stage_open_callback = (
            omni.usd.get_context().get_stage_event_stream().create_subscription_to_pop(self._stage_open_callback_fn)
        )
        await omni.kit.app.get_app().next_update_async()
        self._setup_default_callback_fns()
        await omni.kit.app.get_app().next_update_async()
        set_camera_view()
        return

    @classmethod
    def instance(cls):
        return SimulationContext._instance

    @classmethod
    def clear_instance(cls):
        # We cached the values if the context was initiaized, reset them to the cached values
        if SimulationContext._sim_context_initialized:
            set_carb_setting(
                SimulationContext._instance._settings,
                "/app/runLoops/main/rateLimitEnabled",
                SimulationContext._instance._cached_rate_limit_enabled,
            )
            set_carb_setting(
                SimulationContext._instance._settings,
                "/app/runLoops/main/rateLimitFrequency",
                SimulationContext._instance._cached_rate_limit_frequency,
            )
            set_carb_setting(
                SimulationContext._instance._settings,
                "persistent/simulation/minFrameRate",
                SimulationContext._instance._cached_min_frame_rate,
            )
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

    def get_rendering_dt(self) -> float:
        if self.stage is None:
            raise Exception("There is no stage currently opened")
        return self._rendering_dt

    def get_physics_scene(self) -> PhysicsScene:
        if self.stage is None:
            raise Exception("There is no stage currently opened")
        return self._physics_scene

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
            self._render_callback_functions = dict()
            if SimulationContext._instance is not None:
                SimulationContext._instance.clear_instance()
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
        self._render_callback_functions = dict()
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
            SimulationContext.step(self, render=True)
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

    def init_stage(self, physics_dt=None, rendering_dt=None, stage_units_in_meters=1.0) -> Usd.Stage:
        if get_current_stage() is None:
            create_new_stage()
            self.render()
            if stage_units_in_meters is None:
                set_stage_units(stage_units_in_meters=stage_units_in_meters)
                self.render()
        if stage_units_in_meters is not None:
            set_stage_units(stage_units_in_meters=stage_units_in_meters)
            self.render()
        self._physics_scene = PhysicsScene(physics_dt=physics_dt)
        self.set_simulation_dt(physics_dt=physics_dt, rendering_dt=rendering_dt)
        self.render()
        return self.stage

    async def init_stage_async(self, physics_dt=None, rendering_dt=None, stage_units_in_meters=1.0) -> Usd.Stage:
        if get_current_stage() is None:
            await create_new_stage_async()
            if stage_units_in_meters is None:
                set_stage_units(stage_units_in_meters=stage_units_in_meters)
                await omni.kit.app.get_app().next_update_async()
        if stage_units_in_meters is not None:
            set_stage_units(stage_units_in_meters=stage_units_in_meters)
            await omni.kit.app.get_app().next_update_async()
        self._physics_scene = PhysicsScene(physics_dt=physics_dt)
        self.set_simulation_dt(physics_dt=physics_dt, rendering_dt=rendering_dt)
        await omni.kit.app.get_app().next_update_async()
        return self.stage

    def set_simulation_dt(self, physics_dt: float = 1.0 / 60.0, rendering_dt: float = 1.0 / 60.0) -> None:
        """Specify the physics step and rendering step size to use when stepping and rendering. It is recommended that the two values are divisible. 

        Args:
            physics_dt (float): The physics time-step. (default: 1.0/60.0)
            rendering_dt (float):  The physics time-step. (default: 1.0/60.0)
        """
        if self.stage is None:
            raise Exception("There is no stage currently opened, init_stage needed before calling this func")
        # If the user sets none we assume they don't care and want to use defaults (1.0/60.0)
        if physics_dt is None:
            physics_dt = 1.0 / 60.0
        if rendering_dt is None:
            rendering_dt = 1.0 / 60.0

        if rendering_dt < 0:
            raise ValueError("rendering_dt cannot be <0")
        # if rendering is called the substeps term is used to determine how many physics steps to perform per rendering step
        # is is not used if step(render=False)
        if physics_dt > 0:
            substeps = max(int(rendering_dt / physics_dt), 1)
        else:
            substeps = 1
        self._physics_scene.set_physics_dt(physics_dt, substeps)

        rendering_hz = 0
        if rendering_dt > 0:
            rendering_hz = 1.0 / rendering_dt
        # TODO Is there a better way to do this or atleast reset this to the original values on close
        set_carb_setting(self._settings, "/app/runLoops/main/rateLimitEnabled", True)
        set_carb_setting(self._settings, "/app/runLoops/main/rateLimitFrequency", rendering_hz)
        self._rendering_dt = rendering_dt
        # the custom isaac loop runner is only available when running as a native python script with SimulationApp
        if builtins.ISAAC_LAUNCHED_FROM_TERMINAL is False:
            if self._loop_runner is not None:
                self._loop_runner.set_runner_dt(rendering_dt)
        return

    def step(self, render=True):
        if self.stage is None:
            raise Exception("There is no stage currently opened, init_stage needed before calling this func")
        if render:
            # physics dt is zero, no need to step physics, just render
            if self.get_physics_dt() == 0:
                self.render()
            # rendering dt is zero, but physics is not, call step and then render
            elif self.get_rendering_dt() == 0 and self.get_physics_dt() != 0:
                if self.is_playing():
                    self._physics_scene.step(current_time=self.current_time)
                self.render()
            else:
                self._app.update()
        else:
            if self.is_playing():
                self._physics_scene.step(current_time=self.current_time)
        return

    def render(self):
        set_carb_setting(self._settings, "/app/player/playSimulations", False)
        self._app.update()
        set_carb_setting(self._settings, "/app/player/playSimulations", True)
        return

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

    def physics_callback_exists(self, callback_name):
        if callback_name in self._physics_callback_functions:
            return True
        else:
            return False

    def clear_physics_callbacks(self):
        self._physics_callback_functions = dict()
        # gc.collect()
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

    def add_render_callback(self, callback_name, callback_fn):
        if callback_name in self._render_callback_functions:
            carb.log_error(f"Render callback `{callback_name}` already exists")
            return
            # TODO: should we raise exception?
        self._render_callback_functions[callback_name] = self.app.get_update_event_stream().create_subscription_to_pop(
            callback_fn
        )
        return

    def remove_render_callback(self, callback_name):
        if callback_name in self._render_callback_functions:
            del self._render_callback_functions[callback_name]
        else:
            carb.log_error(f"Editor callback `{callback_name}` doesn't exist")
        return

    def render_callback_exists(self, callback_name):
        if callback_name in self._render_callback_functions:
            return True
        else:
            return False

    def clear_render_callbacks(self):
        self._render_callback_functions = dict()
        return

    def clear_all_callbacks(self):
        self._physics_callback_functions = dict()
        self._stage_callback_functions = dict()
        self._timeline_callback_functions = dict()
        self._render_callback_functions = dict()
        gc.collect()
        return
