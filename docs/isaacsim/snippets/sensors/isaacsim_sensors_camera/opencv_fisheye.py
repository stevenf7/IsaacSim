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
camera_matrix = [[455.8, 0.0, 943.8], [0.0, 454.7, 602.3], [0.0, 0.0, 1.0]]
distortion_coefficients = [0.05, 0.01, -0.003, -0.0005]

# Add a ground plane to the scene
usd_path = get_assets_root_path() + "/Isaac/Environments/Grid/default_environment.usd"
add_reference_to_stage(usd_path=usd_path, prim_path="/ground_plane")

# Add some cubes to the scene
Cube("/World/cube_1", sizes=1.0, positions=np.array([0.0, 0.0, 0.5]), colors=[1, 0, 0])
Cube("/World/cube_2", sizes=1.0, positions=np.array([2.0, 0.0, 0.5]), colors=[0, 1, 0])
Cube("/World/cube_3", sizes=2.0, positions=np.array([0.0, 4.0, 1.0]), colors=[0, 0, 1])

# Extract intrinsic parameters
((fx, _, cx), (_, fy, cy), (_, _, _)) = camera_matrix

# Create camera with OpenCV fisheye distortion schema
cam = RtxCamera(
    "/World/camera",
    schemas=["OmniLensDistortionOpenCvFisheyeAPI"],
    attributes={
        "omni:lensdistortion:opencvFisheye:cx": cx,
        "omni:lensdistortion:opencvFisheye:cy": cy,
        "omni:lensdistortion:opencvFisheye:fx": fx,
        "omni:lensdistortion:opencvFisheye:fy": fy,
        "omni:lensdistortion:opencvFisheye:k1": distortion_coefficients[0],
        "omni:lensdistortion:opencvFisheye:k2": distortion_coefficients[1],
        "omni:lensdistortion:opencvFisheye:k3": distortion_coefficients[2],
        "omni:lensdistortion:opencvFisheye:k4": distortion_coefficients[3],
        "omni:lensdistortion:opencvFisheye:imageSize": Gf.Vec2i(width, height),
    },
    positions=np.array([0.0, 0.0, 2.0]),
)
cam.prims[0].GetAttribute("omni:lensdistortion:model").Set("opencvFisheye")

# Create sensor and render
sensor = CameraSensor(cam, resolution=(height, width), annotators=["rgb"])
