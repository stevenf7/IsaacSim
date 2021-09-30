# Copyright (c) 2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#

from __future__ import annotations  # This allows us to hint types that do not yet exist like omni.usd etc

import os
import sys
import argparse

import carb
import omni.kit.app


class SimulationApp:
    """Helper class to launch Omniverse Toolkit.

    Omniverse loads various plugins at runtime which cannot be imported unless
    the Toolkit is already running. Thus, it is necessary to launch the Toolkit first from
    your python application and then import everything else.

    Usage:

    .. code-block:: python

        # At top of your application
        from omni.isaac.kit import SimulationApp
        config = {
             width: "1280",
             height: "720",
             headless: False,
        }
        simulation_app = SimulationApp(config)

        # Rest of the code follows
        ...
        simulation_app.close()

    Note:
            The settings in :obj:`DEFAULT_LAUNCHER_CONFIG` are overwritten by those in :obj:`config`.

    Arguments:
        config (dict): A dictionary containing the configuration for the app. (default: None)
        experience (str): Path to the application config loaded by the launcher (default: "", will load app/omni.isaac.sim.python.kit if left blank)
    """

    DEFAULT_LAUNCHER_CONFIG = {
        "headless": True,
        "active_gpu": None,
        "sync_loads": True,
        "width": 1280,
        "height": 720,
        "window_width": 1440,
        "window_height": 900,
        "display_options": 0,
        "subdiv_refinement_level": 0,
        "renderer": "RayTracedLighting",  # Can also be PathTracing
        "anti_aliasing": 3,
        "samples_per_pixel_per_frame": 64,
        "denoiser": True,
        "max_bounces": 4,
        "max_specular_transmission_bounces": 6,
        "max_volume_bounces": 4,
    }
    """
    The config variable is a dictionary containing the following entries

    Args:
        headless (bool): Disable UI when running. Defaults to True
        active_gpu (int): Specify the GPU to use when running, set to None to use default value which is usually the first gpu, default is None
        sync_loads (bool): When enabled, will pause rendering until all assets are loaded. Defaults to True
        width (int): Width of the viewport and generated images. Defaults to 1024
        height (int): Height of the viewport and generated images. Defaults to 800
        window_width (int): Width of the application window, independent of viewport, defaults to 1440,
        window_height (int): Height of the application window, independent of viewport, defaults to 900,
        display_options (int): used to specify whats visible in the stage by default. Defaults to 0 so extra objects do not appear in synthetic data. 3807 is another good default, used for the regular isaac-sim editor experience
        subdiv_refinement_level (int): Number of subdivisons to perform on supported geometry. Defaults to 0
        renderer (str): Rendering mode, can be  `RayTracedLighting` or `PathTracing`. Defaults to `PathTracing`
        antialiasing (int): Antialiasing mode, 0: Disabled, 1: TAA, 2: FXAA, 3: DLSS, 4:RTXAA
        samples_per_pixel_per_frame (int): The number of samples to render per frame, increase for improved quality, used for `PathTracing` only. Defaults to 64
        denoiser (bool):  Enable this to use AI denoising to improve image quality, used for `PathTracing` only. Defaults to True
        max_bounces (int): Maximum number of bounces, used for `PathTracing` only. Defaults to 4
        max_specular_transmission_bounces(int): Maximum number of bounces for specular or transmission, used for `PathTracing` only. Defaults to 6
        max_volume_bounces(int): Maximum number of bounces for volumetric materials, used for `PathTracing` only. Defaults to 4
    """

    def __init__(self, launch_config: dict = None, experience: str = "") -> None:
        import omni.isaac.kit.global_vars as global_vars

        # Initialize variables
        global_vars.LAUNCHED_FROM_TERMINAL = False
        self._exiting = False

        # Override settings from input config
        self.config = self.DEFAULT_LAUNCHER_CONFIG
        if experience == "":
            experience = f'{os.environ["EXP_PATH"]}/omni.isaac.sim.python.kit'
        if global_vars.LAUNCHED_FROM_JUPYTER:
            if launch_config["headless"] is False:
                carb.log_warn("Non-headless mode not supported with jupyter notebooks")
                launch_config.update({"headless": True})
        self.config.update({"experience": experience})
        if launch_config is not None:
            self.config.update(launch_config)

        # Load omniverse application plugins
        self._framework = carb.get_framework()
        self._framework.load_plugins(
            loaded_file_wildcards=["omni.kit.app.plugin"],
            search_paths=[os.path.abspath(f'{os.environ["CARB_APP_PATH"]}/plugins')],
        )
        # Get Omniverse application
        self._app = omni.kit.app.get_app()
        self._start_app()

        # vp_interface = omni.kit.viewport.acquire_viewport_interface()
        # vp_window = vp_interface.get_viewport_window()
        # drawable = vp_window.get_drawable()

        # if drawable is None:
        #     self._app.update()

        # once app starts, we can set settings
        from omni.isaac.kit.utils import set_carb_setting

        self._carb_settings = carb.settings.get_settings()
        # Set rtx-default renderder settings
        self._setup_renderer(mode="default")
        # Set rtx settings renderer settings
        self._setup_renderer(mode="non-default")

        set_carb_setting(self._carb_settings, "/persistent/simulation/defaultMetersPerUnit", 1.0)
        print("Simulation App Starting")

        # Update the app
        self._app.update()

        # Dock floating UIs
        self._prepare_ui()
        # Notify toolkit is running
        print("Simulation App Startup Complete")

    def __del__(self):
        """Destructor for the class."""
        if self._exiting is False and sys.meta_path is None:
            print(
                "\033[91m"
                + "ERROR: Python exiting while SimulationApp was still running, Please call close() on the SimulationApp object to exit cleanly"
                + "\033[0m"
            )
        pass

    """
    Private methods
    """

    def _start_app(self) -> None:
        """Launch the Omniverse application."""
        # input arguments to the application
        args = [
            os.path.abspath(__file__),
            f'{self.config["experience"]}',
            f'--/persistent/app/viewport/displayOptions={self.config["display_options"]}',  # hide extra stuff in viewport
            # Forces kit to not render until all USD files are loaded
            f'--/rtx/materialDb/syncLoads={self.config["sync_loads"]}',
            f'--/rtx/hydra/materialSyncLoads={self.config["sync_loads"]}'
            f'--/omni.kit.plugin/syncUsdLoads={self.config["sync_loads"]}',
            f'--/app/renderer/resolution/width={self.config["width"]}',
            f'--/app/renderer/resolution/height={self.config["height"]}',
            f'--/app/window/width={self.config["window_width"]}',
            f'--/app/window/height={self.config["window_height"]}',
            "--ext-folder",
            f'{os.path.abspath(os.environ["ISAAC_PATH"])}/exts',  # adding to json doesn't work
        ]
        if self.config.get("active_gpu") is not None:
            args.append(f'--/renderer/activeGpu={self.config["active_gpu"]}')
        # parse any extra command line args here
        parser = argparse.ArgumentParser()
        parser.add_argument("--portable-root")
        parser.add_argument("--allow-root", default=False, action="store_true")
        parser.add_argument("--no-window", default=False, action="store_true")
        parsed_args, unknown_args = parser.parse_known_args()
        if parsed_args.portable_root is not None:
            args.append("--portable-root")
            args.append(f"{parsed_args.portable_root}")
        else:
            args.append("--portable")

        if parsed_args.allow_root:
            args.append("--allow-root")
        if parsed_args.no_window or self.config.get("headless"):
            args.append("--no-window")
        self.app.startup("kit", os.environ["CARB_APP_PATH"], args)

    def _setup_renderer(self, mode: str = "non-default") -> None:
        """Reset render settings to those in config.

        Note:
            This should be used in case a new stage is opened and the desired config needs
            to be re-applied.

        Keyword Arguments:
            mode {str} -- Whether to setup RTX default or non-default settings. (default: {"non-default"})
        """
        from omni.isaac.kit.utils import set_carb_setting

        # Define mode to configure settings into.
        if mode == "default":
            rtx_mode = "/rtx-defaults"
        else:
            rtx_mode = "/rtx"

        # Set renderer mode.
        set_carb_setting(self._carb_settings, rtx_mode + "/rendermode", self.config["renderer"])
        # Raytrace mode settings
        set_carb_setting(self._carb_settings, rtx_mode + "/post/aa/op", self.config["anti_aliasing"])
        # Pathtrace mode settings
        set_carb_setting(self._carb_settings, rtx_mode + "/pathtracing/spp", self.config["samples_per_pixel_per_frame"])
        set_carb_setting(
            self._carb_settings, rtx_mode + "/pathtracing/totalSpp", self.config["samples_per_pixel_per_frame"]
        )
        set_carb_setting(
            self._carb_settings, rtx_mode + "/pathtracing/clampSpp", self.config["samples_per_pixel_per_frame"]
        )
        set_carb_setting(self._carb_settings, rtx_mode + "/pathtracing/maxBounces", self.config["max_bounces"])
        set_carb_setting(
            self._carb_settings,
            rtx_mode + "/pathtracing/maxSpecularAndTransmissionBounces",
            self.config["max_specular_transmission_bounces"],
        )
        set_carb_setting(
            self._carb_settings, rtx_mode + "/pathtracing/maxVolumeBounces", self.config["max_volume_bounces"]
        )
        set_carb_setting(self._carb_settings, rtx_mode + "/pathtracing/optixDenoiser/enabled", self.config["denoiser"])
        set_carb_setting(
            self._carb_settings, rtx_mode + "/hydra/subdivision/refinementLevel", self.config["subdiv_refinement_level"]
        )

        # Experimental, forces kit to not render until all USD files are loaded
        set_carb_setting(self._carb_settings, rtx_mode + "/materialDb/syncLoads", self.config["sync_loads"])
        set_carb_setting(self._carb_settings, rtx_mode + "/hydra/materialSyncLoads", self.config["sync_loads"])
        set_carb_setting(self._carb_settings, "/omni.kit.plugin/syncUsdLoads", self.config["sync_loads"])

    def _prepare_ui(self) -> None:
        """Dock the windows in the UI if they exist."""
        # Method for docking a particular window to a location
        def dock_window(space, name, location, ratio=0.5):
            window = omni.ui.Workspace.get_window(name)
            if window and space:
                window.dock_in(space, location, ratio=ratio)
            return window

        # Acquire the main docking station
        main_dockspace = omni.ui.Workspace.get_window("DockSpace")
        # Acquire the docking space for viewport
        view = dock_window(main_dockspace, "Viewport", omni.ui.DockPosition.TOP)
        self._app.update()
        dock_window(view, "Console", omni.ui.DockPosition.BOTTOM, 0.3)
        dock_window(view, "Main ToolBar", omni.ui.DockPosition.LEFT)
        self._app.update()
        # Acquire the docking window where `Stage` tab is present and add tabs
        render = dock_window(main_dockspace, "Render Settings", omni.ui.DockPosition.RIGHT, 0.3)
        dock_window(render, "Stage", omni.ui.DockPosition.SAME)
        dock_window(render, "Layer", omni.ui.DockPosition.SAME)
        self._app.update()
        dock_window(render, "Property", omni.ui.DockPosition.BOTTOM)
        self._app.update()

    """
    Public methods
    """

    def new_livesync_stage(self, usd_path: str) -> None:
        """
        Creates a new stage and enables livesync. 
        If a stage exists at the specified path, it will be destroyed upon creation

        Args:
            usd_path (str): path to save new usd stage at and enable livesync
        """
        omni.usd.get_context().new_stage()
        omni.usd.get_context().save_as_stage(usd_path)
        omni.usd.get_context().set_layer_live(usd_path, True)

    def update(self) -> None:
        """
        Convenience function to step the application forward one frame
        """
        self._app.update()
        return

    def set_setting(self, setting: str, value) -> None:
        """
        Set a carbonite setting

        Args:
            setting (str): carb setting path
            value: value to set the setting to, type is used to properly set the setting. 
        """
        from omni.isaac.kit.utils import set_carb_setting

        set_carb_setting(self._carb_settings, setting, value)

    def set_extension_enabled(self, name: str, enabled: bool) -> None:
        """
        Set the state for an extension

        Args:
            name (str): name of extension to enabled
            enabled (bool): true if extension should be enabled, false to turn extension off

        """
        ext_manager = omni.kit.app.get_app().get_extension_manager()
        ext_manager.set_extension_enabled_immediate(name, enabled)

    def close(self) -> None:
        """Close the running Omniverse Toolkit."""
        # check if exited already
        if not self._exiting:
            self._exiting = True
            print("Shutting Down Simulation App...")
            # We are exisitng but something is still loading, wait for it to load to avoid a deadlock
            if self.is_loading():
                print("   Waiting for USD resource operations to complete (this may take a few seconds)")
            while self.is_loading():
                self._app.update()
            self._app.shutdown()
            self._framework.unload_all_plugins()
            # Force all omni module to unload on close
            # This prevents crash on exit
            for m in list(sys.modules.keys()):
                if "omni" in m and m != "omni.kit.app":
                    del sys.modules[m]
            print("Simulation App Shutdown Completed...")

    def is_running(self) -> bool:
        """
            bool: convenience function to see if app is running. True if running, False otherwise
        """
        return self._app.is_running()

    def is_loading(self) -> bool:
        """
            bool: Convenience function to see if any files are being loaded. True if loading, False otherwise
        """
        context = omni.usd.get_context()
        if context is None:
            return False
        else:
            _, _, loading = context.get_stage_loading_status()
            return loading > 0

    def is_exiting(self) -> bool:
        """
            bool: True if close() was called previously, False otherwise
        """
        return self._exiting

    @property
    def app(self) -> omni.kit.app.IApp:
        """
            omni.kit.app.IApp: omniverse kit application object
        """
        return self._app

    @property
    def context(self) -> omni.usd.UsdContext:
        """
            omni.usd.UsdContext: the current USD context
        """
        return omni.usd.get_context()
