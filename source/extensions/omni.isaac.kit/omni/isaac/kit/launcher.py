import os
import time
import asyncio
import argparse
from typing import Any, ClassVar

# omniverse
from omni.isaac.kit.utils import set_carb_setting
import carb
import omni.kit.app
import omni.kit
import omni.isaac.kit.globals as globals

DEFAULT_LAUNCHER_CONFIG = {
    # Width of the viewport and generated images. (default: 1024)
    "width": 1280,
    # Height of the viewport and generated images. (default: 720)
    "height": 720,
    # Rendering mode: `RayTracedLighting` or `PathTracing`. (default: `RayTracedLighting`)
    "renderer": "RayTracedLighting",
    # Whether to run the render on the active GPU or not. (default: False)
    "active_gpu": False,
    # Disable UI when running. (default: False)
    "headless": True,
    # Enable this to use AI de-noising to improve image quality. (default: True)
    "denoiser": True,
    # Enable this to perform anti-aliasing in rendered viewport. (default: 0)
    "anti_aliasing": 0,
    # Number of sub-divisions to perform on supported geometry. (default: 0)
    "subdiv_refinement_level": 0,
    # The number of samples to render per frame used for `PathTracing` only. (default: 64)
    "samples_per_pixel_per_frame": 64,
    # Maximum number of bounces used for `PathTracing` only. (default: 4)
    "max_bounces": 4,
    # Maximum number of bounces for specular or transmission used for `PathTracing` only. (default: 6)
    "max_specular_transmission_bounces": 6,
    # Maximum number of bounces for volumetric, used for `PathTracing` only. (default: 4)
    "max_volume_bounces": 4,
    # When enabled, it will pause rendering until all assets are loaded. (default: False)
    "sync_loads": False,
}


