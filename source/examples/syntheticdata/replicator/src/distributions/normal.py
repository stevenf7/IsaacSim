# Copyright (c) 2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.

import math
import numpy as np

from distributions import Distribution


class Normal(Distribution):
    """ For sampling a Gaussian. """

    def __init__(self, mean: float, var: float, min: float = None, max: float = None):
        """ Constructs of Normal distribution. """

        # TODO: verify values
        self._mean = mean
        self._std_dev = math.sqrt(var)
        self._min_val = min
        self._max_val = max

    def sample(self):
        """ Samples from Gaussian. """

        sample = np.random.normal(self._mean, self._std_dev)
        if self._min_val != None or self._max_val != None:
            sample = np.clip(sample, a_min=self._min_val, a_max=self._max_val)
        return sample
