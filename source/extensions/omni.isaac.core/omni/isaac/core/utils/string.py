# Copyright (c) 2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#


from typing import Callable


def find_unique_string_name(intitial_name: str, is_unique_fn: Callable[[str], bool]) -> str:
    """[summary]

    Args:
        intitial_name (str): [description]
        is_unique_fn (Callable[[str], bool]): [description]

    Returns:
        str: [description]
    """
    if is_unique_fn(intitial_name):
        return intitial_name
    iterator = 1
    result = intitial_name + "_" + str(iterator)
    while not is_unique_fn(result):
        result = intitial_name + "_" + str(iterator)
        iterator += 1
    return result
