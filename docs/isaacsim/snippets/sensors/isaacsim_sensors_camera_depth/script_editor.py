from isaacsim.sensors.experimental.rtx import RtxCamera, SingleViewDepthCameraSensor
from isaacsim.storage.native import get_assets_root_path

assets_root_path = get_assets_root_path()

# Load the Realsense D455 depth camera asset as a USD reference.
# RtxCamera.create() discovers the Camera prim inside the asset automatically.
cam = RtxCamera.create(
    "/World/D455",
    usd_path=assets_root_path + "/Isaac/Sensors/RealSense/D455/rsd455.usd",
)

# Wrap with SingleViewDepthCameraSensor. Depth sensor attributes (baseline,
# focal length, noise, etc.) are automatically copied from the RenderProduct
# prims already embedded in the asset.
sensor = SingleViewDepthCameraSensor(
    cam,
    resolution=(720, 1280),
    annotators=["depth_sensor_distance"],
)
sensor.set_enabled_post_processing(True)
