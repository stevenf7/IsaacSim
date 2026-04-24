# SPDX-FileCopyrightText: Copyright (c) 2025-2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
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

"""Common utilities and base test case for UCX node tests."""

import os
import socket

import numpy as np

try:
    from isaacsim.test.utils import TimedAsyncTestCase
except ImportError:
    raise ImportError(
        "isaacsim.test.utils is required to use UCXTestCase. " "This module should only be imported in test contexts."
    )

# UCX imports
import omni
import omni.timeline
import ucxx._lib.libucxx as ucx_api


def _read_tensor_f32(tensor) -> list:
    """Read float32 values from a FlatBuffers Tensor's ubyte data vector."""
    n_bytes = tensor.DataLength()
    raw = bytes(tensor.Data(i) for i in range(n_bytes))
    return np.frombuffer(raw, dtype=np.float32).tolist()


def find_available_port() -> int:
    """Find an available port for a UCX listener.

    Creates a temporary socket bound to port 0, allowing the OS to assign
    an available ephemeral port, then closes the socket and returns the port.

    Returns:
        An available port number.

    Example:

    .. code-block:: python

        >>> from isaacsim.ucx.nodes.tests.common import find_available_port
        >>>
        >>> port = find_available_port()
        >>> isinstance(port, int) and 1024 <= port <= 65535
        True
    """
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("", 0))
        return sock.getsockname()[1]


class UCXTestCase(TimedAsyncTestCase):
    """Base class for UCX node tests."""

    async def setUp(self):
        """Set up UCX test environment and find an available port."""
        await super().setUp()

        # Set UCX environment variables for TCP-only transport
        os.environ["UCX_TLS"] = "tcp,self"
        os.environ["UCX_NET_DEVICES"] = "all"

        self.port = find_available_port()

        # Initialize UCX client tracking
        self.client_context = None
        self.client_worker = None
        self.client_endpoint = None

    async def tearDown(self):
        """Clean up UCX client resources and stop the timeline."""
        timeline = omni.timeline.get_timeline_interface()
        timeline.stop()

        await omni.kit.app.get_app().next_update_async()

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


_ENCODING_MAP = {
    0: "custom",
    1: "rgb8",
    2: "rgba8",
    3: "bgr8",
    4: "bgra8",
    5: "r8_g8_b8",
    6: "b8_g8_r8",
    7: "mono8",
    8: "mono16",
    9: "mono32",
    10: "mono32f",
}


def unpack_image_message(buffer: object):
    """Unpack a UCX image FlatBuffers message.

    Args:
        buffer: Buffer containing the FlatBuffers-encoded Image message.

    Returns:
        Tuple of (timestamp, width, height, encoding, step, image_data).
        encoding is a lowercase string (e.g. "rgb8").
        step is derived as total_bytes / height.
        image_data is a bytes object containing the raw pixel data.
    """
    from isaacsim.ucx.nodes.messages.isaac import Image as ImageFb

    buf = bytearray(buffer.tobytes())
    msg = ImageFb.Image.GetRootAs(buf, 0)

    timestamp = msg.Header().Stamp().TimeNs() / 1e9
    height = msg.Height()
    width = msg.Width()
    encoding = _ENCODING_MAP.get(msg.Encoding(), "custom")

    tensor = msg.Data()
    n_bytes = tensor.DataLength()
    image_data = bytes(tensor.Data(i) for i in range(n_bytes))

    step = n_bytes // height if height > 0 else 0

    return timestamp, width, height, encoding, step, image_data
