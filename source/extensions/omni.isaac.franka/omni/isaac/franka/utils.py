# Copyright (c) 2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#
import os


def get_franka_usd_path() -> str:
    """[summary]

    Returns:
        str: [description]
    """
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "../../../data/franka.usd")
