import isaacsim.core.utils.numpy.rotations as rot_utils  # convenience functions for quaternion operations
import numpy as np

dX, dY, dZ = _, _, _  # Extrinsics translation vector from the calibration toolkit
rW, rX, rY, rZ = _, _, _, _  # Note the order of the rotation parameters, it depends on the toolkit

Camera(
    prim_path="/rig/camera_color",
    position=np.array([-dZ, dX, dY]),  # Note, translation in the local frame of the prim
    orientation=np.array([rW, -rZ, rX, rY]),  # quaternion orientation in the world/ local frame of the prim
    # (depends if translation or position is specified)
)
