import omni.usd
import pxr
import usd.schema.isaac.robot_schema as rs
from pxr import Sdf, Usd, UsdGeom

stage = omni.usd.get_context().get_stage()
robot_asset_path = "/".join(stage.GetRootLayer().identifier.split("/")[:-1])  # Get the asset path from the stage
robot_asset = ".".join(
    stage.GetRootLayer().identifier.split("/")[-1].split(".")[:-1]
)  # Get the asset name from the stage
schema_asset = f"configuration/{robot_asset}_robot_schema.usda"
edit_layer = Sdf.Layer.FindOrOpen(f"{robot_asset_path}/{schema_asset}")
if not edit_layer:
    edit_layer = Sdf.Layer.CreateNew(f"{robot_asset_path}/{schema_asset}")
# Add sublayer to the stage, but as a relative path, only if not already present
if schema_asset not in stage.GetRootLayer().subLayerPaths:
    stage.GetRootLayer().subLayerPaths.append(schema_asset)
# Make all edits in the edit layer
with pxr.Usd.EditContext(stage, edit_layer):

    default_prim = stage.GetDefaultPrim()

    # Apply the Robot API to the default prim, and auto-populate the Links and Joints lists
    rs.ApplyRobotAPI(default_prim)


edit_layer.Save()
stage.Save()
