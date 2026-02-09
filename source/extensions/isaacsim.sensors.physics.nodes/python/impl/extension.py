# SPDX-FileCopyrightText: Copyright (c) 2018-2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
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
"""Omniverse extension entry point for physics sensor OmniGraph nodes.

This extension provides only OmniGraph nodes; sensor backends and lifecycle
are in isaacsim.sensors.experimental.physics.
"""
import omni


class Extension(omni.ext.IExt):
    """Omniverse extension for physics sensor OmniGraph nodes.

    No startup/shutdown work required; nodes use backends from
    isaacsim.sensors.experimental.physics.
    """

    def on_startup(self, ext_id: str):
        """Initialize the extension when it is loaded."""
        pass

    def on_shutdown(self):
        """Clean up when the extension is unloaded."""
        pass
