# Copyright (c) 2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#


from typing import Callable, Tuple


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


def find_root_prim_path_from_regex(prim_path_regex: str) -> Tuple[str, int]:
    """
        Used to find the first prim above the regex pattern prim and its position.
    Args:
        prim_path_regex (str): full prim path including the regex pattern prim.

    Returns:
        Tuple[str, int]: First position is the prim path to the parent of the regex prim. 
                         Second position represents the level of the regex prim in the USD stage tree representation.
    """
    prim_paths_list = prim_path_regex.split("/")
    root_idx = None
    for prim_path_idx in range(len(prim_paths_list)):
        chars = set("[]*|^")
        if any((c in chars) for c in prim_paths_list[prim_path_idx]):
            root_idx = prim_path_idx
            break
    root_prim_path = None
    tree_level = None
    if root_idx is not None:
        root_prim_path = "/".join(prim_paths_list[:root_idx])
        tree_level = root_idx
    return root_prim_path, tree_level
