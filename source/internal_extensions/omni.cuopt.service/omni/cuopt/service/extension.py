# SPDX-FileCopyrightText: Copyright (c) 2021-2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: LicenseRef-NvidiaProprietary
#
# NVIDIA CORPORATION, its affiliates and licensors retain all intellectual
# property and proprietary rights in and to this material, related
# documentation and any modifications thereto. Any use, reproduction,
# disclosure or distribution of this material and related documentation
# without an express license agreement from NVIDIA CORPORATION or
# its affiliates is strictly prohibited.
"""Extension entry point for the shared cuOpt service Python package."""

from typing import Any

import omni.ext


# Any class derived from `omni.ext.IExt` in top level module (defined in `python.modules` of `extension.toml`) will be
# instantiated when extension gets enabled and `on_startup(ext_id)` will be called. Later when extension gets disabled
# on_shutdown() is called.
class MyExtension(omni.ext.IExt):
    """No-op lifecycle hook for loading service helpers as an Isaac Sim extension."""

    # ext_id is current extension id. It can be used with extension manager to query additional information, like where
    # this extension is located on filesystem.
    def on_startup(self, ext_id: Any) -> Any:
        """Handle extension startup; service helpers initialize lazily when imported.

        Args:
            ext_id: Extension identifier passed by the extension manager.

        Returns:
            This hook does not return a value.
        """

    def on_shutdown(self) -> Any:
        """Handle extension shutdown; no service state is owned by this hook.

        Returns:
            This hook does not return a value.
        """
