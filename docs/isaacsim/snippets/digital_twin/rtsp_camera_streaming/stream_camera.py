import omni.graph.core as og
import omni.kit.app
import omni.usd
from pxr import UsdGeom

ext_mgr = omni.kit.app.get_app().get_extension_manager()
ext_mgr.set_extension_enabled_immediate("isaacsim.core.nodes", True)
ext_mgr.set_extension_enabled_immediate("isaacsim.streaming.rtsp", True)

stage = omni.usd.get_context().get_stage()
UsdGeom.Camera.Define(stage, "/Camera")

og.Controller.edit(
    {"graph_path": "/RTSPGraph", "evaluator_name": "execution"},
    {
        og.Controller.Keys.CREATE_NODES: [
            ("OnPlaybackTick", "omni.graph.action.OnPlaybackTick"),
            ("CreateRenderProduct", "isaacsim.core.nodes.IsaacCreateRenderProduct"),
            ("RTSPHelper", "isaacsim.streaming.rtsp.RTSPCameraHelper"),
        ],
        og.Controller.Keys.SET_VALUES: [
            ("CreateRenderProduct.inputs:cameraPrim", "/Camera"),
            ("CreateRenderProduct.inputs:width", 1280),
            ("CreateRenderProduct.inputs:height", 720),
            ("RTSPHelper.inputs:port", 8554),
            ("RTSPHelper.inputs:mountPath", "/stream"),
            ("RTSPHelper.inputs:useRawEncoding", False),
        ],
        og.Controller.Keys.CONNECT: [
            ("OnPlaybackTick.outputs:tick", "CreateRenderProduct.inputs:execIn"),
            ("CreateRenderProduct.outputs:execOut", "RTSPHelper.inputs:execIn"),
            ("CreateRenderProduct.outputs:renderProductPath", "RTSPHelper.inputs:renderProductPath"),
        ],
    },
)
