import carb
import omni.client
from omni.client._omniclient import Result


def find_nucleus_server(suffix="/Isaac"):
    """
    Attempts to determine best nucleus server to use based on existing savedServers setting and the default server specied in json config at "/isaac/nucleus/default"
    """

    default_server = omni.kit.settings.get_settings_interface().get("/isaac/nucleus/default")
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

    saved_servers = omni.kit.settings.get_settings_interface().get("/persistent/app/omniverse/savedServers")

    if saved_servers:
        server_list = saved_servers.split(";")
        if len(server_list):
            for server in server_list:
                server_name = "omniverse://{}".format(server)
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
            carb.log_warn("No saved servers in /persistent/app/omniverse/savedServers setting")
            return False, ""
    else:
        carb.log_warn("/persistent/app/omniverse/savedServers setting not found")
        return False, ""


def get_server_path(suffix="/Isaac"):
    result, nucleus_server = find_nucleus_server(suffix)
    if result is False:
        carb.log_error("Could not find nucleus server with {} folder".format(suffix))
        return None
    return nucleus_server + suffix
