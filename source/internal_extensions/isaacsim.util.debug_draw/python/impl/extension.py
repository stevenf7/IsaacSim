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

"""Debug draw extension entry point."""

import omni.ext

from .. import _debug_draw


class Extension(omni.ext.IExt):
    """Extension that manages the debug draw interface lifecycle."""

    def on_startup(self) -> None:
        """Initialize the extension and acquire the debug draw interface."""
        self._draw = _debug_draw.acquire_debug_draw_interface()

    def on_shutdown(self) -> None:
        """Release the debug draw interface during shutdown."""
        _debug_draw.release_debug_draw_interface(self._draw)
