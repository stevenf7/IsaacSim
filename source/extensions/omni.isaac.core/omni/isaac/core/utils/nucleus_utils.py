# Copyright (c) 2018-2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#

import carb
import omni.client
from omni.client._omniclient import Result
import json
import asyncio


def check_server(server, suffix):
    """
    Check a specific server for a directory
    """
    carb.log_info("Testing {} Server for {} folder".format(server, suffix))
    result, entries = omni.client.stat("{}{}".format(server, suffix))
    if result == Result.OK:
        carb.log_info("Success: {} Server has {} folder".format(server, suffix))
        return True
    else:
        carb.log_warn("Failure: Server {} does not have {} folder".format(server, suffix))
        return False


async def check_server_async(server, suffix):
    """
    Check a specific server for a directory
    """
    carb.log_info("Testing {} Server for {} folder".format(server, suffix))
    result, entries = await omni.client.stat_async("{}{}".format(server, suffix))
    if result == Result.OK:
        carb.log_info("Success: {} Server has {} folder".format(server, suffix))
        return True
    else:
        carb.log_warn("Failure: Server {} does not have {} folder".format(server, suffix))
        return False


async def find_nucleus_server_async(suffix="/Isaac", timeout=5.0):
    """
    Async version of find_nucleus_server that has a timeout
    """
    default_server = carb.settings.get_settings().get("/isaac/nucleus/default")
    if default_server:
        try:
            result = await asyncio.wait_for(check_server_async(default_server, suffix), timeout=timeout)
            if result:
                return True, default_server
        except asyncio.TimeoutError:
            carb.log_warn("Connection Timeout after {} seconds for {}".format(timeout, default_server))
    carb.log_warn(
        '/isaac/nucleus/default not specified in json config or via --/isaac/nucleus/default="omniverse://my-nucleus-server" command line'
    )
    carb.log_warn("Attempting to locate server from previously saved servers...")
    all_servers = build_server_list()

    if len(all_servers):
        for server_name in all_servers:
            try:
                result = await asyncio.wait_for(check_server_async(server_name, suffix), timeout=timeout)
                if result:
                    return True, server_name
            except asyncio.TimeoutError:
                carb.log_warn("Connection Timeout after {} seconds for {}".format(timeout, default_server))
        carb.log_warn("No saved server contains {} folder".format(suffix))
        return False, ""
    else:
        carb.log_warn("No saved servers")
        return False, ""


def build_server_list():
    """
    Return list with all known servers to check
    """
    saved_servers = carb.settings.get_settings().get("/persistent/app/omniverse/savedServers")
    all_servers = []
    if saved_servers is not None:
        # print("savedServers", saved_servers)
        server_list = saved_servers.split(";")
        if len(server_list):
            for server in server_list:
                if len(server):
                    all_servers.append("omniverse://{}".format(server))
    else:
        carb.log_warn("/persistent/app/omniverse/savedServers setting not found")
    mounted_drives = carb.settings.get_settings().get_settings_dictionary("/persistent/app/omniverse/mountedDrives")

    if mounted_drives is not None:
        # print("mountedDrives", mounted_drives)
        mounted_dict = json.loads(mounted_drives.get_dict())
        for drive in mounted_dict.items():
            all_servers.append(drive[1])
    else:
        carb.log_warn("/persistent/app/omniverse/mountedDrives setting not found")
    return all_servers


def find_nucleus_server(suffix="/Isaac"):
    """
    Attempts to determine best nucleus server to use based on existing savedServers setting and the default server specied in json config at "/isaac/nucleus/default". Call is blocking
    """

    default_server = carb.settings.get_settings().get("/isaac/nucleus/default")
    if default_server:
        result = check_server(default_server, suffix)
        if result:
            return True, default_server
    carb.log_warn(
        '/isaac/nucleus/default not specified in json config or via --/isaac/nucleus/default="omniverse://my-nucleus-server" command line'
    )
    carb.log_warn("Attempting to locate server from previously saved servers...")
    all_servers = build_server_list()

    if len(all_servers):
        for server_name in all_servers:
            result = check_server(server_name, suffix)
            if result:
                return True, server_name
        carb.log_warn("No saved server contains {} folder".format(suffix))
        return False, ""
    else:
        carb.log_warn("No saved servers")
        return False, ""


def get_server_path(suffix="/Isaac"):
    """
    Tries to find a nucleus server for the given folder
    """
    result, nucleus_server = find_nucleus_server(suffix)
    if result is False:
        carb.log_warn("Could not find nucleus server with {} folder".format(suffix))
        return None
    return nucleus_server + suffix
