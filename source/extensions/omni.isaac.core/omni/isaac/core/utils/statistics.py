# Copyright (c) 2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#

# python
import os
import copy


def get_memory_stats() -> dict:
    """Returns dictionary with memory usage staticstics in MB for GPU and Host memory

    Returns:
        dict: A dictionary with memory usage statistics. The "Total" key contains totals for each category
    """
    # Note: Need to import here (reason not clear).
    import psutil
    import omni.stats

    memory_usage = {}

    process = psutil.Process(os.getpid())
    memory_usage["Total"] = {}
    memory_usage["Total"]["System Memory"] = {
        "description": "Total System Memory / RAM used",
        "value": process.memory_info().rss * 1e-6,  # byte to mb
    }

    stats_interface = omni.stats.get_stats_interface()
    scopes = stats_interface.get_scopes()
    for scope in scopes:
        stat_dict = {}
        scope_id = scope["scopeId"]
        stats = stats_interface.get_stats(scope_id)
        total = 0
        for s in stats:
            stat_dict[s["name"]] = {"description": s["description"], "value": s["value"]}
            total += s["value"]

        memory_usage[scope["name"]] = stat_dict
        memory_usage["Total"][scope["name"]] = {"description": f'Total for {scope["name"]} category', "value": total}

    return memory_usage


def get_memory_delta(start: dict, end: dict) -> dict:
    """Computes the difference between two memory reports computed using get_memory_stats

    Args:
        start (dict): get_memory_stats from point A in time
        end (dict): get_memory_stats from point B in time

    Returns:
        dict: returns memory report for B - A
    """
    # Create a copy so we don't have to start from scratch
    result = copy.deepcopy(start)
    for k, v in start.items():
        d_start = v
        d_end = end[k]
        d_result = result[k]

        for kk, vv in d_start.items():
            i_start = vv
            i_end = d_end[kk]
            i_result = d_result[kk]
            i_result["value"] = i_end["value"] - i_start["value"]

    return result
