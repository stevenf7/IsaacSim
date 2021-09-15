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

# omniverse
import carb
import omni.kit
import omni.kit.app
from pxr import UsdGeom, Gf, Usd, Sdf, UsdPhysics, PhysxSchema
from omni.isaac.kit.utils import set_carb_setting
from omni.isaac.kit.constants import AXES_INDICES
import omni.kit.loop._loop as omni_loop


class SimulationContext:
    def __init__(self, physics_dt: float = 1.0 / 60.0):
        # Only import custom loop runner if we create this object
        # TODO: customization for the physics
        self.set_stage_units(1.0)
        self._physics_scene = PhysicsScene(physics_dt=physics_dt)
        # Acquire the running application interface
        self._app = omni.kit.app.get_app_interface()
        # Acquire interfaces to extensions from Omniverse Toolkit
        self._framework = carb.get_framework()
        self._timeline = omni.timeline.get_timeline_interface()
        self._viewport = omni.kit.viewport.get_default_viewport_window()
        self.set_camera_view()
        # Turn auto-update on for timeline
        self._timeline.set_auto_update(True)
        self._physics_callback_functions = []
        self._stage_callback_functions = []
        self._timeline_callback_functions = []
        self._number_of_steps = 0
        self._current_async_task = None
        self._extension_manager = omni.kit.app.get_app().get_extension_manager()
        self._async_tasks = []
        return

    def __del__(self):
        """Destructor for object."""
        self._physics_callback_functions = []
        self._stage_callback_functions = []
        self._timeline_callback_functions = []
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
        return self._timeline.get_current_time()

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

    def start_simulation(self):
        self.play()
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

    def set_camera_view(self, eye=[2, 2, 2], target=[0, 0, 0], vel=0.05):
        """Set the pose of the default camera "/OmniverseKit_Persp".

        Keyword Arguments:
            eye {list} -- The position of the camera. (default: {[1, 1, 1]})
            lookat {list} -- The target location for the camera. (default: {[0, 0, 0]})
            vel {float} -- The velocity of the camera. (default: {0.05})
        """
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
        self._number_of_steps = 0
        await omni.kit.app.get_app().next_update_async()
        return

    def stop(self):
        """Stops the editor physics simulation"""
        self._timeline.stop()
        self._app.update()
        self._number_of_steps = 0
        return

    async def create_new_stage_async(self) -> Usd.Stage:
        await omni.usd.get_context().new_stage_async()
        await omni.kit.app.get_app().next_update_async()
        self.set_stage_units(1.0)
        self._physics_scene = PhysicsScene(self._physics_scene._current_physics_dt)
        await omni.kit.app.get_app().next_update_async()
        self._timeline = omni.timeline.get_timeline_interface()
        # Turn auto-update on for timeline
        self._timeline.set_auto_update(True)
        self.set_camera_view()
        return

    def create_new_stage(self) -> Usd.Stage:
        # Create a blank new stage
        # This sleep prevents a deadlock in certain cases.
        new_stage_task = asyncio.ensure_future(omni.usd.get_context().new_stage_async())
        while not new_stage_task.done():
            time.sleep(0.001)
            self._app.update()
        # Update the app
        self._app.update()
        self.set_stage_units(1.0)
        self._physics_scene = PhysicsScene(self._physics_scene._current_physics_dt)
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
        curr_time = self._timeline.get_current_time()
        self._timeline.set_current_time(curr_time + self._physics_scene._current_physics_dt)
        self._number_of_steps += 1
        if render:
            self._app.update()
        else:
            self._physics_scene.step()
        return

    def add_physics_callback(self, callback_fn):
        self._physics_callback_functions.append(
            self._physics_scene._physx_interface.subscribe_physics_step_events(callback_fn)
        )
        return

    def clear_physics_callbacks(self):
        self._physics_callback_functions = []
        return

    def add_stage_callback(self, callback_fn):
        self._stage_callback_functions.append(
            omni.usd.get_context().get_stage_event_stream().create_subscription_to_pop(callback_fn)
        )
        return

    def clear_stage_callbacks(self):
        self._stage_callback_functions = []
        return

    def add_timeline_callback(self, callback_fn):
        self._timeline_callback_functions.append(
            self._timeline.get_timeline_event_stream().create_subscription_to_pop(callback_fn)
        )
        return

    def clear_timeline_callbacks(self):
        self._timeline_callback_functions = []
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
        # define gravity vector
        gravity_dir = Gf.Vec3f(0.0)
        gravity_dir[AXES_INDICES[up_axis]] = -1.0
        # add the physics scene
        if prim.IsValid():
            print(f"Prim at path `{self._path}` is already defined.")
            scene = UsdPhysics.Scene(prim)
        else:
            print("Defining a new physics scene")
            scene = UsdPhysics.Scene.Define(self._stage, self._path)
        scene.CreateGravityDirectionAttr().Set(gravity_dir)
        scene.CreateGravityMagnitudeAttr().Set(9.81 / meters_per_unit)
        self._previous_physics_dt = None
        self._current_physics_dt = self._previous_physics_dt
        self._physx_interface = omni.physx.acquire_physx_interface()
        self._timeline = omni.timeline.get_timeline_interface()
        self._loop_runner = omni_loop.acquire_loop_interface()
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
        physxSceneAPI = None
        for prim in self._stage.Traverse():
            if prim.IsA(UsdPhysics.Scene):
                physxSceneAPI = PhysxSchema.PhysxSceneAPI.Apply(prim)
        if physxSceneAPI is not None:
            physxSceneAPI.GetTimeStepsPerSecondAttr().Set(steps_per_second)
        # set the min frame rate, i.e. frequency of substeps.
        set_carb_setting(carb.settings.get_settings(), "/app/runLoops/main/rateLimitEnabled", True)
        set_carb_setting(carb.settings.get_settings(), "persistent/simulation/minFrameRate", min_steps)
        set_carb_setting(carb.settings.get_settings(), "/app/runLoops/main/rateLimitFrequency", min_steps)
        self._loop_runner.set_runner_dt(dt)

    def set_physics_scene(
        self,
        enable_ccd: bool = True,
        enable_stablization: bool = True,
        enable_gpu_dynamics: bool = False,
        broadphase_type: str = "MBP",
        solver_type: str = "TGS",
    ):
        # Set physics scene to use cpu physics
        PhysxSchema.PhysxSceneAPI.Apply(self._stage.GetPrimAtPath(self._path))
        physxSceneAPI = PhysxSchema.PhysxSceneAPI.Get(self._stage, self._path)
        physxSceneAPI.CreateEnableCCDAttr(enable_ccd)
        physxSceneAPI.CreateEnableStabilizationAttr(enable_stablization)
        physxSceneAPI.CreateEnableGPUDynamicsAttr(enable_gpu_dynamics)
        physxSceneAPI.CreateBroadphaseTypeAttr(broadphase_type)
        physxSceneAPI.CreateSolverTypeAttr(solver_type)
        return

    def step(self):
        self._physx_interface.update_simulation(self._current_physics_dt, self._timeline.get_current_time())
        self._physx_interface.update_transformations(True, True, False, False)
        return
