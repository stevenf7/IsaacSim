from omni.isaac.core.utils.extensions import enable_extension

enable_extension("omni.isaac.debug_draw")

from omni.isaac.core.utils import stage, nucleus

assets_root_path = nucleus.get_assets_root_path()
stage.add_reference_to_stage(assets_root_path + "/Isaac/Environments/Simple_Warehouse/full_warehouse.usd", "/bg")

import omni
from pxr import Gf

_, sensor = omni.kit.commands.execute(
    "IsaacSensorCreateRtxLidar",
    path="/sensor",
    parent=None,
    config="Example_Solid_State",
    translation=(0, 0, 1.0),
    orientation=Gf.Quatd(0.5, 0.5, -0.5, -0.5),  # Gf.Quatd is w,i,j,k
)


from omni.isaac.core.utils.render_product import create_hydra_texture

_, render_product_path = create_hydra_texture([1, 1], sensor.GetPath().pathString)

from omni.syntheticdata import sensors

# Create the post process graph that publishes the render var
sensors.get_synthetic_data().activate_node_template("RtxLidar" + "DebugDrawPointCloud", 0, [render_product_path])
