# Copyright (c) 2018-2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#

import omni


def get_selected_path():
    selectedPrims = omni.usd.get_context().get_selection().get_selected_prim_paths()

    if len(selectedPrims) > 0:
        curr_prim = selectedPrims[-1]
    else:
        curr_prim = None
    return curr_prim
