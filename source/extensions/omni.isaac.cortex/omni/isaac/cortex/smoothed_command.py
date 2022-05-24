# Copyright (c) 2020-2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.

""" Tools for exponentially smoothing motion commands as they come in.

These tools are important for real-world execution. They ensure that discontinuities from discretely
changing motion commands are never directly sent to the underlying motion policies. They're smoothed
first. This allows motion policies whose evolution is smooth w.r.t. state to be smooth even given
discontinuities in commands.
"""

import numpy as np

import omni.isaac.cortex.math_util as math_util


# The default smoothing ciefficient used by the smoothed command. Higher values are more smooth.
SmoothedCommand_a = 0.95


class TargetAdapter(object):
    """ Abstract interface to a target.
    
    Different use cases might have different target data structures. The SmoothedCommand object
    expects the target to have the API characterized here.

    Note that the target does not need to explicitly derive from this interface. It just needs to
    have this API.
    """

    def get_position(self) -> np.array:
        """ Return the position target in robot base coordinates.
        """
        pass

    def has_rotation(self) -> bool:
        """ Returns true if the target has a rotation to it.
        """
        pass

    def get_rotation_matrix(self) -> np.array:
        """ Returns the target rotation matrix (if one exists). If has_rotation() returns true, this
        method should return the target rotation matrix in robot base coordinates. Otherwise, the
        behavior is undefined.
        """
        pass


class SmoothedCommand(object):
    """ Represents a smoothed command.
   
    The API includes:
    - reset(): Clear the current smoothed target data.
    - update(): Updating the data given a new target.

    A command consists of a position target, an optional rotation matrix target, and a posture
    config. The smoothed command is stored in members x (position), R (rotation matrix), q (posture
    config), and can be accessed from there. On first update of any given component, the component
    is set directly to the value provided. On subsequent updates the currently value is averaged
    with the new value, creating an exponentially weighted average of values received. If a
    particular component is never received (e.g. the posture config, or the rotation matrix) the
    corresponding member is never initialized and remains None.

    Rotation recursive averaging is done by averaging the matrices themselves then projecting using
    math_util.proj_R(), which converts the (invalid) rotation matrix to a quaternion, normalizes,
    then converts back to a matrix.

    If use_distance_based_smoothing_regulation is set to True (default) the degree of smoothing
    diminishes to a minimum value of 0.5 as the system approaches the target. This feature is
    optimized for discrete jumps in targets. Then a large jump is detected, the smoothing increase
    to the interpolation_alpha provided on initialization, but then decreases to the minimum value
    as it nears the target. Note that the distance between rotation matrices factors into the
    distance to target.
    """

    def __init__(self, interpolation_alpha=SmoothedCommand_a, use_distance_based_smoothing_regulation=True):
        """ Initialize to use interpolation_alpha as the alpha blender. Larger values mean higher
        smoothing. interpolation_alpha should be between 0 and 1; a good default (for use with 60hz
        updates) is given by SmoothedCommand_a.
        """
        self.x = None
        self.R = None
        self.q = None
        self.init_interpolation_alpha = interpolation_alpha
        self.use_distance_based_smoothing_regulation = use_distance_based_smoothing_regulation
        self.reset()

    def reset(self):
        """ Reset the smoother back to its initial state.
        """
        self.x = None
        self.R = None
        self.q = None

        self.interpolation_alpha = self.init_interpolation_alpha

    def update(self, target, posture_config, eff_x, eff_R):
        """ Update the smoothed target given the current command (target, posture_config) and the
        current end-effector frame (eff_{x,R}).

        Params:
        - target: A target object implementing the TargetAdapter API. (It need not have a rotational
          target.)
        - posture_config: The posture configuration for this command. None is valid.
        - eff_x: The position component of the current end-effector frame.
        - eff_R: The rotational component of the current end-effector frame.
        """
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
            self.R = math_util.proj_R(a * self.R + (1.0 - a) * R_curr)
        if self.q is not None and q_curr is not None:
            self.q = a * self.q + (1.0 - a) * q_curr
