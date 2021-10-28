# Copyright (c) 2020-2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.


import carb
import omni.kit.app
import omni.kit
import time
from omni.isaac.kit import SimulationApp

DEPRECATION_WARN = (
    "OmnikitHelper is deprecated please use omni.isaac.kit.SimulationApp and omni.isaac.core.SimulationContext"
)


class OmniKitHelper:
    """
    Deprecated: Please use omni.isaac.kit.SimulationApp
    Helper class for launching OmniKit from a Python environment.
    """

    DEFAULT_CONFIG = {
        "experience": "isaac-sim.python.kit",
        "headless": True,
        "active_gpu": None,
        "sync_loads": False,
        "width": 1024,
        "height": 800,
        "window_width": 1440,
        "window_height": 900,
        "display_options": 0,
        "subdiv_refinement_level": 0,
        "renderer": "PathTracing",  # Can also be RayTracedLighting
        "anti_aliasing": 3,  # 3 for dlss, 2 for fxaa, 1 for taa, 0 to disable aa
        "samples_per_pixel_per_frame": 64,
        "denoiser": True,
        "max_bounces": 4,
        "max_specular_transmission_bounces": 6,
        "max_volume_bounces": 4,
    }

    def __init__(self, config=DEFAULT_CONFIG):
        carb.log_warn(DEPRECATION_WARN)
        self.config = SimulationApp.DEFAULT_LAUNCHER_CONFIG
        if config is not None:
            self.config.update(config)
        self.simulation_app = SimulationApp(launch_config=config, experience=self.config["experience"])
        from omni.kit.loop import _loop

        self.loop_runner = _loop.acquire_loop_interface()
        self.timeline = omni.timeline.get_timeline_interface()
        self._exiting = False
        self._previous_physics_dt = 1.0 / 60.0
        self.last_update_t = time.time()

    def shutdown(self):
        carb.log_warn(DEPRECATION_WARN)
        self.simulation_app.close()

    def get_stage(self):
        """Returns the current USD stage."""
        carb.log_warn(DEPRECATION_WARN)
        return self.simulation_app.context.get_stage()

    def get_context(self):
        """Returns the current USD context."""
        carb.log_warn(DEPRECATION_WARN)
        return self.simulation_app.context

    def set_setting(self, setting, value):
        """Convenience function to set settings.

        Args:
            setting (str): string representing the setting being changed
            value: new value for the setting being changed, the type of this value must match its repsective setting
        """
        carb.log_warn(DEPRECATION_WARN)
        from omni.isaac.core.utils.carb import set_carb_setting

        set_carb_setting(carb.settings.get_settings(), setting, value)

    def set_physics_dt(self, physics_dt: float = 1.0 / 60.0, physics_substeps: int = 1):
        """Specify the physics step size to use when simulating, default is 1/60.
        Note that a physics scene has to be in the stage for this to do anything

        Args:
            physics_dt (float): Use this value for physics step
            physics_substeps (int): The number of physics substeps to perform each editor timestep
        """
        carb.log_warn(DEPRECATION_WARN)
        if self.get_stage() is None:
            return
        if physics_dt == self._previous_physics_dt:
            return
        if physics_substeps is None or physics_substeps <= 1:
            physics_substeps = 1
        self._previous_physics_dt = physics_dt
        from pxr import UsdPhysics, PhysxSchema

        steps_per_second = int(1.0 / physics_dt)
        min_steps = int(steps_per_second / physics_substeps)
        physxSceneAPI = None
        for prim in self.get_stage().Traverse():
            if prim.IsA(UsdPhysics.Scene):
                physxSceneAPI = PhysxSchema.PhysxSceneAPI.Apply(prim)
        if physxSceneAPI is not None:
            physxSceneAPI.GetTimeStepsPerSecondAttr().Set(steps_per_second)

        settings = carb.settings.get_settings()
        settings.set_int("persistent/simulation/minFrameRate", min_steps)

    def update(self, dt=0.0, physics_dt=None, physics_substeps=None):
        """Render one frame. Optionally specify dt in seconds, specify None to use wallclock.
        Specify physics_dt and  physics_substeps to decouple the physics step size from rendering

        For example: to render with a dt of 1/30 and simulate physics at 1/120 use:
            - dt = 1/30.0
            - physics_dt = 1/120.0
            - physics_substeps = 4

        Args:
            dt (float): The step size used for the overall update, set to None to use wallclock
            physics_dt (float, optional): If specified use this value for physics step
            physics_substeps (int, optional): Maximum number of physics substeps to perform
        """
        carb.log_warn(DEPRECATION_WARN)
        # dont update if exit was called
        if self._exiting:
            return
        # a physics dt was specified and is > 0
        if physics_dt is not None and physics_dt > 0.0:
            self.set_physics_dt(physics_dt, physics_substeps)
        # a dt was specified and is > 0
        if dt is not None and dt > 0.0:
            # if physics dt was not specified, use rendering dt
            if physics_dt is None:
                self.set_physics_dt(dt)
            self.loop_runner.set_runner_dt(dt)
            self.simulation_app.update()
        else:
            # dt not specified, run in realtime
            time_now = time.time()
            dt = time_now - self.last_update_t
            if physics_dt is None:
                self.set_physics_dt(1.0 / 60.0, 4)
            self.last_update_t = time_now
            self.loop_runner.set_runner_dt(dt)
            self.simulation_app.update()

    def play(self):
        """Starts the editor physics simulation"""
        carb.log_warn(DEPRECATION_WARN)
        self.update()
        self.timeline.play()
        self.update()

    def pause(self):
        """Pauses the editor physics simulation"""
        carb.log_warn(DEPRECATION_WARN)
        self.update()
        self.timeline.pause()
        self.update()

    def stop(self):
        """Stops the editor physics simulation"""
        carb.log_warn(DEPRECATION_WARN)
        self.update()
        self.timeline.stop()
        self.update()

    def get_status(self):
        """Get the status of the renderer to see if anything is loading"""
        carb.log_warn(DEPRECATION_WARN)
        return omni.usd.get_context().get_stage_loading_status()

    def is_loading(self):
        """convenience function to see if any files are being loaded

        Returns:
            bool: True if loading, False otherwise
        """
        carb.log_warn(DEPRECATION_WARN)
        message, loaded, loading = self.get_status()
        return loading > 0

    def is_exiting(self):
        """get current exit status for this object
        Returns:
            bool: True if exit() was called previously, False otherwise
        """
        carb.log_warn(DEPRECATION_WARN)
        return self._exiting

    def execute(self, *args, **kwargs):
        """Allow use of omni.kit.commands interface"""
        carb.log_warn(DEPRECATION_WARN)
        omni.kit.commands.execute(*args, **kwargs)

    def setup_renderer(self, mode="non-default"):
        """
        Sets the defaults for the renderer based on the config provided at initialization
        """
        carb.log_warn(DEPRECATION_WARN)
        rtx_mode = "/rtx-defaults" if mode == "default" else "/rtx"
        """Reset render settings to those in config. This should be used in case a new stage is opened and the desired config needs to be re-applied"""
        self.set_setting(rtx_mode + "/rendermode", self.config["renderer"])
        # Raytrace mode settings
        self.set_setting(rtx_mode + "/post/aa/op", self.config["anti_aliasing"])
        # Pathtrace mode settings
        self.set_setting(rtx_mode + "/pathtracing/spp", self.config["samples_per_pixel_per_frame"])
        self.set_setting(rtx_mode + "/pathtracing/totalSpp", self.config["samples_per_pixel_per_frame"])
        self.set_setting(rtx_mode + "/pathtracing/clampSpp", self.config["samples_per_pixel_per_frame"])
        self.set_setting(rtx_mode + "/pathtracing/maxBounces", self.config["max_bounces"])
        self.set_setting(
            rtx_mode + "/pathtracing/maxSpecularAndTransmissionBounces",
            self.config["max_specular_transmission_bounces"],
        )
        self.set_setting(rtx_mode + "/pathtracing/maxVolumeBounces", self.config["max_volume_bounces"])
        self.set_setting(rtx_mode + "/pathtracing/optixDenoiser/enabled", self.config["denoiser"])
        self.set_setting(rtx_mode + "/hydra/subdivision/refinementLevel", self.config["subdiv_refinement_level"])

        # Experimental, forces kit to not render until all USD files are loaded
        self.set_setting(rtx_mode + "/materialDb/syncLoads", self.config["sync_loads"])
        self.set_setting(rtx_mode + "/hydra/materialSyncLoads", self.config["sync_loads"])
        self.set_setting("/omni.kit.plugin/syncUsdLoads", self.config["sync_loads"])

    def create_prim(
        self, path, prim_type, translation=None, rotation=None, scale=None, ref=None, semantic_label=None, attributes={}
    ):
        """Create a prim, apply specified transforms, apply semantic label and
        set specified attributes.

        args:
            path (str): The path of the new prim.
            prim_type (str): Prim type name
            translation (tuple(float, float, float), optional): prim translation (applied last)
            rotation (tuple(float, float, float), optional): prim rotation in degrees with rotation
                order ZYX.
            scale (tuple(float, float, float), optional): scaling factor in x, y, z.
            ref (str, optional): Path to the USD that this prim will reference.
            semantic_label (str, optional): Semantic label.
            attributes (dict, optional): Key-value pairs of prim attributes to set.
        """
        carb.log_warn(DEPRECATION_WARN)
        from pxr import UsdGeom, Semantics

        prim = self.get_stage().DefinePrim(path, prim_type)

        for k, v in attributes.items():
            prim.GetAttribute(k).Set(v)
        xform_api = UsdGeom.XformCommonAPI(prim)
        if ref:
            prim.GetReferences().AddReference(ref)
        if semantic_label:
            sem = Semantics.SemanticsAPI.Apply(prim, "Semantics")
            sem.CreateSemanticTypeAttr()
            sem.CreateSemanticDataAttr()
            sem.GetSemanticTypeAttr().Set("class")
            sem.GetSemanticDataAttr().Set(semantic_label)
        if rotation:
            xform_api.SetRotate(rotation, UsdGeom.XformCommonAPI.RotationOrderXYZ)
        if scale:
            xform_api.SetScale(scale)
        if translation:
            xform_api.SetTranslate(translation)
        return prim

    def set_up_axis(self, axis):
        """Change the up axis of the current stage

        Args:
            axis: valid values are `UsdGeom.Tokens.y`, or `UsdGeom.Tokens.z`
        """
        carb.log_warn(DEPRECATION_WARN)
        from pxr import UsdGeom
        from omni.isaac.core.utils.stage import set_stage_up_axis

        if axis == UsdGeom.Tokens.x:
            set_stage_up_axis("x")
        elif axis == UsdGeom.Tokens.y:
            set_stage_up_axis("y")
        else:
            set_stage_up_axis("z")
