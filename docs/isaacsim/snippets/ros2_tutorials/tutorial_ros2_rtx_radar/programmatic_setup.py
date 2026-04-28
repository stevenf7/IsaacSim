import carb
import omni.graph.core as og
import omni.kit.app
from isaacsim.sensors.experimental.rtx import Radar

# This snippet uses OG nodes from isaacsim.core.nodes (IsaacCreateRenderProduct,
# OgnIsaacRunOneSimulationFrame) and isaacsim.ros2.nodes (ROS2RtxRadarHelper).
# Enable both before constructing the action graph.
ext_mgr = omni.kit.app.get_app().get_extension_manager()
ext_mgr.set_extension_enabled_immediate("isaacsim.core.nodes", True)
ext_mgr.set_extension_enabled_immediate("isaacsim.ros2.nodes", True)

# RTX Radar requires Motion BVH to be enabled.
settings = carb.settings.get_settings()
settings.set("/renderer/raytracingMotion/enabled", True)
settings.set("/renderer/raytracingMotion/enableHydraEngineMasking", True)
settings.set("/renderer/raytracingMotion/enabledForHydraEngines", "0,1,2,3,4")

# Create radar with auxiliary output for radial velocity.
radar = Radar(path="/Radar", aux_output_level="BASIC")

# Create the OmniGraph (mirrors the action graph built by the GUI workflow above).
og.Controller.edit(
    {"graph_path": "/ActionGraph", "evaluator_name": "execution"},
    {
        og.Controller.Keys.CREATE_NODES: [
            ("OnPlaybackTick", "omni.graph.action.OnPlaybackTick"),
            ("RunOnce", "isaacsim.core.nodes.OgnIsaacRunOneSimulationFrame"),
            ("CreateRenderProduct", "isaacsim.core.nodes.IsaacCreateRenderProduct"),
            ("RadarHelper", "isaacsim.ros2.bridge.ROS2RtxRadarHelper"),
        ],
        og.Controller.Keys.SET_VALUES: [
            ("CreateRenderProduct.inputs:cameraPrim", radar.paths[0]),
            ("RadarHelper.inputs:topicName", "radar_point_cloud"),
            ("RadarHelper.inputs:frameId", "radar"),
            ("RadarHelper.inputs:outputRadialVelocityMS", True),
        ],
        og.Controller.Keys.CONNECT: [
            ("OnPlaybackTick.outputs:tick", "RunOnce.inputs:execIn"),
            ("RunOnce.outputs:step", "CreateRenderProduct.inputs:execIn"),
            ("CreateRenderProduct.outputs:execOut", "RadarHelper.inputs:execIn"),
            ("CreateRenderProduct.outputs:renderProductPath", "RadarHelper.inputs:renderProductPath"),
        ],
    },
)
