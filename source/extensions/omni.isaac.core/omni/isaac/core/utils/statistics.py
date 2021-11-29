# Copyright (c) 2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#


def get_memory_stats() -> dict:
    """Returns dictionary with memory usage staticstics in MB for GPU and Host memory

    Returns:
        dict: dictionary with memory usage statistics. The "Total" key contains totals for each category
    """
    memory_usage = {}
    import os, psutil

    process = psutil.Process(os.getpid())
    memory_usage["Total"] = {}
    memory_usage["Total"]["System Memory"] = {
        "description": "Total System Memory / RAM used",
        "value": process.memory_info().rss * 1e-6,  # byte to mb
    }

    import omni.stats

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
