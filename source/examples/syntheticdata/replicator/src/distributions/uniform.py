# Copyright (c) 2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.

import numpy as np

from distributions import Distribution


class Uniform(Distribution):
    """ For sampling uniformly from a continuous range. """

    def __init__(self, min_val: float, max_val: float):
        """ Constructs a Uniform distribution. """

        # TODO: verify values
        self._min_val = min_val
        self._max_val = max_val

    def sample(self):
        """ Samples from continuous range. """

        return np.random.uniform(self._min_val, self._max_val)
