# SPDX-FileCopyrightText: Copyright (c) 2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os

from pxr import Plug

from .api import MOTION_PLANNING_API_NAME, MOTION_PLANNING_ENABLED_ATTR, apply_motion_planning_api


def _register_plugin_path(path: str) -> None:
    pluginfo_path = os.path.join(path, "plugInfo.json")
    if not os.path.exists(pluginfo_path):
        return

    try:
        import json

        with open(pluginfo_path, "r") as file_handle:
            lines = file_handle.readlines()
            json_lines = [line for line in lines if not line.strip().startswith("#")]
            json_content = "".join(json_lines)
            data = json.loads(json_content)

        plugin_names_to_register = set()
        if "Plugins" in data:
            for plugin_info in data["Plugins"]:
                if "Name" in plugin_info:
                    plugin_names_to_register.add(plugin_info["Name"])

        if not plugin_names_to_register:
            return

        registry = Plug.Registry()
        registered_plugin_names = {plugin.name for plugin in registry.GetAllPlugins()}
        if plugin_names_to_register.issubset(registered_plugin_names):
            return
    except Exception:
        pass

    Plug.Registry().RegisterPlugins(path)


def _register_plugins(ext_path: str) -> None:
    _register_plugin_path(os.path.join(ext_path, "usd", "schema", "isaac", "robot_motion_schema"))
    _register_plugin_path(os.path.join(ext_path, "robot_motion_schema"))


ext_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
_register_plugins(ext_path)

__all__ = [
    "MOTION_PLANNING_API_NAME",
    "MOTION_PLANNING_ENABLED_ATTR",
    "apply_motion_planning_api",
]
