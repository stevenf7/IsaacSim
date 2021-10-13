# Copyright (c) 2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.

import numpy as np


class GenerateDisparity:
    """ For converting stereo depth maps to stereo disparity maps. """

    def __init__(self, depth1, depth2, fx, fy, cx, cy, baseline):
        """ Constructing GenerateDisparity and computing disparity maps. """

        self.depth1 = np.array(depth1, dtype=np.float32)
        self.depth2 = np.array(depth2, dtype=np.float32)
        self.fx = fx
        self.fy = fy
        self.cx = cx
        self.cy = cy
        self.baseline = baseline

        self.disp_l, self.disp_r = self.compute_disparity()

    def get_disp(self):
        return self.disp_l, self.disp_r

    def compute_disparity(self):
        """ Computes a disparity map from left and right depth maps. """

        if not (isinstance(self.depth1, np.ndarray) and len(self.depth1.shape) == 2) and not (
            isinstance(self.depth2, np.ndarray) and isinstance((self.depth2, np.ndarray))
        ):
            raise TypeError("Depth maps should be a 2-dimensional ndarrays")

        # List all valid depths in the depth map
        (yi, xi) = np.nonzero(np.invert(np.isnan(self.depth1)))
        depths1 = self.depth1[yi, xi]
        depth2 = self.depth2[yi, xi]
        depth = {"left": depths1, "right": depth2}

        # Start from left image, backproject to 3D world
        X_right_est = self.backproject(xi, depth["left"])
        # Add the baseline to 3D world position
        X_right_est += self.baseline
        # Project to the right image domain
        x_lr_pt = self.project(X_right_est, depth["left"])
        # Compute disparity only the x-axis only since the left and right images are rectified
        disp_lr = x_lr_pt - xi

        # Repeat the same above for right to left image
        X_left_est = self.backproject(xi, depth["right"])
        X_left_est -= self.baseline
        x_rl_pt = self.project(X_left_est, depth["right"])
        disp_rl = xi - x_rl_pt

        # Use numpy vectorization to get pixel coordinates
        disp_l, disp_r = np.zeros(self.depth1.shape), np.zeros(self.depth2.shape)

        disp_l[yi, xi] = np.abs(disp_lr)
        disp_r[yi, xi] = np.abs(disp_rl)

        disp_l = np.float32(disp_l)
        disp_r = np.float32(disp_r)

        return disp_l, disp_r

    def project(self, X, Z):
        """ Projects from real world to camera. """

        return self.cx + (X / Z * self.fx)

    def backproject(self, x, depths):
        """ Projects point x to the real world point. """

        X = (x - self.cx) * (depths / self.fx)
        return X
