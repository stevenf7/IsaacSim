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


def get_teamcity_version():
    return(os.getenv('TEAMCITY_VERSION', None))


def in_teamcity():
    return(get_teamcity_version() is not None)
