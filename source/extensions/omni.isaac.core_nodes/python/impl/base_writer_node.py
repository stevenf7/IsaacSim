# Copyright (c) 2020-2022, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#

import omni.usd
import carb.events
from .base_reset_node import BaseResetNode
from pxr import Usd


class WriterRequest:
    def __init__(self, writer, render_product_path, activate: bool = True):
        self.writer = writer
        self.render_product_path = render_product_path
        self.activate = activate


class BaseWriterNode(BaseResetNode):
    """
        Base class for nodes that automatically reset when stop is pressed.
    """

    def __init__(self, initialize=False):
        self.writers = []
        self.requests = []
        self._event_stream = None
        super().__init__(initialize=False)

    def custom_reset(self):
        for w in self.writers:
            self.append_request(WriterRequest(w, None, False))
        self.writers = []
        self.initialized = False

    def append_request(self, request: WriterRequest):
        self.requests.append(request)
        if self._event_stream is None:
            self._event_stream = (
                omni.kit.app.get_app()
                .get_update_event_stream()
                .create_subscription_to_pop(self._process_acivation_requests)
            )

    def _process_acivation_requests(self, event):
        stage = omni.usd.get_context().get_stage()
        if not stage:
            self._event_stream = None
            return
        with Usd.EditContext(stage, stage.GetSessionLayer()):
            for request in self.requests:
                if request.activate:
                    try:
                        request.writer.attach(request.render_product_path)
                        self.writers.append(request.writer)
                    except Exception as e:
                        carb.log_error(
                            f"Could not process writer attach request {request.writer, request.render_product_path}, {e}"
                        )
                else:
                    request.writer.detach()
            # Stop processing additional requests until another one is appended
            self.requests = []
            self._event_stream = None
