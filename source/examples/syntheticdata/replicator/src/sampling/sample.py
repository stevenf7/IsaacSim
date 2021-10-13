# Copyright (c) 2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.

from output import Logger
from distributions import Distribution


LOGGER = Logger()


class Sampler:
    """ For managing parameter sampling. """

    # Static variable of parameter set
    params = None

    def __init__(self, *args):
        """ Construct a Sampler. Potentially set an associated group. """

        if len(args) == 1:
            self.group = args[0]
        else:
            self.group = None

    def sample(self, key, group=None):
        """ Sample a parameter. """

        if group is None:
            group = self.group

        if key.startswith("obj") or key.startswith("light") and group:
            param_set = self.params["groups"][group]
        else:
            param_set = self.params

        if key in param_set:
            val = param_set[key]
        else:
            print('Warning key "{}" in group "{}" not found in parameter set.'.format(key, group))
            return None

        if isinstance(val, Distribution):
            val = val.sample()

        LOGGER.write_parameter(key, val, group=group)
        return val
