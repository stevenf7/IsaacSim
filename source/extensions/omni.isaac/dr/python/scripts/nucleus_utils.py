import carb
import omni.client
from omni.client._omniclient import Result


def find_nucleus_server():
    """
    Attempts to determine best nucleus server to use based on existing savedServers setting and the default server specied in json config at "/isaac/nucleus/default"
    """

    default_server = omni.kit.settings.get_settings_interface().get("/isaac/nucleus/default")
    if default_server:
        result, entries = omni.client.list("{}/Isaac".format(default_server))
        if result == Result.OK:
            carb.log_info("Success: {} Server has /Isaac folder".format(default_server))
            return True, default_server
        else:
            carb.log_warn("default server {} does not have /Isaac folder".format(default_server))
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
                carb.log_info("Testing {} Server for /Isaac folder".format(server_name))
                result, entries = omni.client.list("{}/Isaac".format(server_name))
                if result == Result.OK:
                    carb.log_warn("Success: {} Server has /Isaac folder".format(server_name))
                    return True, server_name
                else:
                    carb.log_warn("Server {} does not have /Isaac folder".format(server_name))
            carb.log_warn("No saved server contains /Isaac folder")
            return False, ""
        else:
            carb.log_warn("No saved servers in /persistent/app/omniverse/savedServers setting")
            return False, ""
    else:
        carb.log_warn("/persistent/app/omniverse/savedServers setting not found")
        return False, ""
