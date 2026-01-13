# SPDX-FileCopyrightText: Copyright (c) 2023-2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
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

import omni.ext
from isaacsim.asset.importer.urdf import _urdf


class Extension(omni.ext.IExt):
    """Core URDF Importer Extension.

    This extension provides the core URDF parsing and importing functionality.
    For the UI components, see the isaacsim.asset.importer.urdf.ui extension.
    """

    def on_startup(self, ext_id):
        self._ext_id = ext_id
        self._urdf_interface = _urdf.acquire_urdf_interface()

    def on_shutdown(self):
        _urdf.release_urdf_interface(self._urdf_interface)
