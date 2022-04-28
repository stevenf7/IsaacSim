# Copyright (c) 2020-2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.

import numpy as np

SmoothedCommand_a = 0.95


class TargetAdapter(object):
    def get_position(self) -> np.array:
        pass

    def has_rotation(self) -> bool:
        pass

    def get_rotation_matrix(self) -> np.array:
        pass


class SmoothedCommand(object):
    def __init__(
        self, interpolation_alpha=SmoothedCommand_a, alpha_diminish=None, use_distance_based_smoothing_regulation=True
    ):
        self.x = None
        self.R = None
        self.q = None
        self.init_interpolation_alpha = interpolation_alpha
        self.init_alpha_diminish = alpha_diminish
        self.use_distance_based_smoothing_regulation = use_distance_based_smoothing_regulation
        self.reset()

    def reset(self):
        self.x = None
        self.R = None
        self.q = None

        self.interpolation_alpha = self.init_interpolation_alpha
        self.alpha_diminish = self.init_alpha_diminish

    def update(self, target, posture_config, eff_x, eff_R):
        x_curr = target.get_position()
        R_curr = None
        if target.has_rotation():
            R_curr = target.get_rotation_matrix()
        q_curr = None
        if posture_config is not None:
            q_curr = np.array(posture_config)

        if self.x is None:
            self.x = eff_x
        if self.R is None:
            self.R = eff_R
        if self.q is None:
            self.q = q_curr

        # Clear the R if there's no rotation command. But don't do the same for the posture config.
        # Always keep around the previous posture config.
        if R_curr is None:
            self.R = None

        if self.use_distance_based_smoothing_regulation:
            d = np.linalg.norm([eff_x - x_curr])
            if self.R is not None:
                d2 = np.linalg.norm([eff_R - self.R]) * 1.0
                d = max(d, d2)
            std_dev = 0.05
            scalar = 1.0 - np.exp(-0.5 * (d / std_dev) ** 2)
            alpha_min = 0.5
            a = scalar * self.interpolation_alpha + (1.0 - scalar) * alpha_min
        else:
            a = self.interpolation_alpha

        self.x = a * self.x + (1.0 - a) * x_curr
        if self.R is not None and R_curr is not None:
            self.R = a * self.R + (1.0 - a) * R_curr
        if self.q is not None and q_curr is not None:
            self.q = a * self.q + (1.0 - a) * q_curr

        if self.alpha_diminish is not None:
            self.interpolation_alpha *= self.alpha_diminish


if __name__ == "__main__":
    print("main function")
