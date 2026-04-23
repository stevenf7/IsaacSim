# Pseudocode -- adapt axis remapping and quaternion reordering to your calibration toolkit.
import numpy as np
from isaacsim.sensors.experimental.rtx import RtxCamera

dX, dY, dZ = _, _, _  # Extrinsics translation vector from the calibration toolkit
rW, rX, rY, rZ = _, _, _, _  # Note the order of the rotation parameters, it depends on the toolkit

RtxCamera(
    "/rig/camera_color",
    positions=np.array([-dZ, dX, dY]),  # Translation in the local frame of the prim
    orientations=np.array([rW, -rZ, rX, rY]),  # Quaternion orientation (wxyz) in the world/local frame
    # (depends if translations or positions is specified)
)
