import os

from pxr import Plug

pluginsRoot = os.path.join(os.path.dirname(__file__), "../../../plugins")

Plug.Registry().RegisterPlugins(pluginsRoot + "/DrSchema/resources")
Plug.Registry().RegisterPlugins(pluginsRoot + "/RangeSensorSchema/resources")
Plug.Registry().RegisterPlugins(pluginsRoot + "/RobotEngineBridgeSchema/resources")
Plug.Registry().RegisterPlugins(pluginsRoot + "/RosBridgeSchema/resources")
