from isaacsim.sensors.camera import SingleViewDepthSensorAsset
from isaacsim.storage.native import get_assets_root_path

# Add Realsense D455 to the stage
asset_path = get_assets_root_path() + "/Isaac/Sensors/Intel/RealSense/rsd455.usd"
realsense_d455 = SingleViewDepthSensorAsset(prim_path="/World/realsense_d455", asset_path=asset_path)

# Initialize all depth sensor prims in the asset, creating render products
# attached to HydraTextures for each.
realsense_d455.initialize()

# Print prim paths for all available depth sensors in the asset
print(realsense_d455.get_all_depth_sensor_paths())

# Get a specific depth sensor by camera prim path
depth_sensor = realsense_d455.get_child_depth_sensor("/World/realsense_d455/RSD455/Camera_Pseudo_Depth")

# Attach an Annotator to the depth sensor
depth_sensor.attach_annotator("DepthSensorDistance")
