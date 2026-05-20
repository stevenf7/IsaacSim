# -- Begin importing Isaac packages -- #
import carb
import isaacsim.core.experimental.utils.stage as stage_utils
from isaacsim.core.experimental.prims import Articulation
from isaacsim.examples.base.base_sample_experimental import BaseSample
from isaacsim.storage.native import get_assets_root_path

# -- End of importing Isaac packages -- #


class HelloWorld(BaseSample):
    def __init__(self) -> None:
        super().__init__()

    def setup_scene(self):
        # Add ground plane
        ground_plane = stage_utils.add_reference_to_stage(
            usd_path=get_assets_root_path() + "/Isaac/Environments/Grid/default_environment.usd",
            path="/World/ground",
        )

        # Get the assets root path from the Nucleus server
        assets_root_path = get_assets_root_path()
        if assets_root_path is None:
            carb.log_error("Could not find nucleus server with /Isaac folder")
            return

        # -- Begin adding Jetbot -- #
        # Add the Jetbot robot to the stage
        asset_path = assets_root_path + "/Isaac/Robots/NVIDIA/Jetbot/jetbot.usd"
        stage_utils.add_reference_to_stage(usd_path=asset_path, path="/World/Fancy_Robot")
        # -- End of adding Jetbot -- #

    async def setup_post_load(self):
        # -- Begin articulation -- #
        # Wrap the Jetbot with the Articulation class for control
        self._jetbot = Articulation("/World/Fancy_Robot")
        # -- End of articulation -- #

        # Print info about the Jetbot
        print("Number of DOFs: " + str(self._jetbot.num_dofs))
        print("DOF names: " + str(self._jetbot.dof_names))
        print("Joint Positions: " + str(self._jetbot.get_dof_positions().numpy()))
