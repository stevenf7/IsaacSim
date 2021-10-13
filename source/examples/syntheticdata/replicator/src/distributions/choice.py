# Copyright (c) 2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.

import numpy as np
import os

from distributions import Distribution


class Choice(Distribution):
    """ For sampling from a list of elems. """

    def __init__(self, input, p=None, blacklist=None):
        """ Construct a Choice distribution. Process input to elem list. """

        # TODO: verify values
        self._input = input
        self._p = p
        self._blacklist = blacklist
        if self._p:
            self._p = np.array(self._p)
            self._p = self._p / np.sum(self._p)

        self._elems = self.process_input()

    def process_input(self):
        """ Process input into a list of elems, with blacklisted elems removed. """

        elems = self._process_input(self._input)
        if self._blacklist:
            blacklisted_elems = self._process_input(self._blacklist)

            elem_set = set(elems)
            for elem in blacklisted_elems:
                if elem in elem_set:
                    elems.remove(elem)

        return elems

    def _process_input(self, input):
        """ Process input into a list of elems. """

        elems = []
        if type(input) is str and input[-4:] == ".txt":
            input_file = input
            file_elems = self._parse_input_file(input_file)
            elems.extend(file_elems)
        elif type(input) is list:
            for elem in input:
                list_elems = self._process_input(elem)
                elems.extend(list_elems)
        else:
            elem = input
            if type(elem) is tuple:
                elem = np.array(elem)
            elems.append(input)

        return elems

    def _parse_input_file(self, input_file):
        """ Parse an input file into a list of elems. """

        if input_file.startswith("/"):
            input_file = input_file
        elif input_file.startswith("~"):
            input_file = os.path.join(Distribution.input_mount, input_file)
        else:
            # TODO: Make less fragile
            input_file = os.path.join(os.path.dirname(__file__), "../..", input_file)

        if not os.path.exists(input_file):
            raise ValueError("unable to open Choice file: {}".format(input_file))

        with open(input_file) as f:
            lines = f.readlines()
            lines = [line.strip() for line in lines]
            file_elems = []
            for elem in lines:
                if elem and not elem.startswith("#"):
                    try:
                        elem = eval(elem)
                    except Exception as e:
                        pass
                    if type(elem) is tuple:
                        elem = np.array(elem)
                    file_elems.append(elem)
            return file_elems

    def sample(self):
        """ Samples from the list of elems. """

        if self._elems:
            index = np.random.choice(len(self._elems), p=self._p)
            return self._elems[index]
        else:
            return None

    def get_elems(self):
        return self._elems

    def set_elems(self, elems):
        self._elems = elems
