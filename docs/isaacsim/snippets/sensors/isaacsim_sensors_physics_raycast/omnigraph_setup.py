# Programmatic OmniGraph setup: Physics Raycast Sensor + Debug Draw visualization
import omni.graph.core as og

sensor_prim_path = "/World/Sensors/Solid_State_Physics_Raycast_Sensor"

action_graph, _, _, _ = og.Controller.edit(
    {"graph_path": "/World/ActionGraph", "evaluator_name": "execution"},
    {
        og.Controller.Keys.CREATE_NODES: [
            ("OnPlaybackTick", "omni.graph.action.OnPlaybackTick"),
            ("ReadRaycast", "isaacsim.sensors.physics.IsaacReadRaycastSensor"),
            ("DebugDraw", "isaacsim.util.debug_draw.DebugDrawRayCast"),
        ],
        og.Controller.Keys.SET_VALUES: [
            ("ReadRaycast.inputs:raycastSensorPrim", sensor_prim_path),
            ("DebugDraw.inputs:doTransform", False),
        ],
        og.Controller.Keys.CONNECT: [
            ("OnPlaybackTick.outputs:tick", "ReadRaycast.inputs:execIn"),
            ("ReadRaycast.outputs:execOut", "DebugDraw.inputs:exec"),
            ("ReadRaycast.outputs:beamOrigins", "DebugDraw.inputs:beamOrigins"),
            ("ReadRaycast.outputs:beamEndPoints", "DebugDraw.inputs:beamEndPoints"),
            ("ReadRaycast.outputs:numRays", "DebugDraw.inputs:numRays"),
        ],
    },
)
