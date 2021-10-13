# Copyright (c) 2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.

import numpy as np

from distributions import Choice


class Walk(Choice):
    """ For sampling from a list of elems without replacement. """

    def __init__(self, input, ordered=True):
        """ Constructs a Walk distribution. """

        super().__init__(input)
        # TODO: verify input
        self._ordered = ordered
        self._completed = False
        self._index = 0
        self._num_sampled = 0

        if not self._ordered:
            self._sampled_indices = list(range(self.length()))

    def sample(self):
        """ Samples from list of elems and updates the index tracker. """

        if self._ordered:
            self._index %= self.length()
            sample = self._elems[self._index]
            self._index += 1
        else:
            if len(self._sampled_indices) == 0:
                self._sampled_indices = list(range(self.length()))
            self._index = np.choice(self._sampled_indices)
            self._sampled_indices.remove(self._index)
            sample = self._elems[self._index]
        self._num_sampled += 1

        # print("walking with sample: {}, index: {}".format(sample, self._index))

        return sample

    def length(self):
        return len(self._elems)
