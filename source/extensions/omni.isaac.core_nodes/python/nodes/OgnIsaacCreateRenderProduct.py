# Copyright (c) 2020-2023, NVIDIA CORPORATION. All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto. Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#

import carb
import omni
import omni.hydratexture
from omni.isaac.core_nodes import BaseResetNode

# from omni.kit.viewport.utility import create_viewport_window, get_active_viewport_window
# from omni.isaac.core.utils.viewports import get_window_from_id, get_id_from_index
from omni.isaac.core_nodes.ogn.OgnIsaacCreateRenderProductDatabase import OgnIsaacCreateRenderProductDatabase
from pxr import Usd


class OgnIsaacCreateRenderProductInternalState(BaseResetNode):
    def __init__(self):
        self.hydra_texture = None
        self.render_product_path = None
        self.factory = None
        super().__init__(initialize=False)

    def on_stage_event(self, event: carb.events.IEvent):
        if event.type == int(omni.timeline.TimelineEventType.STOP):
            if self.hydra_texture:
                self.hydra_texture.updates_enabled = False
            self.initialized = False
        elif event.type == int(omni.timeline.TimelineEventType.PLAY):
            if self.hydra_texture:
                self.hydra_texture.updates_enabled = True


class OgnIsaacCreateRenderProduct:
    """
    Isaac Sim Create Hydra Texture
    """

    @staticmethod
    def internal_state():
        return OgnIsaacCreateRenderProductInternalState()

    @staticmethod
    def compute(db) -> bool:
        state = db.internal_state
        if db.inputs.enabled is False:
            if state.hydra_texture is not None:
                state.hydra_texture.updates_enabled = False
            return False
        else:
            if state.hydra_texture is not None:
                state.hydra_texture.updates_enabled = True

        if len(db.inputs.cameraPrim) == 0:
            db.log_error(f"Camera prim must be specified")
            return False
        if state.factory is None:
            state.factory = omni.hydratexture.acquire_hydra_texture_factory_interface()
        if state.hydra_texture is None:
            stage = omni.usd.get_context().get_stage()
            with Usd.EditContext(stage, stage.GetSessionLayer()):
                state.render_product_path = omni.usd.get_stage_next_free_path(
                    stage, "/Render/RenderProduct_Isaac", False
                )
                name = state.render_product_path.split("/Render/RenderProduct_")[-1]
                state.hydra_texture = state.factory.create_hydra_texture(
                    name, db.inputs.width, db.inputs.height, "", db.inputs.cameraPrim[0].GetString(), "rtx", True, True
                )
            db.outputs.renderProductPath = state.render_product_path

            state.rp_sub = (
                omni.timeline.get_timeline_interface()
                .get_timeline_event_stream()
                .create_subscription_to_pop(state.on_stage_event, name="IsaacSimOGNCoreNodesRPEventHandler")
            )
        db.outputs.execOut = omni.graph.core.ExecutionAttributeState.ENABLED
        return True

    @staticmethod
    def release(node):
        try:
            state = OgnIsaacCreateRenderProductDatabase.per_node_internal_state(node)
        except Exception:
            state = None
            pass

        if state is not None:
            state.hydra_texture = None
            state.hydra_texture_factory = None
            state.rp_sub = None
