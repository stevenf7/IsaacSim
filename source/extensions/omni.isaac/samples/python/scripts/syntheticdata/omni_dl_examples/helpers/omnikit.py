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
from pxr import UsdGeom

import os
import time
import atexit
import asyncio


DEFAULT_CONFIG = {
    "ov-server": None,
    "username": None,
    "password": None,
    "width": 1024,
    "height": 800,
    "renderer": "PathTracing",
    "samples_per_pixel_per_frame": 64,
    "denoiser": True,
    "subdiv_refinement_level": 2,
    "headless": True,
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
        setup_future = self._launch_kit()
        self._start_app()

        while self.app.is_running() and not setup_future.done():
            self.update()

        self.editor = omni.kit.editor.get_editor_interface()

    def _launch_kit(self):
        # Set up the renderer
        async def setup():
            if self.config["ov-server"] and self.config["username"] and self.config["password"]:
                await omni.kit.asyncapi.connect(
                    self.config["ov-server"], self.config["username"], self.config["password"]
                )
            await omni.kit.asyncapi.new_stage()

            # Setup renderer
            self.settings = carb.settings.acquire_settings_interface()
            self.settings.set_int("/rtx/pathtracing/spp", self.config["samples_per_pixel_per_frame"])
            self.settings.set_bool("/rtx/pathtracing/optixDenoiser/enabled", self.config["denoiser"])
            self.settings.set_string("/rtx/rendermode", self.config["renderer"])
            self.settings.set_int("/rtx/hydra/subdivision/refinementLevel", self.config["subdiv_refinement_level"])

        return asyncio.ensure_future(setup())

    def _start_app(self):
        args = [
            os.path.abspath(__file__),
            "--carb/persistent/app/viewport/displayOptions=0",
            "--carb/app/window/hideUi=true",
            f'--carb/app/renderer/resolution/width={self.config["width"]}',
            f'--carb/app/renderer/resolution/height={self.config["height"]}',
            "--carb/app/extensions/enabled/0='omni.syntheticdata'",
        ]
        if self.config.get("headless"):
            args.append("--no-window")
        self.app.startup("omniverse-kit", os.environ["CARB_APP_PATH"], args)

    def _cleanup(self):
        self.update()
        self.app.shutdown()

    def get_stage(self):
        """Returns the current stage."""
        return omni.usd.get_context().get_stage()

    def update(self):
        """Render one frame."""
        time_now = time.time()
        dt = time_now - self.last_update_t
        self.last_update_t = time_now
        self.app.update(dt)


if __name__ == "__main__":
    # Example usage
    kit = OmniKitHelper()

    stage = kit.get_stage()
    cube = UsdGeom.Cube.Define(stage, "/World/cube")
    UsdGeom.XformCommonAPI(cube).SetScale([100, 100, 100])
