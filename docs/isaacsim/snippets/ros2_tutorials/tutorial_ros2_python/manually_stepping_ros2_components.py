import omni.graph.core as og
import omni.kit.app

# Test setup: enable extensions that register the OmniGraph node types used below.
extension_manager = omni.kit.app.get_app().get_extension_manager()
extension_manager.set_extension_enabled_immediate("isaacsim.core.nodes", True)
extension_manager.set_extension_enabled_immediate("isaacsim.ros2.nodes", True)
# End test setup

# Create a new graph with the path /ActionGraph
og.Controller.edit(
    {"graph_path": "/ActionGraph", "evaluator_name": "execution"},
    {
        og.Controller.Keys.CREATE_NODES: [
            ("ReadSimTime", "isaacsim.core.nodes.IsaacReadSimulationTime"),
            ("Context", "isaacsim.ros2.bridge.ROS2Context"),
            ("PublishClock", "isaacsim.ros2.bridge.ROS2PublishClock"),
            ("OnImpulseEvent", "omni.graph.action.OnImpulseEvent"),
        ],
        og.Controller.Keys.CONNECT: [
            # Connecting execution of OnImpulseEvent node to PublishClock so it will only publish when an impulse event is triggered
            ("OnImpulseEvent.outputs:execOut", "PublishClock.inputs:execIn"),
            # Connecting simulationTime data of ReadSimTime to the clock publisher node
            ("ReadSimTime.outputs:simulationTime", "PublishClock.inputs:timeStamp"),
            # Connecting the ROS2 Context to the clock publisher node so it will run under the specified ROS2 Domain ID
            ("Context.outputs:context", "PublishClock.inputs:context"),
        ],
        og.Controller.Keys.SET_VALUES: [
            # Assigning topic name to clock publisher
            ("PublishClock.inputs:topicName", "/clock"),
            # Assigning a Domain ID of 1 to Context node
            ("Context.inputs:domain_id", 1),
            # Disable useDomainIDEnvVar to ensure we use the above set Domain ID
            ("Context.inputs:useDomainIDEnvVar", False),
        ],
    },
)
