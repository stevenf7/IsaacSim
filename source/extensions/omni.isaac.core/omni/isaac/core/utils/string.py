# Copyright (c) 2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#


def find_unique_string_name(intitial_name, is_unique_fn):
    if is_unique_fn(intitial_name):
        return intitial_name
    iterator = 1
    result = intitial_name + "_" + str(iterator)
    while not is_unique_fn(result):
        result = intitial_name + "_" + str(iterator)
        iterator += 1
    return result
