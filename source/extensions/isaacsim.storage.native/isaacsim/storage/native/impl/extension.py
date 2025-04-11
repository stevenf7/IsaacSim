# SPDX-FileCopyrightText: Copyright (c) 2022-2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: LicenseRef-NvidiaProprietary
#
# NVIDIA CORPORATION, its affiliates and licensors retain all intellectual
# property and proprietary rights in and to this material, related
# documentation and any modifications thereto. Any use, reproduction,
# disclosure or distribution of this material and related documentation
# without an express license agreement from NVIDIA CORPORATION or
# its affiliates is strictly prohibited.


import os

import carb
import omni.client
import omni.ext


class Extension(omni.ext.IExt):
    def on_startup(self, ext_id):
        """Initialize the extension.

        Args:
            ext_id: The extension ID.
        """
        self._auth_cb = None

        # Register authentication callback only if ETM_ACTIVE environment variable is set
        if os.getenv("ETM_ACTIVE"):
            self._auth_cb = omni.client.register_authentication_callback(self._authenticate)

    def _authenticate(self, prefix):
        """Authentication callback for Omniverse client.

        Args:
            prefix: URL prefix for authentication.

        Returns:
            tuple: (username, password) if credentials are available, None otherwise.
        """
        omniuser = os.getenv("ISAACSIM_OMNI_USER")
        omnipass = os.getenv("ISAACSIM_OMNI_PASS")

        if omniuser and omnipass:
            return (omniuser, omnipass)
        return None

    def on_shutdown(self):
        """Clean up resources when the extension is shut down."""
        self._auth_cb = None
