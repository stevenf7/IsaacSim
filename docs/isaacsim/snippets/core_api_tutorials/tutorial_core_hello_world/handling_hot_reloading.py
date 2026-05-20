# -- Import Isaac sim packages -- #
import isaacsim.core.experimental.utils.stage as stage_utils
from isaacsim.examples.base.base_sample_experimental import BaseSample
from isaacsim.storage.native import get_assets_root_path

# -- End of import Isaac sim packages -- #


class HelloWorld(BaseSample):
    def __init__(self) -> None:
        super().__init__()

    # -- Set up scene -- #
    # This function is called to setup the assets in the scene for the first time
    def setup_scene(self):
        # Add ground plane directly to the stage
        ground_plane = stage_utils.add_reference_to_stage(
            usd_path=get_assets_root_path() + "/Isaac/Environments/Grid/default_environment.usd",
            path="/World/ground",
        )

    # -- End of set up scene -- #
