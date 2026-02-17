import isaacsim.core.utils.numpy.rotations as rot_utils
import numpy as np
from isaacsim.core.api import World
from isaacsim.core.api.objects import DynamicCuboid
from isaacsim.core.utils.stage import add_reference_to_stage
from isaacsim.sensors.camera import Camera
from isaacsim.storage.native import get_assets_root_path
from PIL import Image, ImageDraw

# Desired image resolution, camera intrinsics matrix, and distortion coefficients
# These values were selected to estimate distortion for the Realsense D455 camera, and
# will vary for each individual camera.
width, height = 1920, 1200
camera_matrix = [[455.8, 0.0, 943.8], [0.0, 454.7, 602.3], [0.0, 0.0, 1.0]]
distortion_coefficients = [0.05, 0.01, -0.003, -0.0005]

# Camera sensor size and optical path parameters. These parameters are not the part of the
# OpenCV camera model, but they are nessesary to simulate the depth of field effect.
#
# Note: To disable the depth of field effect, set the f_stop to 0.0. This is useful for debugging.
# Set pixel size (microns)
pixel_size = 3
# Set f-number, the ratio of the lens focal length to the diameter of the entrance pupil (unitless)
f_stop = 1.8
# Set focus distance (meters) - chosen as distance from camera to cube
focus_distance = 1.5

# Add a ground plane to the scene
usd_path = get_assets_root_path() + "/Isaac/Environments/Grid/default_environment.usd"
add_reference_to_stage(usd_path=usd_path, prim_path="/ground_plane")

# Add some cubes and a Camera to the scene
cube_1 = DynamicCuboid(
    prim_path="/new_cube_1",
    name="cube_1",
    position=np.array([0, 0, 0.5]),
    scale=np.array([1.0, 1.0, 1.0]),
    size=1.0,
    color=np.array([255, 0, 0]),
)

cube_2 = DynamicCuboid(
    prim_path="/new_cube_2",
    name="cube_2",
    position=np.array([2, 0, 0.5]),
    scale=np.array([1.0, 1.0, 1.0]),
    size=1.0,
    color=np.array([0, 255, 0]),
)

cube_3 = DynamicCuboid(
    prim_path="/new_cube_3",
    name="cube_3",
    position=np.array([0, 4, 1]),
    scale=np.array([2.0, 2.0, 2.0]),
    size=1.0,
    color=np.array([0, 0, 255]),
)

camera = Camera(
    prim_path="/World/camera",
    position=np.array([0.0, 0.0, 2.0]),  # 1 meter away from the side of the cube
    frequency=30,
    resolution=(width, height),
    orientation=rot_utils.euler_angles_to_quats(np.array([0, 90, 0]), degrees=True),
)
camera.initialize()

# Calculate the focal length and aperture size from the camera matrix
((fx, _, cx), (_, fy, cy), (_, _, _)) = camera_matrix  # fx, fy are in pixels, cx, cy are in pixels
horizontal_aperture = pixel_size * width * 1e-6  # convert to meters
vertical_aperture = pixel_size * height * 1e-6  # convert to meters
focal_length_x = pixel_size * fx * 1e-6  # convert to meters
focal_length_y = pixel_size * fy * 1e-6  # convert to meters
focal_length = (focal_length_x + focal_length_y) / 2  # convert to meters

# Set the camera parameters, note the unit conversion between Isaac Sim sensor and Kit
camera.set_focal_length(focal_length)
camera.set_focus_distance(focus_distance)
camera.set_lens_aperture(f_stop)
camera.set_horizontal_aperture(horizontal_aperture)
camera.set_vertical_aperture(vertical_aperture)

camera.set_clipping_range(0.05, 1.0e5)

# Set the distortion coefficients
camera.set_opencv_fisheye_properties(cx=cx, cy=cy, fx=fx, fy=fy, fisheye=distortion_coefficients)
