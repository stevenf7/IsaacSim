import argparse
import sys

parser = argparse.ArgumentParser()
parser.add_argument("--test", action="store_true", help="Run in test mode.")
args, unknown = parser.parse_known_args()

import carb
from isaacsim import SimulationApp

BACKGROUND_STAGE_PATH = "/background"
BACKGROUND_USD_PATH = "/Isaac/Environments/Simple_Warehouse/warehouse_with_forklifts.usd"

CONFIG = {"renderer": "RayTracedLighting", "headless": False}

# Example ROS 2 bridge sample demonstrating the manual loading of stages and manual publishing of images
simulation_app = SimulationApp(CONFIG)
import isaacsim.core.experimental.utils.app as app_utils
import isaacsim.core.experimental.utils.stage as stage_utils
import isaacsim.core.experimental.utils.transform as transform_utils
import numpy as np
import omni
import omni.graph.core as og
import omni.replicator.core as rep
import omni.syntheticdata._syntheticdata as sd
from isaacsim.core.nodes.scripts.utils import set_target_prims
from isaacsim.sensors.experimental.rtx import CameraSensor, RtxCamera
from isaacsim.storage.native import get_assets_root_path

# Enable ROS 2 bridge extension
app_utils.enable_extension("isaacsim.ros2.bridge")

simulation_app.update()

stage_utils.set_stage_units(meters_per_unit=1.0)

# Locate Isaac Sim assets folder to load environment and robot stages
assets_root_path = get_assets_root_path()
if assets_root_path is None:
    carb.log_error("Could not find Isaac Sim assets folder")
    simulation_app.close()
    sys.exit()

# Loading the environment
stage_utils.add_reference_to_stage(assets_root_path + BACKGROUND_USD_PATH, BACKGROUND_STAGE_PATH)


###### Camera helper functions for setting up publishers. ########


def _get_sensor_info(sensor: CameraSensor) -> tuple[str, str, str]:
    """Extract render product path, camera prim path, and frame id from a CameraSensor."""
    rp_path = str(sensor.render_product.GetPath())
    prim_path = sensor.authoring_object.paths[0]
    frame_id = prim_path.split("/")[-1]
    return rp_path, prim_path, frame_id


def publish_camera_info(sensor: CameraSensor, freq):
    from isaacsim.ros2.core import read_camera_info

    rp_path, _, frame_id = _get_sensor_info(sensor)
    step_size = int(60 / freq)
    topic_name = frame_id + "_camera_info"

    writer = rep.writers.get("ROS2PublishCameraInfo")
    camera_info, _ = read_camera_info(render_product_path=rp_path)
    writer.initialize(
        frameId=frame_id,
        nodeNamespace="",
        queueSize=1,
        topicName=topic_name,
        width=camera_info.width,
        height=camera_info.height,
        projectionType=camera_info.distortion_model,
        k=camera_info.k.reshape([1, 9]),
        r=camera_info.r.reshape([1, 9]),
        p=camera_info.p.reshape([1, 12]),
        physicalDistortionModel=camera_info.distortion_model,
        physicalDistortionCoefficients=camera_info.d,
    )
    writer.attach([rp_path])

    gate_path = omni.syntheticdata.SyntheticData._get_node_path("PostProcessDispatch" + "IsaacSimulationGate", rp_path)
    og.Controller.attribute(gate_path + ".inputs:step").set(step_size)


def publish_pointcloud_from_depth(sensor: CameraSensor, freq):
    rp_path, _, frame_id = _get_sensor_info(sensor)
    step_size = int(60 / freq)
    topic_name = frame_id + "_pointcloud"

    # Note, this pointcloud publisher will convert the Depth image to a pointcloud using the Camera intrinsics.
    # This pointcloud generation method does not support semantic labeled objects.
    rv = omni.syntheticdata.SyntheticData.convert_sensor_type_to_rendervar(sd.SensorType.DistanceToImagePlane.name)

    writer = rep.writers.get(rv + "ROS2PublishPointCloud")
    writer.initialize(frameId=frame_id, nodeNamespace="", queueSize=1, topicName=topic_name)
    writer.attach([rp_path])

    gate_path = omni.syntheticdata.SyntheticData._get_node_path(rv + "IsaacSimulationGate", rp_path)
    og.Controller.attribute(gate_path + ".inputs:step").set(step_size)


def publish_rgb(sensor: CameraSensor, freq):
    rp_path, _, frame_id = _get_sensor_info(sensor)
    step_size = int(60 / freq)
    topic_name = frame_id + "_rgb"

    rv = omni.syntheticdata.SyntheticData.convert_sensor_type_to_rendervar(sd.SensorType.Rgb.name)
    writer = rep.writers.get(rv + "ROS2PublishImage")
    writer.initialize(frameId=frame_id, nodeNamespace="", queueSize=1, topicName=topic_name)
    writer.attach([rp_path])

    gate_path = omni.syntheticdata.SyntheticData._get_node_path(rv + "IsaacSimulationGate", rp_path)
    og.Controller.attribute(gate_path + ".inputs:step").set(step_size)


def publish_depth(sensor: CameraSensor, freq):
    rp_path, _, frame_id = _get_sensor_info(sensor)
    step_size = int(60 / freq)
    topic_name = frame_id + "_depth"

    rv = omni.syntheticdata.SyntheticData.convert_sensor_type_to_rendervar(sd.SensorType.DistanceToImagePlane.name)
    writer = rep.writers.get(rv + "ROS2PublishImage")
    writer.initialize(frameId=frame_id, nodeNamespace="", queueSize=1, topicName=topic_name)
    writer.attach([rp_path])

    gate_path = omni.syntheticdata.SyntheticData._get_node_path(rv + "IsaacSimulationGate", rp_path)
    og.Controller.attribute(gate_path + ".inputs:step").set(step_size)


