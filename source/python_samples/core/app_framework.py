import os, sys

import carb
import omni.kit.app
import asyncio

# Simple example showing the minimal setup to run omniverse app from python


class PythonApp:
    def __init__(self):
        # Load app plugin
        self.framework = carb.get_framework()
        self.framework.load_plugins(
            loaded_file_wildcards=["omni.kit.app.plugin"],
            search_paths=[os.path.abspath(f'{os.environ["CARB_APP_PATH"]}/plugins')],
        )
        self.app = omni.kit.app.get_app()

        # Path to where kit was built to
        app_root = os.environ["CARB_APP_PATH"]

        # Inject experience config:
        sys.argv.insert(1, f'{os.environ["EXP_PATH"]}/isaac-sim.python.kit')

        # Add paths to extensions
        sys.argv.append(f'--/app/extensions/folders2/0="{os.path.abspath(os.environ["CARB_APP_PATH"])}/exts"')
        sys.argv.append(f'--/app/extensions/folders2/1="{os.path.abspath(os.environ["CARB_APP_PATH"])}/extsPhysics"')
        sys.argv.append(f'--/app/extensions/folders2/2="{os.path.abspath(os.environ["ISAAC_PATH"])}/exts"')
        # Run headless
        sys.argv.append("--no-window")

        # Start the default Kit Experience App
        self.app.startup("kit", app_root, sys.argv)

    def shutdown(self):
        # Shutdown
        self.app.shutdown()
        self.framework.unload_all_plugins()
        print("Shutdown complete")


if __name__ == "__main__":
    kit = PythonApp()

    # Do something, in this case we wait for stage to open and then exit
    stage_task = asyncio.ensure_future(omni.usd.get_context().new_stage_async())

    while not stage_task.done():
        kit.app.update()

    kit.shutdown()
