# Copyright (c) 2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.

import numpy as np

from distributions import Distribution


class Range(Distribution):
    """ For sampling from a range of integers. """

    def __init__(self, min_val: int, max_val: int):
        """ Constructs a Range distribution. """

        # TODO: verify values
        self._range = range(min_val, max_val + 1)

    def sample(self):
        """ Samples from discrete range. """

        return np.random.choice(self._range)
