# SPDX-FileCopyrightText: Copyright (c) 2018-2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
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

"""ROS 2 UI extension entry point."""

import omni.ext
from isaacsim.ros2.ui.og_shortcuts_menu import Ros2ShortcutsMenuExtension


class Extension(omni.ext.IExt):
    """Extension entry point for the ROS 2 UI shortcuts menu."""

    def on_startup(self, ext_id):
        """Initialize the extension."""
        print("ROS2 UI extension startup")

        self.shortcuts_menu = Ros2ShortcutsMenuExtension()
        self.shortcuts_menu.on_startup(ext_id)

    def on_shutdown(self):
        """Clean up resources when the extension shuts down."""
        if hasattr(self, "shortcuts_menu"):
            self.shortcuts_menu.on_shutdown()
