#!/usr/bin/python3.6

# Copyright (c) 2018, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.

import sys
import os
import json

from pprint import pprint


class MergeRequest:

    def __init__(self, json_str=''):
        if(not len(json_str)):
            raise Exception("ATM I can bootstrap from JSON only")

        self.from_json(json_str)

    def from_json(self, json_str):
        parsed = json.loads(json_str)

        for k, v in parsed.items():
            self.__dict__[k] = v
