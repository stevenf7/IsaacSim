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

import os

try:
    from isaacsim.test.utils import TimedAsyncTestCase
except ImportError:
    raise ImportError(
        "isaacsim.test.utils is required to use UCXTestCase. " "This module should only be imported in test contexts."
    )

# UCX imports
import ucxx._lib.libucxx as ucx_api


class UCXTestCase(TimedAsyncTestCase):
    """Base class for UCX node tests"""

    async def setUp(self):
        await super().setUp()

        # Set UCX environment variables for TCP-only transport
        os.environ["UCX_TLS"] = "tcp,self"
        os.environ["UCX_NET_DEVICES"] = "all"

        # Initialize UCX client tracking
        self.client_context = None
        self.client_worker = None
        self.client_endpoint = None

    async def tearDown(self):
        # Clean up UCX client resources
        if self.client_worker:
            try:
                self.client_worker.stop_progress_thread()
            except Exception:
                pass

        if self.client_endpoint:
            self.client_endpoint = None

        self.client_context = None
        self.client_worker = None

        await super().tearDown()

    def create_ucx_client(self, port: int):
        """Create a UCX client connection to the specified port.

        Args:
            port: Port number to connect to.

        Returns:
            Tuple of (context, worker, endpoint).
        """
        self.client_context = ucx_api.UCXContext()
        self.client_worker = ucx_api.UCXWorker(self.client_context)

        self.client_endpoint = ucx_api.UCXEndpoint.create(
            self.client_worker,
            "127.0.0.1",
            port,
            endpoint_error_handling=True,
        )

        # Start the progress thread to handle async communication
        self.client_worker.start_progress_thread()

        return self.client_context, self.client_worker, self.client_endpoint
