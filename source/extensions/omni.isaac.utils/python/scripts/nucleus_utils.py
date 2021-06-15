import carb
import omni.client
from omni.client._omniclient import Result
import json


def find_nucleus_server(suffix="/Isaac"):
    """
    Attempts to determine best nucleus server to use based on existing savedServers setting and the default server specied in json config at "/isaac/nucleus/default"
    """

    default_server = carb.settings.get_settings().get("/isaac/nucleus/default")
    if default_server:
        result, entries = omni.client.list("{}{}".format(default_server, suffix))
        if result == Result.OK:
            carb.log_info("Success: {} Server has {} folder".format(default_server, suffix))
            return True, default_server
        else:
            carb.log_warn("default server {} does not have {} folder".format(default_server, suffix))
    carb.log_warn(
        '/isaac/nucleus/default not specified in json config or via --/isaac/nucleus/default="omniverse://my-nucleus-server" command line'
    )
    carb.log_warn("Attempting to locate server from previously saved servers...")

    saved_servers = carb.settings.get_settings().get("/persistent/app/omniverse/savedServers")
    all_servers = []
    if saved_servers is not None:
        # print("savedServers", saved_servers)
        server_list = saved_servers.split(";")
        if len(server_list):
            for server in server_list:
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

    if len(all_servers):
        for server_name in all_servers:
            carb.log_info("Testing {} Server for {} folder".format(server_name, suffix))
            result, entries = omni.client.list("{}{}".format(server_name, suffix))
            if result == Result.OK:
                carb.log_warn("Success: {} Server has {} folder".format(server_name, suffix))
                return True, server_name
            else:
                carb.log_warn("Server {} does not have {} folder".format(server_name, suffix))
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
        carb.log_error("Could not find nucleus server with {} folder".format(suffix))
        return None
    return nucleus_server + suffix
