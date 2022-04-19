# Copyright (c) 2018-2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#

# python
import typing
import os
import json
import asyncio
import carb
from collections import namedtuple

# omniverse
import omni.client
from omni.client._omniclient import Result, CopyBehavior


class Version(namedtuple("Version", "major minor patch")):
    def __new__(cls, s):
        return super().__new__(cls, *map(int, s.split(".")))

    def __repr__(self):
        return ".".join(map(str, self))


def create_folder(server: str, path: str) -> bool:
    """Create a folder on server

    Args:
        server (str): Name of Nucleus server
        path (str): Path to folder

    Returns:
        bool: True if folder is created successfully
    """
    carb.log_info("Create {} folder on {} Server".format(path, server))
    result = omni.client.create_folder("{}{}".format(server, path))
    if result == Result.OK:
        carb.log_info("Success: {} Server has {} folder created".format(server, path))
        return True
    else:
        carb.log_warn("Failure: Server {} not able to create {} folder".format(server, path))
        return False


def delete_folder(server: str, path: str) -> bool:
    """Remove folder and all of its contents

    Args:
        server (str): Name of Nucleus server
        path (str): Path to folder

    Returns:
        bool: True if folder is deleted successfully
    """
    carb.log_info("Cleaup {} folder on {} Server".format(path, server))
    result = omni.client.delete("{}{}".format(server, path))
    if result == Result.OK:
        carb.log_info("Success: {} Server has {} folder deleted".format(server, path))
        return True
    else:
        carb.log_warn("Failure: Server {} not able to delete {} folder".format(server, path))
        return False


async def _list_files(url: str) -> typing.Tuple[str, typing.List]:
    """List files under a URL

    Args:
        url (str): URL of Nucleus server with path to folder

    Returns:
        root (str): Root of URL of Nucleus server
        paths (typing.List): List of path to each file
    """
    root, paths = await _collect_files(url)
    return root, paths


async def download_assets_async(
    src: str,
    dst: str,
    progress_callback,
    concurrency: int = 3,
    copy_behaviour: omni.client._omniclient.CopyBehavior = CopyBehavior.OVERWRITE,
    copy_after_delete: bool = True,
    timeout: float = 300.0,
) -> omni.client._omniclient.Result:
    """Download assets from S3 bucket

    Args:
        src (str): URL of S3 bucket as source
        dst (str): URL of Nucleus server to copy assets to
        progress_callback: Callback function to keep track of progress of copy
        concurrency (int): Number of concurrent copy operations. Default value: 3
        copy_behaviour (omni.client._omniclient.CopyBehavior): Behavior if the destination exists. Default value: OVERWRITE
        copy_after_delete (bool): True if destination needs to be deleted before a copy. Default value: True
        timeout (float): Default value: 300 seconds

    Returns:
        Result (omni.client._omniclient.Result): Result of copy
    """
    # omni.client is a singleton, import locally to allow to run with multiprocessing
    import omni.client

    count = 0
    result = Result.ERROR

    if copy_after_delete and check_server(dst, ""):
        carb.log_info("Deleting existing folder {}".format(dst))
        delete_folder(dst, "")

    sem = asyncio.Semaphore(concurrency)
    carb.log_info("Listing {} ...".format(src))
    root_source, paths = await _list_files("{}".format(src))
    carb.log_info("Found {} files from {}".format(len(paths), root_source))

    for entry in reversed(paths):
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


def check_server(server: str, path: str) -> bool:
    """Check a specific server for a path

    Args:
        server (str): Name of Nucleus server
        path (str): Path to search

    Returns:
        bool: True if folder is found
    """
    carb.log_info("Testing {} Server for {} folder".format(server, path))
    result, _ = omni.client.stat("{}{}".format(server, path))
    if result == Result.OK:
        carb.log_info("Success: {} Server has {} folder".format(server, path))
        return True
    else:
        carb.log_warn("Failure: Server {} does not have {} folder".format(server, path))
        return False


async def check_server_async(server: str, path: str) -> bool:
    """Check a specific server for a path (asynchronous version).

    Args:
        server (str): Name of Nucleus server
        path (str): Path to search

    Returns:
        bool: True if folder is found
    """
    carb.log_info("Testing {} Server for {} folder".format(server, path))
    result, _ = await omni.client.stat_async("{}{}".format(server, path))
    if result == Result.OK:
        carb.log_info("Success: {} Server has {} folder".format(server, path))
        return True
    else:
        carb.log_warn("Failure: Server {} does not have {} folder".format(server, path))
        return False


