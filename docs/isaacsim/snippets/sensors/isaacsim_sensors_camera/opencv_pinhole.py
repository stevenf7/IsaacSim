import numpy as np
from isaacsim.core.experimental.objects import Cube
from isaacsim.core.utils.stage import add_reference_to_stage
from isaacsim.sensors.experimental.rtx import CameraSensor, RtxCamera
from isaacsim.storage.native import get_assets_root_path
from pxr import Gf

# Desired image resolution, camera intrinsics matrix, and distortion coefficients
# These values were selected to estimate distortion for the Realsense D455 camera, and
# will vary for each individual camera.
width, height = 1920, 1200
camera_matrix = [[958.8, 0.0, 957.8], [0.0, 956.7, 589.5], [0.0, 0.0, 1.0]]
distortion_coefficients = [0.14, -0.03, -0.0002, -0.00003, 0.009, 0.5, -0.07, 0.017]

# Distortion coefficient names for OpenCV pinhole (rational polynomial) model
pinhole_coeff_names = ["k1", "k2", "p1", "p2", "k3", "k4", "k5", "k6", "s1", "s2", "s3", "s4"]

# Add a ground plane to the scene
usd_path = get_assets_root_path() + "/Isaac/Environments/Grid/default_environment.usd"
add_reference_to_stage(usd_path=usd_path, prim_path="/ground_plane")

# Add some cubes to the scene
Cube("/World/cube_1", sizes=1.0, positions=np.array([0.0, 0.0, 0.5]), colors=[1, 0, 0])
Cube("/World/cube_2", sizes=1.0, positions=np.array([2.0, 0.0, 0.5]), colors=[0, 1, 0])
Cube("/World/cube_3", sizes=2.0, positions=np.array([0.0, 4.0, 1.0]), colors=[0, 0, 1])

# Extract intrinsic parameters
((fx, _, cx), (_, fy, cy), (_, _, _)) = camera_matrix

# Build distortion attributes
distortion_attrs = {
    f"omni:lensdistortion:opencvPinhole:{pinhole_coeff_names[i]}": distortion_coefficients[i]
    for i in range(len(distortion_coefficients))
}

# Create camera with OpenCV pinhole distortion schema
cam = RtxCamera(
    "/World/camera",
    schemas=["OmniLensDistortionOpenCvPinholeAPI"],
    attributes={
        "omni:lensdistortion:opencvPinhole:cx": cx,
        "omni:lensdistortion:opencvPinhole:cy": cy,
        "omni:lensdistortion:opencvPinhole:fx": fx,
        "omni:lensdistortion:opencvPinhole:fy": fy,
        "omni:lensdistortion:opencvPinhole:imageSize": Gf.Vec2i(width, height),
        **distortion_attrs,
    },
    positions=np.array([0.0, 0.0, 2.0]),
)
cam.prims[0].GetAttribute("omni:lensdistortion:model").Set("opencvPinhole")

# Create sensor and render
sensor = CameraSensor(cam, resolution=(height, width), annotators=["rgb"])