def publish_camera_tf(sensor: CameraSensor):
    _, camera_prim, _ = _get_sensor_info(sensor)

    if not stage_utils.get_current_stage().GetPrimAtPath(camera_prim).IsValid():
        raise ValueError(f"Camera path '{camera_prim}' is invalid.")

    try:
        # Generate the camera_frame_id. OmniActionGraph will use the last part of
        # the full camera prim path as the frame name, so we will extract it here
        # and use it for the pointcloud frame_id.
        camera_frame_id = camera_prim.split("/")[-1]

        # Generate an action graph associated with camera TF publishing.
        ros_camera_graph_path = "/CameraTFActionGraph"

        # If a camera graph is not found, create a new one.
        if not stage_utils.get_current_stage().GetPrimAtPath(ros_camera_graph_path).IsValid():
            (ros_camera_graph, _, _, _) = og.Controller.edit(
                {
                    "graph_path": ros_camera_graph_path,
                    "evaluator_name": "execution",
                    "pipeline_stage": og.GraphPipelineStage.GRAPH_PIPELINE_STAGE_SIMULATION,
                },
                {
                    og.Controller.Keys.CREATE_NODES: [
                        ("OnTick", "omni.graph.action.OnTick"),
                        ("IsaacClock", "isaacsim.core.nodes.IsaacReadSimulationTime"),
                        ("RosPublisher", "isaacsim.ros2.bridge.ROS2PublishClock"),
                    ],
                    og.Controller.Keys.CONNECT: [
                        ("OnTick.outputs:tick", "RosPublisher.inputs:execIn"),
                        ("IsaacClock.outputs:simulationTime", "RosPublisher.inputs:timeStamp"),
                    ],
                },
            )

        # Generate 2 nodes associated with each camera: TF from world to ROS camera convention, and world frame.
        og.Controller.edit(
            ros_camera_graph_path,
            {
                og.Controller.Keys.CREATE_NODES: [
                    ("PublishTF_" + camera_frame_id, "isaacsim.ros2.bridge.ROS2PublishTransformTree"),
                    ("PublishRawTF_" + camera_frame_id + "_world", "isaacsim.ros2.bridge.ROS2PublishRawTransformTree"),
                ],
                og.Controller.Keys.SET_VALUES: [
                    ("PublishTF_" + camera_frame_id + ".inputs:topicName", "/tf"),
                    # Note if topic_name is changed to something else besides "/tf",
                    # it will not be captured by the ROS tf broadcaster.
                    ("PublishRawTF_" + camera_frame_id + "_world.inputs:topicName", "/tf"),
                    ("PublishRawTF_" + camera_frame_id + "_world.inputs:parentFrameId", camera_frame_id),
                    ("PublishRawTF_" + camera_frame_id + "_world.inputs:childFrameId", camera_frame_id + "_world"),
                    # Static transform from ROS camera convention to world (+Z up, +X forward) convention:
                    ("PublishRawTF_" + camera_frame_id + "_world.inputs:rotation", [0.5, -0.5, 0.5, 0.5]),
                ],
                og.Controller.Keys.CONNECT: [
                    (ros_camera_graph_path + "/OnTick.outputs:tick", "PublishTF_" + camera_frame_id + ".inputs:execIn"),
                    (
                        ros_camera_graph_path + "/OnTick.outputs:tick",
                        "PublishRawTF_" + camera_frame_id + "_world.inputs:execIn",
                    ),
                    (
                        ros_camera_graph_path + "/IsaacClock.outputs:simulationTime",
                        "PublishTF_" + camera_frame_id + ".inputs:timeStamp",
                    ),
                    (
                        ros_camera_graph_path + "/IsaacClock.outputs:simulationTime",
                        "PublishRawTF_" + camera_frame_id + "_world.inputs:timeStamp",
                    ),
                ],
            },
        )
    except Exception as e:
        print(e)

    # Add target prims for the USD pose. All other frames are static.
    set_target_prims(
        primPath=ros_camera_graph_path + "/PublishTF_" + camera_frame_id,
        inputName="inputs:targetPrims",
        targetPrimPaths=[camera_prim],
    )
    return


###################################################################

# Create a CameraSensor. RtxCamera handles prim creation with position/orientation;
# CameraSensor wraps it and creates a render product at the desired resolution.
rtx_camera = RtxCamera(
    "/World/floating_camera",
    positions=np.array([-3.11, -1.87, 1.0]),
    orientations=transform_utils.euler_angles_to_quaternion(np.array([0, 0, 0]), degrees=True).numpy(),
)

simulation_app.update()

camera_sensor = CameraSensor(rtx_camera, resolution=(256, 256))

############### Calling Camera publishing functions ###############

approx_freq = 30
publish_camera_tf(camera_sensor)
publish_camera_info(camera_sensor, approx_freq)
publish_rgb(camera_sensor, approx_freq)
publish_depth(camera_sensor, approx_freq)
publish_pointcloud_from_depth(camera_sensor, approx_freq)

####################################################################

# Initialize physics
app_utils.play()

i = 0
while simulation_app.is_running() and (not args.test or i < 100):
    simulation_app.update()
    i += 1
app_utils.stop()
simulation_app.close()