async def find_nucleus_server_async(
    suffix: str = "/Isaac", timeout: float = 5.0
) -> typing.Tuple[omni.client.Result, str]:
    """Attempts to determine best Nucleus server to use based on existing savedServers setting and
    the default server specified in json config at "/persistent/isaac/nucleus/default". Call is blocking
    (asynchronous version)

    Args:
        suffix (str): Path to folder to search for. Default value: /Isaac
        timeout (float): Default value: 5 seconds

    Returns:
        omni.client.Result: OK if Nucleus server with suffix is found
        url (str): URL of found Nucleus
    """
    timeout_return = False
    default_server = carb.settings.get_settings().get("/persistent/isaac/nucleus/default")
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
            omni.client.sign_out(default_server)
            timeout_return = True
    carb.log_warn(
        '/persistent/isaac/nucleus/default not specified in json config or via --/persistent/isaac/nucleus/default="omniverse://my-nucleus-server" command line'
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
                omni.client.sign_out(default_server)
                timeout_return = True
        if potential_server:
            return Result.OK_NOT_YET_FOUND, potential_server
        if timeout_return:
            return Result.ERROR_CONNECTION, ""
        carb.log_warn("No saved server contains {} folder".format(suffix))
        return Result.ERROR_NOT_FOUND, ""
    else:
        if timeout_return:
            return Result.ERROR_CONNECTION, ""
        carb.log_warn("No saved servers")
        return Result.ERROR_NOT_FOUND, ""


async def check_assets_version_async(
    src: str, dst: str, dst_path: str, timeout: float = 5.0
) -> typing.Tuple[omni.client.Result, str]:
    """Attempts to determine Isaac assets version and check if there are updates.
    (asynchronous version)

    Args:
        src (str): URL of S3 bucket as source
        dst (str): URL of Nucleus server to copy assets to
        dst_path (str): Path of Nucleus server to copy assets to
        timeout (float): Default value: 5 seconds

    Returns:
        omni.client.Result: OK if Assets are up to date
        ver (str): Version of latest Isaac Sim assets
    """

    # omni.client is a singleton, import locally to allow to run with multiprocessing
    import omni.client

    ver_local = Version("0.0.0")
    ver_mount = Version("0.0.0")

    # Get local version
    carb.log_info(f"Looking at {dst}{dst_path}")
    try:
        result = await asyncio.wait_for(check_server_async(dst, dst_path), timeout=timeout)
        if result:
            result, entries = await asyncio.wait_for(omni.client.list_async(dst + dst_path), timeout=timeout)

            if result != omni.client.Result.OK:
                raise Exception(f"Failed to list entries for {dst}{dst_path}: {result}")

            for entry in entries:
                # carb.log_info(f"Files: {entry.relative_path}")
                if not entry.flags & omni.client.ItemFlags.CAN_HAVE_CHILDREN > 0:
                    try:
                        ver_local = Version(entry.relative_path)
                        break
                    except TypeError:
                        carb.log_warn(f"Unable to parse version file: {entry.relative_path}")
        else:
            result = await asyncio.wait_for(check_server_async(dst, "/"), timeout=timeout)
            if not result:
                carb.log_error("Error connecting to {}".format(dst))
                return Result.ERROR_CONNECTION, ""
    except asyncio.TimeoutError:
        carb.log_warn("Connection Timeout after {} seconds for {}".format(timeout, dst))
        return Result.ERROR_CONNECTION, ""
    except:
        carb.log_error("Error connecting to {}{}".format(dst, dst_path))
        return Result.ERROR_CONNECTION, ""

    # Get mount version
    carb.log_info(f"Looking at {src}")
    try:
        result, entries = await asyncio.wait_for(omni.client.list_async(src), timeout=10)

        if result != omni.client.Result.OK:
            carb.log_warn(f"Failed to list entries for {src}: {result}")

        for entry in entries:
            if not entry.flags & omni.client.ItemFlags.CAN_HAVE_CHILDREN > 0:
                try:
                    ver_mount = Version(entry.relative_path)
                except TypeError:
                    carb.log_warn(f"Unable to parse version file: {entry.relative_path}")

    except asyncio.TimeoutError:
        carb.log_warn("Connection Timeout after {} seconds for {}".format(timeout, src))
        return Result.ERROR_CONNECTION, ""

    # Compare versions
    carb.log_info(f"ver_local = {ver_local.major}.{ver_local.minor}.{ver_local.patch}")
    carb.log_info(f"ver_mount = {ver_mount.major}.{ver_mount.minor}.{ver_mount.patch}")

    if ver_mount > ver_local:
        carb.log_info(f"New version of Isaac Sim assets found: {ver_mount}")
        return Result.OK_NOT_YET_FOUND, ver_mount
    elif ver_mount == Version("0.0.0"):
        carb.log_warn("Error finding new version of Isaac Sim assets")
        return Result.ERROR_BAD_VERSION, ""
    else:
        return Result.OK, ver_mount


def build_server_list() -> typing.List:
    """Return list with all known servers to check

    Returns:
        all_servers (typing.List): List of servers found
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


def find_nucleus_server(suffix: str = "/Isaac") -> typing.Tuple[bool, str]:
    """Attempts to determine best Nucleus server to use based on existing savedServers setting and the
    default server specified in json config at "/persistent/isaac/nucleus/default". Call is blocking

    Args:
        suffix (str): Path to folder to search for. Default value: /Isaac

    Returns:
        bool: True if Nucleus server with suffix is found
        url (str): URL of found Nucleus
    """
    default_server = carb.settings.get_settings().get("/persistent/isaac/nucleus/default")
    if default_server:
        result = check_server(default_server, suffix)
        if result:
            return True, default_server
    carb.log_warn(
        '/persistent/isaac/nucleus/default not specified in json config or via --/persistent/isaac/nucleus/default="omniverse://my-nucleus-server" command line'
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


def get_server_path(suffix: str = "/Isaac") -> typing.Union[str, None]:
    """Tries to find a Nucleus server with specific path

    Args:
        suffix (str): Path to folder to search for. Default value: /Isaac

    Returns:
        url (str): URL of Nucleus server with path to folder.
        Returns None if Nucleus server not found.
    """
    result, server = find_nucleus_server(suffix)
    if result is False:
        carb.log_warn("Could not find Nucleus server with {} folder".format(suffix))
        return None
    return server + suffix


def get_assets_root_path() -> typing.Union[str, None]:
    """Tries to find the root path to the Isaac Sim assets on a Nucleus server

    Returns:
        url (str): URL of Nucleus server with root path to assets folder.
            Returns None if Nucleus server not found.
    """
    suffix = "/Isaac"
    result, server = find_nucleus_server(suffix)
    if result is False:
        carb.log_warn("Could not find Nucleus server with {} folder".format(suffix))
        return None
    return server + suffix


def get_assets_server() -> typing.Union[str, None]:
    """Tries to find a server with the Isaac Sim assets

    Returns:
        url (str): URL of Nucleus server with the Isaac Sim assets
            Returns None if Nucleus server not found.
    """
    suffix = "/Isaac"
    result, server = find_nucleus_server(suffix)
    if result is False:
        carb.log_warn("Could not find Nucleus server with {} folder".format(suffix))
        return None
    return server


async def _collect_files(url: str) -> typing.Tuple[str, typing.List]:
    """Collect files under a URL.

    Args:
        url (str): URL of Nucleus server with path to folder

    Returns:
        root (str): Root of URL of Nucleus server
        paths (typing.List): List of path to each file
    """
    paths = []

    if await is_dir_async(url):
        root = url + "/"
        paths.extend(await recursive_list_folder(root))
        return root, paths
    else:
        if await is_file_async(url):
            root = os.path.dirname(url)
            return root, [url]


async def is_dir_async(path: str) -> bool:
    """Check if path is a folder

    Args:
        path (str): Path to folder

    Returns:
        bool: True if path is a folder
    """
    result, folder = await asyncio.wait_for(omni.client.list_async(path), timeout=10)
    if result != omni.client.Result.OK:
        raise Exception(f"Failed to determine if {path} is a folder: {result}")
    return True if len(folder) > 0 else False


async def is_file_async(path: str) -> bool:
    """Check if path is a file

    Args:
        path (str): Path to file

    Returns:
        bool: True if path is a file
    """
    result, file = await asyncio.wait_for(omni.client.stat_async(path), timeout=10)
    if result != omni.client.Result.OK:
        raise Exception(f"Failed to determine if {path} is a file: {result}")
    return False if file.flags & omni.client.ItemFlags.CAN_HAVE_CHILDREN > 0 else True


def is_file(path: str) -> bool:
    """Check if path is a file

    Args:
        path (str): Path to file

    Returns:
        bool: True if path is a file
    """
    result, file = omni.client.stat(path)
    if result != omni.client.Result.OK:
        raise Exception(f"Failed to determine if {path} is a file: {result}")
    return False if file.flags & omni.client.ItemFlags.CAN_HAVE_CHILDREN > 0 else True


async def recursive_list_folder(path: str) -> typing.List:
    """Recursively list all files

    Args:
        path (str): Path to folder

    Returns:
        paths (typing.List): List of path to each file
    """
    paths = []
    files, dirs = await list_folder(path)
    paths.extend(files)

    tasks = []
    for dir in dirs:
        tasks.append(asyncio.create_task(recursive_list_folder(dir)))

    results = await asyncio.gather(*tasks)
    for result in results:
        paths.extend(result)

    return paths


async def list_folder(path: str) -> typing.Tuple[typing.List, typing.List]:
    """List files and sub-folders from root path

    Args:
        path (str): Path to root folder

    Raises:
        Exception: When unable to find files under the path.

    Returns:
        files (typing.List): List of path to each file
        dirs (typing.List): List of path to each sub-folder
    """
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
