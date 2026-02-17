# Create a new writer with the augmented image
rep.writers.register_node_writer(
    name=f"CustomROS2PublishImage",
    node_type_id="isaacsim.ros2.bridge.ROS2PublishImage",
    annotators=[
        "rgb_gaussian_noise",
        omni.syntheticdata.SyntheticData.NodeConnectionTemplate(
            "IsaacReadSimulationTime", attributes_mapping={"outputs:simulationTime": "inputs:timeStamp"}
        ),
    ],
    category="custom",
)

# Register writer for Replicator telemetry tracking
(
    rep.WriterRegistry._default_writers.append("CustomROS2PublishImage")
    if "CustomROS2PublishImage" not in rep.WriterRegistry._default_writers
    else None
)
