# SPDX-FileCopyrightText: Copyright (c) 2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
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

"""UCX Nodes Extension - manages lifecycle of native plugin."""

import carb
import omni
import omni.ext

# Bridge constants
BRIDGE_NAME = "isaacsim.ucx.nodes"
BRIDGE_PREFIX = "UCX"


class UCXBridgeExtension(omni.ext.IExt):
    """UCX Bridge Extension class."""

    def on_startup(self, ext_id):
        """Called when the extension is loaded."""
        carb.log_info("UCX Bridge Extension starting up")

        # Acquire the native plugin interface - this triggers plugin load
        from .bindings._ucx_nodes import acquire_interface

        self._interface = acquire_interface()

        self.register_nodes()

        carb.log_info("UCX Bridge Extension started")

    def on_shutdown(self):
        """Called when the extension is unloaded."""
        carb.log_info("UCX Bridge Extension shutting down")

        # Release the native plugin interface
        from .bindings._ucx_nodes import release_interface

        if hasattr(self, "_interface") and self._interface is not None:
            release_interface(self._interface)
            self._interface = None

        self.unregister_nodes()

        carb.log_info("UCX Bridge Extension shut down")

    def register_nodes(self):
        """Register the nodes for the UCX Bridge Extension."""
        pass

    def unregister_nodes(self):
        """Unregister the nodes for the UCX Bridge Extension."""
        pass
