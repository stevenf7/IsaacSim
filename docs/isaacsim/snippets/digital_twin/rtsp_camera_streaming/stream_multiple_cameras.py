import omni.graph.core as og
import omni.kit.app
import omni.usd
from pxr import UsdGeom

ext_mgr = omni.kit.app.get_app().get_extension_manager()
ext_mgr.set_extension_enabled_immediate("isaacsim.core.nodes", True)
ext_mgr.set_extension_enabled_immediate("isaacsim.streaming.rtsp", True)

stage = omni.usd.get_context().get_stage()
UsdGeom.Camera.Define(stage, "/CameraFront")
UsdGeom.Camera.Define(stage, "/CameraRear")

og.Controller.edit(
    {"graph_path": "/MultiStreamGraph", "evaluator_name": "execution"},
    {
        og.Controller.Keys.CREATE_NODES: [
            ("OnPlaybackTick", "omni.graph.action.OnPlaybackTick"),
            ("FrontRP", "isaacsim.core.nodes.IsaacCreateRenderProduct"),
            ("RearRP", "isaacsim.core.nodes.IsaacCreateRenderProduct"),
            ("FrontRTSP", "isaacsim.streaming.rtsp.RTSPCameraHelper"),
            ("RearRTSP", "isaacsim.streaming.rtsp.RTSPCameraHelper"),
        ],
        og.Controller.Keys.SET_VALUES: [
            ("FrontRP.inputs:cameraPrim", "/CameraFront"),
            ("FrontRP.inputs:width", 1280),
            ("FrontRP.inputs:height", 720),
            ("RearRP.inputs:cameraPrim", "/CameraRear"),
            ("RearRP.inputs:width", 1280),
            ("RearRP.inputs:height", 720),
            ("FrontRTSP.inputs:port", 8554),
            ("FrontRTSP.inputs:mountPath", "/front"),
            ("RearRTSP.inputs:port", 8555),
            ("RearRTSP.inputs:mountPath", "/rear"),
        ],
        og.Controller.Keys.CONNECT: [
            ("OnPlaybackTick.outputs:tick", "FrontRP.inputs:execIn"),
            ("OnPlaybackTick.outputs:tick", "RearRP.inputs:execIn"),
            ("FrontRP.outputs:execOut", "FrontRTSP.inputs:execIn"),
            ("RearRP.outputs:execOut", "RearRTSP.inputs:execIn"),
            ("FrontRP.outputs:renderProductPath", "FrontRTSP.inputs:renderProductPath"),
            ("RearRP.outputs:renderProductPath", "RearRTSP.inputs:renderProductPath"),
        ],
    },
)
