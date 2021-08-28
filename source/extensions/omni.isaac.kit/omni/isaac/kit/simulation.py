# python
import time
import asyncio

# omniverse
import carb
import omni.kit
import omni.kit.app
import omni.kit
from omni.isaac.kit.utils import set_carb_setting
from pxr import UsdPhysics, PhysxSchema, UsdGeom, Gf
from omni.isaac.kit.constants import AXES_INDICES
import omni.isaac.kit.globals as globals
import os
import omni.kit.loop._loop as omni_loop


class SimulationContext:
    def __init__(self):
        # Only import custom loop runner if we create this object
        # TODO: customization for the physics
        self.set_stage_units(1.0)
        self._physics_scene = PhysicsScene()
        # Acquire the running application interface
        self._app = omni.kit.app.get_app_interface()
        # Acquire interfaces to extensions from Omniverse Toolkit
        self._framework = carb.get_framework()
        self._timeline = omni.timeline.get_timeline_interface()
        # Turn auto-update on for timeline
        self._timeline.set_auto_update(True)
        self._physics_call_back_functions = []
        self._rendering_call_back_functions = []
        self._number_of_steps = 0

    def __del__(self):
        """Destructor for object."""
        pass

    @property
    def app(self):
        """Returns: The Omniverse Toolkit application."""
        return self._app

    @property
    def time_step_index(self):
        return self._number_of_steps

    @property
    def time(self):
        return self._timeline.get_current_time()

    @property
    def stage(self):
        """Returns: The current USD stage."""
        return omni.usd.get_context().get_stage()

    def is_playing(self) -> bool:
        """Returns: True if the simulator is playing."""
        return self._timeline.is_playing()

    def is_stopped(self) -> bool:
        """Returns: True if the simulator is stopped."""
        return self._timeline.is_stopped()

    # TODO: check why you need a simulate before and after

    def start_simulation(self):
        self.play()
        self._physics_scene._physx_interface.start_simulation()
        self._physics_scene._physx_interface.force_load_physics_from_usd()
        return

    def play(self):
        self._timeline.play()
        self.step(render=True)
        return

    def pause(self):
        """Pauses the editor physics simulation"""
        self._timeline.pause()
        self.step(render=True)
        return

    def stop(self):
        """Stops the editor physics simulation"""
        self._timeline.stop()
        self.step(render=True)
        self._number_of_steps = 0
        return

    def create_new_stage(self):
        # Create a blank new stage
        new_stage_task = asyncio.ensure_future(omni.usd.get_context().new_stage_async())
        # This sleep prevents a deadlock in certain cases.
        if not globals.LAUNCHED_FROM_TERMINAL:
            while not new_stage_task.done():
                time.sleep(0.001)
                self._app.update()
            # Update the app
            self._app.update()
        self.set_stage_units(1.0)
        self._physics_scene = PhysicsScene()
        self._physics_scene._stage = omni.usd.get_context().get_stage()
        return

    def open_usd(self, usd_path, prim_path):
        prim = self.stage.DefinePrim(prim_path, "Xform")
        # add reference to the USD in the current stage
        prim.GetReferences().AddReference(usd_path)
        # if not globals.LAUNCHED_FROM_TERMINAL:
        #     self._app.update()
        return prim

    def set_physics_dt(self, dt: float = 1.0 / 60.0, substeps: int = 1):
        self._physics_scene.set_physics_dt(dt, substeps)
        return

    def step(self, number_of_steps=1, render=True):
        for i in range(number_of_steps):
            curr_time = self._timeline.get_current_time()
            self._timeline.set_current_time(curr_time + self._physics_scene._current_physics_dt)
            self._number_of_steps += 1
            if render:
                self._app.update()
            else:
                self._physics_scene.step()
        return

    def add_physics_callback(self, call_back_fn):
        def call_back_func_wrapper(step_size):
            call_back_fn()

        self._physics_call_back_functions.append(
            self._physics_scene._physx_interface.subscribe_physics_step_events(call_back_func_wrapper)
        )
        return

    def set_stage_units(self, stage_units_in_meters):
        UsdGeom.SetStageMetersPerUnit(self.stage, stage_units_in_meters)
        return


# EOF


class PhysicsScene:
    def __init__(self, path: str = "/World/physicsScene"):
        self._stage = omni.usd.get_context().get_stage()
        self._path = path
        if not os.path.abspath(self._path):
            raise ValueError(f"Input prim path is not absolute: {self._path}")
        # check if path pre-exists
        prim = self._stage.GetPrimAtPath(path)
        if prim.IsValid():
            print(f"Prim at path `{self._path}` is already defined.")
            return
        # extract parameters from stage configuration
        meters_per_unit = UsdGeom.GetStageMetersPerUnit(self._stage)
        up_axis = UsdGeom.GetStageUpAxis(self._stage)
        # define gravity vector
        gravity_dir = Gf.Vec3f(0.0)
        gravity_dir[AXES_INDICES[up_axis]] = -1.0
        # add the physics scene
        scene = UsdPhysics.Scene.Define(self._stage, self._path)
        scene.CreateGravityDirectionAttr().Set(gravity_dir)
        scene.CreateGravityMagnitudeAttr().Set(9.81 / meters_per_unit)
        self._previous_physics_dt = 1.0 / 60.0
        self._current_physics_dt = self._previous_physics_dt
        self._physx_interface = omni.physx.acquire_physx_interface()
        self._timeline = omni.timeline.get_timeline_interface()
        self._loop_runner = omni_loop.acquire_loop_interface()
        self.set_physics_scene()
        self.set_physics_dt()
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
        set_carb_setting(carb.settings.get_settings(), "persistent/simulation/minFrameRate", min_steps)
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
