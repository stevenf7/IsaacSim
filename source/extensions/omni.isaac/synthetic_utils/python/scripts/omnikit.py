#!/usr/bin/env python
# Copyright (c) 2020, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.


"""Helper class for launching OmniKit from a Python environment.

Launches and configures OmniKit and exposes useful functions.

    Typical usage example:

    config = {'width': 800, 'height': 600, 'renderer': 'PathTracing'}
    kit = OmniKitHelper(config)   # Start omniverse kit
    # <Code to generate or load a scene>
    kit.update()    # Render a single frame
"""


import carb
import omni.kit.app
import omni.kit.editor
import omni.kit.pipapi
import omni.kit.asyncapi
import omni.kit.commands
from pxr import UsdGeom, Semantics

import os
import time
import atexit
import asyncio


DEFAULT_CONFIG = {
    "width": 1024,
    "height": 800,
    "renderer": "PathTracing",
    "samples_per_pixel_per_frame": 64,
    "denoiser": True,
    "subdiv_refinement_level": 2,
    "headless": True,
    "max_bounces": 4,
    "max_specular_transmission_bounces": 6,
    "max_volume_bounces": 4,
    "config": "isaac-sim-synthetic.json",
}


class OmniKitHelper:
    def __init__(self, config=None):
        # initialize vars
        self._is_dirty_instance_mappings = True
        atexit.register(self._cleanup)
        self.config = DEFAULT_CONFIG
        if config is not None:
            self.config.update(config)

        # Load app plugin
        carb.get_framework().load_plugins(
            loaded_file_wildcards=["omni.kit.app.plugin"], search_paths=["${CARB_APP_PATH}/plugins"]
        )

        # launch kit
        self.last_update_t = time.time()
        self.app = omni.kit.app.get_app_interface()
        self.kit_settings = None
        setup_future = self._launch_kit()
        self._start_app()

        while self.app.is_running() and not setup_future.done():
            time.sleep(0.001)  # This sleep prevents a deadlock in certain cases
            self.update()

        self.editor = omni.kit.editor.get_editor_interface()

    def _launch_kit(self):
        # Set up the renderer
        async def setup():
            await omni.kit.asyncapi.new_stage()
            self.carb_settings = carb.settings.acquire_settings_interface()
            self.kit_settings = omni.kit.settings.get_settings_interface()
            self.setup_renderer()
            self.set_setting("/rtx/rendermode", self.config["renderer"])

        return asyncio.ensure_future(setup())

    def _start_app(self):
        args = [
            os.path.abspath(__file__),
            f'--merge-config={self.config["config"]}',
            "--/persistent/app/viewport/displayOptions=0",  # hide extra stuff in viewport
            "--/persistent/physics/overrideGPUSettings=0",  # force CPU physx
            # "--/persistent/physics/updateToUsd=True",
            # "--/persistent/physics/useFastCache=True",
            "--/app/content/emptyStageOnStart=False",  # This is required due to a infinite loop but results in errors on launch
            f'--/app/renderer/resolution/width={self.config["width"]}',
            f'--/app/renderer/resolution/height={self.config["height"]}',
            f'--carb/app/extensions/folders2/0="{os.environ["KIT_PATH"]}/exts"',  # adding to json doesn't work
            f'--carb/app/extensions/folders2/1="{os.environ["KIT_PATH"]}/extsPhysics"',  # adding to json doesn't work
            f'--carb/app/extensions/folders2/2="{os.environ["ISAAC_PATH"]}/exts"',  # adding to json doesn't work
        ]
        if self.config.get("headless"):
            args.append("--no-window")
            args.append("--/app/window/hideUi=true")
        self.app.startup("omniverse-kit", os.environ["CARB_APP_PATH"], args)

    def _cleanup(self):
        self.update()
        self.app.post_quit()
        # self.app.shutdown()
        self.app = None

    def get_stage(self):
        """Returns the current stage."""
        return omni.usd.get_context().get_stage()

    def set_setting(self, setting, value):
        """Convenience function to set settings."""
        if isinstance(value, str):
            self.carb_settings.set_string(setting, value)
        elif isinstance(value, bool):
            self.carb_settings.set_bool(setting, value)
        elif isinstance(value, int):
            self.carb_settings.set_int(setting, value)
        elif isinstance(value, float):
            self.carb_settings.set_float(setting, value)
        else:
            raise ValueError(f"Value of type {type(value)} is not supported.")

    def update(self, dt=0.0):
        """Render one frame. Optionally specify dt in seconds, specify None to use wallclock"""
        if dt is not None:
            if self.kit_settings and dt > 0.0:
                self.kit_settings.set("/physics/timeStepsPerSecond", float(1.0 / dt))
            self.app.update(dt)
        else:
            time_now = time.time()
            dt = time_now - self.last_update_t
            self.last_update_t = time_now
            if self.kit_settings and dt > 0.0:
                self.kit_settings.set("/physics/timeStepsPerSecond", float(1.0 / dt))
            self.app.update(dt)

    def play(self):
        """Starts the editor physics simulation"""
        self.update()
        self.editor.play()
        self.update()

    def pause(self):
        """Pauses the editor physics simulation"""
        self.update()
        self.editor.pause()
        self.update()

    def stop(self):
        """Stops the editor physics simulation"""
        self.update()
        self.editor.stop()
        self.update()

    def get_status(self):
        """Get the status of the renderer to see if anything is loading"""
        return self.editor.get_current_renderer_status()

    def is_loading(self):
        """convenience function to see if any files are being loaded"""
        time, message, loaded, loading = self.get_status()
        return loading > 0

    def execute(self, *args, **kwargs):
        """allow use of kit command interface"""
        omni.kit.commands.execute(*args, **kwargs)

    def setup_renderer(self):
        """Set settings for renderer"""
        self.set_setting("/rtx/pathtracing/spp", self.config["samples_per_pixel_per_frame"])
        self.set_setting("/rtx/pathtracing/totalSpp", self.config["samples_per_pixel_per_frame"])
        self.set_setting("/rtx/pathtracing/clampSpp", self.config["samples_per_pixel_per_frame"])
        self.set_setting("/rtx/pathtracing/maxBounces", self.config["max_bounces"])
        self.set_setting(
            "/rtx/pathtracing/maxSpecularAndTransmissionBounces", self.config["max_specular_transmission_bounces"]
        )
        self.set_setting("/rtx/pathtracing/maxVolumeBounces", self.config["max_volume_bounces"])
        self.set_setting("/rtx/pathtracing/optixDenoiser/enabled", self.config["denoiser"])
        self.set_setting("/rtx/hydra/subdivision/refinementLevel", self.config["subdiv_refinement_level"])

    def create_prim(
        self, path, prim_type, translation=None, rotation=None, scale=None, ref=None, semantic_label=None, attributes={}
    ):
        """Create a prim, apply specified transforms, apply semantic label and
        set specified attributes.

        args:
            path (str): The path of the new prim.
            prim_type (str): Prim type name
            translation (tuple(float, float, float), optional): prim translation (applied last)
            rotation (tuple(float, float, float), optional): prim rotation in radians with rotation
                order ZYX.
            scale (tuple(float, float, float), optional): scaling factor in x, y, z.
            ref (str, optional): Path to the USD that this prim will reference.
            semantic_label (str, optional): Semantic label.
            attributes (dict, optional): Key-value pairs of prim attributes to set.
        """
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
            xform_api.SetRotate(rotation, UsdGeom.XformCommonAPI.RotationOrderZYX)
        if scale:
            xform_api.SetScale(scale)
        if translation:
            xform_api.SetTranslate(translation)
        return prim


if __name__ == "__main__":
    # Example usage, with step size test
    kit = OmniKitHelper()

    stage = kit.get_stage()
    cube = UsdGeom.Cube.Define(stage, "/World/cube")
    UsdGeom.XformCommonAPI(cube).SetScale([100, 100, 100])
    # Create callbacks to print both editor and physics

    def editor_update(dt):
        print("kit update step:", dt, "seconds")

    def physics_update(dt):
        print("physics update step:", dt, "seconds")

    kit.play()
    update_sub = kit.editor.subscribe_to_update_events(editor_update)
    physics_sub = omni.physx._physx.acquire_physx_interface().subscribe_physics_step_events(physics_update)
    kit.update(1.0)
    kit.update(2.0)
    kit.update(1.0 / 60.0)
    kit.update(1.0)
    update_sub = None
    physics_sub = None
    kit.stop()