class SimulationApp:
    """Helper class to launch Omniverse Toolkit.

    Omniverse loads various plugins at runtime which cannot be imported unless
    the Toolkit is already running. Thus, it is necessary to launch the Toolkit first from
    your python application and then import everything else.

    Usage:

        >>> # At top of your application
        >>> from omniverse_robotics.core.launcher import OmniKitLauncher
        >>>
        >>> config = {
        ...     width: "1280",
        ...     height: "720",
        ...     headless: False,
        ... }
        >>> _ = OmniKitLauncher(config)
        >>>
        >>> # Rest of the code follows
        >>> ...
    """

    def __init__(self, config: dict = None):
        """Initializes the Omniverse application from input configuration.

        Note:
            The settings in :obj:`DEFAULT_LAUNCHER_CONFIG` are overwritten by those in :obj:`config`.

        Arguments:
            config {dict} -- A dictionary containing the configuration for the app. (default: {None})
        """
        # Override settings from input config
        globals.LAUNCHED_FROM_TERMINAL = False
        self.config = DEFAULT_LAUNCHER_CONFIG
        self.config.update({"experience": f'{os.environ["EXP_PATH"]}/omni.isaac.sim.python.kit'})
        if config is not None:
            self.config.update(config)
        # Initialize variables
        self._exiting = False
        # Load omniverse application plugins
        self._framework = carb.get_framework()
        self._framework.load_plugins(
            loaded_file_wildcards=["omni.kit.app.plugin"],
            search_paths=[os.path.abspath(f'{os.environ["CARB_APP_PATH"]}/plugins')],
        )
        # Get Omniverse application
        self._app = omni.kit.app.get_app()
        self._start_app()

        # Set rtx-default renderder settings
        self._setup_renderer(mode="default")
        # Set rtx settings renderer settings
        self._setup_renderer(mode="non-default")

        new_stage_task = asyncio.ensure_future(omni.usd.get_context().new_stage_async())
        # This sleep prevents a deadlock in certain cases.
        while not new_stage_task.done():
            time.sleep(0.001)
            self._app.update()
        # Update the app
        self._app.update()

        # Dock floating UIs
        self._prepare_ui()
        # Notify toolkit is running
        # print_notify("Running Omniverse Toolkit application...")

    def __del__(self):
        """Destructor for the class."""
        pass

    """
    Private methods
    """

    def _start_app(self):
        """Launch the Omniverse application."""
        # input arguments to the application
        args = [
            os.path.abspath(__file__),
            # User defined settings for launching Omniverse
            f'{self.config["experience"]}',
            # Hide extra stuff in viewport
            "--/persistent/app/viewport/displayOptions=0",
            # TODO: Make this a config setting?
            # Force CPU PhysX
            "--/persistent/physics/overrideGPUSettings=0",
            # Forces kit to not render until all USD files are loaded.
            f'--/rtx-defaults/materialDb/syncLoads={self.config["sync_loads"]}',
            f'--/rtx/hydra/materialSyncLoads={self.config["sync_loads"]}',
            f'--/omni.kit.plugin/syncUsdLoads={self.config["sync_loads"]}',
            # TODO: Is this still needed?
            # This is required due to a infinite loop but results in errors on launch
            "--/app/content/emptyStageOnStart=False",
            "--/app/hydraEngine/waitIdle=True",
            # Setup renderer
            "--/app/asyncRendering=False",
            f'--/app/renderer/resolution/width={self.config["width"]}',
            f'--/app/renderer/resolution/height={self.config["height"]}',
            # Specify directories to load extensions from (adding to json doesn't work)
            "--ext-folder",
            f'{os.path.abspath(os.environ["ISAAC_PATH"])}/exts',
        ]
        # Whether to run the app without UI
        if self.config.get("headless"):
            args.append("--no-window")
        # Whether to use current GPU
        if self.config.get("active_gpu"):
            args.append(f'--/renderer/activeGpu={self.config["active_gpu"]}')
        # Parse any extra command line args here
        parser = argparse.ArgumentParser()
        parser.add_argument("--portable-root")
        parsed_args, _ = parser.parse_known_args()
        if parsed_args.portable_root is not None:
            args.append("--portable-root")
            args.append(f"{parsed_args.portable_root}")
        else:
            args.append("--portable")
        # Finally, launch the application
        self._app.startup("kit", os.environ["CARB_APP_PATH"], args)

    def _setup_renderer(self, mode: str = "non-default"):
        """Reset render settings to those in config.

        Note:
            This should be used in case a new stage is opened and the desired config needs
            to be re-applied.

        Keyword Arguments:
            mode {str} -- Whether to setup RTX default or non-default settings. (default: {"non-default"})
        """
        # Define mode to configure settings into.
        if mode == "default":
            rtx_mode = "/rtx-defaults"
        else:
            rtx_mode = "/rtx"
        carb_settings = carb.settings.get_settings()
        # Set renderer mode.
        set_carb_setting(carb_settings, rtx_mode + "/rendermode", self.config["renderer"])
        # Raytrace mode settings
        set_carb_setting(carb_settings, rtx_mode + "/post/aa/op", self.config["anti_aliasing"])
        # Pathtrace mode settings
        set_carb_setting(carb_settings, rtx_mode + "/pathtracing/spp", self.config["samples_per_pixel_per_frame"])
        set_carb_setting(carb_settings, rtx_mode + "/pathtracing/totalSpp", self.config["samples_per_pixel_per_frame"])
        set_carb_setting(carb_settings, rtx_mode + "/pathtracing/clampSpp", self.config["samples_per_pixel_per_frame"])
        set_carb_setting(carb_settings, rtx_mode + "/pathtracing/maxBounces", self.config["max_bounces"])
        set_carb_setting(
            carb_settings,
            rtx_mode + "/pathtracing/maxSpecularAndTransmissionBounces",
            self.config["max_specular_transmission_bounces"],
        )
        set_carb_setting(carb_settings, rtx_mode + "/pathtracing/maxVolumeBounces", self.config["max_volume_bounces"])
        set_carb_setting(carb_settings, rtx_mode + "/pathtracing/optixDenoiser/enabled", self.config["denoiser"])
        set_carb_setting(
            carb_settings, rtx_mode + "/hydra/subdivision/refinementLevel", self.config["subdiv_refinement_level"]
        )

        # Experimental, forces kit to not render until all USD files are loaded
        set_carb_setting(carb_settings, rtx_mode + "/materialDb/syncLoads", self.config["sync_loads"])
        set_carb_setting(carb_settings, rtx_mode + "/hydra/materialSyncLoads", self.config["sync_loads"])
        set_carb_setting(carb_settings, "/omni.kit.plugin/syncUsdLoads", self.config["sync_loads"])

    def _prepare_ui(self):
        """Dock the windows in the UI if they exist."""
        # Method for docking a particular window to a location
        def dock_window(space, name, location):
            window = omni.ui.Workspace.get_window(name)
            if window and space:
                window.dock_in(space, location)
            return window

        # Acquire the main docking station
        main_dockspace = omni.ui.Workspace.get_window("DockSpace")
        # Acquire the docking space for viewport
        view = dock_window(main_dockspace, "Viewport", omni.ui.DockPosition.TOP)
        self._app.update()
        dock_window(view, "Console", omni.ui.DockPosition.BOTTOM)
        dock_window(view, "Main ToolBar", omni.ui.DockPosition.LEFT)
        self._app.update()
        # Acquire the docking window where `Stage` tab is present and add tabs
        render = dock_window(main_dockspace, "Render Settings", omni.ui.DockPosition.RIGHT)
        dock_window(render, "Stage", omni.ui.DockPosition.SAME)
        dock_window(render, "Layer", omni.ui.DockPosition.SAME)
        self._app.update()
        dock_window(render, "Property", omni.ui.DockPosition.BOTTOM)
        self._app.update()

    def close(self):
        """Close the running Omniverse Toolkit."""
        # check if exited already
        if not self._exiting:
            self._exiting = True
            # We are exiting but something is still loading, wait for it to load to avoid a deadlock
            # if self.is_loading():
            #     print_info("Waiting for USD resource operations to complete (this may take a few seconds)...")
            # while self.is_loading():
            #     self._app.update()
            # Shut down simulator.
            self._app.shutdown()
            self._framework.unload_all_plugins()
            # print_notify("Shutting down completed...")
