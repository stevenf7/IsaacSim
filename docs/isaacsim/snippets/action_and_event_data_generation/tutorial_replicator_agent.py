"""
Minimal IRA example: SimulationApp setup, load config, setup simulation, generate data.
"""

import os
import tempfile

from isaacsim import SimulationApp

# Start the application
simulation_app = SimulationApp({"headless": True})

# Get the utility to enable extensions
from isaacsim.core.utils.extensions import enable_extension

# Enable the IRA extension
enable_extension("isaacsim.replicator.agent.core")
simulation_app.update()

DEFAULT_CONFIG = """
isaacsim.replicator.agent:
  version: 1.1.0
  environment:
    base_stage_asset_path: "Isaac/Environments/Simple_Warehouse/full_warehouse.usd"
"""


def _get_config_path() -> str:
    """Return config path; create a temp default config file if config_path is None."""
    content = DEFAULT_CONFIG.strip()
    fd, path = tempfile.mkstemp(suffix=".yaml", prefix="ira_default_config_")
    try:
        with os.fdopen(fd, "w") as f:
            f.write(content)
        return path
    except Exception:
        os.close(fd)
        raise


async def run_ira_data_generation(run_data_generation: bool = False):
    from isaacsim.replicator.agent.core import api as IRA

    # IRA: load config
    config_path = _get_config_path()
    result = IRA.load_config_file(config_path)
    if not result:
        raise RuntimeError(f"Failed to load IRA config: {config_path}")

    # IRA: get config, you can modify the config here
    config = IRA.get_config_file()
    IRA.set_config(config)

    # IRA: setup simulation
    await IRA.setup_simulation()

    # Allow a few frames for scene to settle
    import omni.kit.app

    app = omni.kit.app.get_app()
    for _ in range(10):
        await app.next_update_async()

    # IRA: generate data (only when run_data_generation is True)
    if run_data_generation:
        await IRA.start_data_generation_async(will_wait_until_complete=True)


from omni.kit.async_engine import run_coroutine

task = run_coroutine(run_ira_data_generation(run_data_generation=False))
while not task.done():
    simulation_app.update()
