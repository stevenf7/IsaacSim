import os
import sys
import time
import asyncio
import argparse

# omniverse
import carb
import omni.kit.app
import omni.kit
import omni.isaac.kit.globals as globals
from omni.isaac.kit.utils import set_carb_setting


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
        "sync_loads": False,
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
        experience (str): The config file used to launch the application. Must be specified
        headless (bool): Disable UI when running. Defaults to True
        active_gpu (int): Specify the GPU to use when running, set to None to use default value which is usually the first gpu, default is None
        sync_loads (bool): When enabled, will pause rendering until all assets are loaded. Defaults to False
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

    def __init__(self, config: dict = None, experience: str = ""):
        # Initialize variables
        globals.LAUNCHED_FROM_TERMINAL = False

        # Override settings from input config
        self.config = self.DEFAULT_LAUNCHER_CONFIG
        if experience == "":
            experience = f'{os.environ["EXP_PATH"]}/omni.isaac.sim.python.kit'
        self.config.update({"experience": experience})
        if config is not None:
            self.config.update(config)

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
        # once app starts, we can set settings
        self._extension_manager = omni.kit.app.get_app().get_extension_manager()
        self._carb_settings = carb.settings.get_settings()
        # Set rtx-default renderder settings
        self._setup_renderer(mode="default")
        # Set rtx settings renderer settings
        self._setup_renderer(mode="non-default")

        set_carb_setting(self._carb_settings, "/persistent/simulation/defaultMetersPerUnit", 1.0)
        new_stage_task = asyncio.ensure_future(omni.usd.get_context().new_stage_async())

        print("Simulation App Starting")
        while not new_stage_task.done():
            # This sleep prevents a deadlock in certain cases.
            time.sleep(0.001)
            self._app.update()

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

    def _start_app(self):
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

    def _prepare_ui(self):
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

    def close(self):
        """Close the running Omniverse Toolkit."""
        # check if exited already
        if not self._exiting:
            self._exiting = True
            print("Shutting Down Simulation App...")
            # We are exisitng but something is still loading, wait for it to load to avoid a deadlock
            if self.is_loading:
                print("   Waiting for USD resource operations to complete (this may take a few seconds)")
            while self.is_loading:
                self._app.update()
            self._app.shutdown()
            self._framework.unload_all_plugins()
            print("Simulation App Shutdown Completed...")

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

    @property
    def app(self) -> omni.kit.app.IApp:
        """
            omni.kit.app.IApp: omniverse kit application object
        """
        return self._app

    @property
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

    @property
    def is_exiting(self) -> bool:
        """
            bool: True if close() was called previously, False otherwise
        """
        return self._exiting
