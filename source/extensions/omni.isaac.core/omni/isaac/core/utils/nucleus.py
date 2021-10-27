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
from omni.client._omniclient import Result, CopyBehavior
import json
import asyncio
import os
import typing


def create_folder(server, suffix):
    """
    Create a folder on server
    """
    carb.log_info("Create {} folder on {} Server".format(suffix, server))
    result = omni.client.create_folder("{}{}".format(server, suffix))
    if result == Result.OK:
        carb.log_info("Success: {} Server has {} folder created".format(server, suffix))
        return True
    else:
        carb.log_warn("Failure: Server {} not able to create {} folder".format(server, suffix))
        return False


def cleanup_folder(server, suffix):
    """
    Remove folder
    """
    carb.log_info("Cleaup {} folder on {} Server".format(suffix, server))
    result = omni.client.delete("{}{}".format(server, suffix))
    if result == Result.OK:
        carb.log_info("Success: {} Server has {} folder deleted".format(server, suffix))
        return True
    else:
        carb.log_warn("Failure: Server {} not able to delete {} folder".format(server, suffix))
        return False


async def list_files(url):
    """
    List files
    """
    root_source, paths = await _collect_files(url)
    return root_source, paths


async def download_assets_async(
    src: str, dst: str, progress_callback, concurrency=3, copy_behaviour=CopyBehavior.OVERWRITE, timeout=300
):
    """
    Download assets from S3 bucket
    """
    # omni.client is a singleton, import locally to allow to run with multiprocessing
    import omni.client

    count = 0
    result = Result.ERROR

    sem = asyncio.Semaphore(concurrency)
    carb.log_info("Listing {} ...".format(src))
    root_source, paths = await list_files("{}".format(src))
    carb.log_info("Found {} files from {}".format(len(paths), root_source))

    for entry in paths:
        count += 1
        path = os.path.relpath(entry, root_source).replace("\\", "/")

        carb.log_info(
            "Downloading asset {} of {} from {}/{} to {}/{}".format(count, len(paths), root_source, path, dst, path)
        )
        async with sem:
            result = await asyncio.wait_for(
                omni.client.copy_async("{}/{}".format(root_source, path), "{}/{}".format(dst, path), copy_behaviour),
                timeout=timeout,
            )
        if result != Result.OK:
            raise Exception(f"Failed to copy {path} to {dst}: {result}")
        progress_callback(count, len(paths))

    return result


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
            carb.log_info("Checking {}{}".format(default_server, suffix))
            result = await asyncio.wait_for(check_server_async(default_server, suffix), timeout=timeout)
            if result:
                carb.log_info("{} folder found on {}".format(suffix, default_server))
                return Result.OK, default_server
            else:
                result = await asyncio.wait_for(check_server_async(default_server, "/"), timeout=timeout)
                if result:
                    carb.log_warn("Connected to {} but {} folder not found".format(default_server, suffix))
                    return Result.OK_NOT_YET_FOUND, default_server
        except asyncio.TimeoutError:
            carb.log_warn("Connection Timeout after {} seconds for {}".format(timeout, default_server))
    carb.log_warn(
        '/isaac/nucleus/default not specified in json config or via --/isaac/nucleus/default="omniverse://my-nucleus-server" command line'
    )
    carb.log_warn("Attempting to locate server from previously saved servers...")
    all_servers = build_server_list()
    potential_server = ""

    if len(all_servers):
        for server_name in all_servers:
            try:
                if server_name == default_server:
                    continue
                carb.log_info("Checking {}{}".format(server_name, suffix))
                result = await asyncio.wait_for(check_server_async(server_name, suffix), timeout=timeout)
                if result:
                    return Result.OK, server_name
                else:
                    result = await asyncio.wait_for(check_server_async(server_name, "/"), timeout=timeout)
                    if result:
                        carb.log_warn("Connected to {} but {} folder not found".format(server_name, suffix))
                        potential_server = server_name
            except asyncio.TimeoutError:
                carb.log_warn("Connection Timeout after {} seconds for {}".format(timeout, default_server))
        if potential_server:
            return Result.OK_NOT_YET_FOUND, potential_server
        carb.log_warn("No saved server contains {} folder".format(suffix))
        return Result.ERROR_NOT_FOUND, ""
    else:
        carb.log_warn("No saved servers")
        return Result.ERROR_NOT_FOUND, ""


def build_server_list():
    """
    Return list with all known servers to check
    """
    saved_servers = carb.settings.get_settings().get("/persistent/app/omniverse/savedServers")
    all_servers = []
    if saved_servers is not None:
        server_list = saved_servers.split(";")
        if len(server_list):
            for server in server_list:
                if len(server):
                    all_servers.append("omniverse://{}".format(server))
    else:
        carb.log_warn("/persistent/app/omniverse/savedServers setting not found")

    mounted_drives = carb.settings.get_settings().get_settings_dictionary("/persistent/app/omniverse/mountedDrives")

    if mounted_drives is not None:
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


async def _collect_files(source: str) -> typing.List:
    paths = []

    if await _is_dir(source):
        source = source + "/"
        paths.extend(await _recursive_walk(source))
        return source, paths
    else:
        if await _is_file(source):
            root_source = os.path.dirname(source)
            return root_source, [source]


async def _is_dir(path: str) -> bool:
    result, paths = await asyncio.wait_for(omni.client.list_async(path), timeout=10)
    if result != omni.client.Result.OK:
        raise Exception(f"Failed to determine if {path} is a file or directory: {result}")
    return True if len(paths) > 0 else False


async def _is_file(path: str) -> bool:
    result, entry = await asyncio.wait_for(omni.client.stat_async(path), timeout=10)
    if result != omni.client.Result.OK:
        raise Exception(f"Failed to determine if {path} is a file or directory: {result}")
    return False if entry.flags & omni.client.ItemFlags.CAN_HAVE_CHILDREN > 0 else True


async def _recursive_walk(path: str) -> typing.List:
    paths = []
    files, dirs = await _list(path)
    paths.extend(files)

    tasks = []
    for dir in dirs:
        tasks.append(asyncio.create_task(_recursive_walk(dir)))

    results = await asyncio.gather(*tasks)
    for result in results:
        paths.extend(result)

    return paths


async def _list(path: str) -> typing.Tuple[typing.List, typing.List]:
    # omni.client is a singleton, import locally to allow to run with multiprocessing
    import omni.client

    files = []
    dirs = []

    carb.log_info(f"Collecting files for {path}")
    result, entries = await asyncio.wait_for(omni.client.list_async(path), timeout=10)

    if result != omni.client.Result.OK:
        raise Exception(f"Failed to list entries for {path}: {result}")

    for entry in entries:
        full_path = omni.client.combine_urls(path, entry.relative_path)
        if entry.flags & omni.client.ItemFlags.CAN_HAVE_CHILDREN > 0:
            dirs.append(full_path + "/")
        else:
            carb.log_info(f"Enqueuing {full_path} for processing")
            files.append(full_path)

    return files, dirs
