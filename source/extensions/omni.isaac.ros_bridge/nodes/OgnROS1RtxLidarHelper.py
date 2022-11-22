import omni
import carb
import omni.syntheticdata
import omni.graph.core as og
from dataclasses import dataclass
from omni.isaac.ros_bridge.ogn.OgnROS1RtxLidarHelperDatabase import OgnROS1RtxLidarHelperDatabase
from omni.isaac.core_nodes.scripts.utils import submit_node_template_activation
import traceback
from pxr import Usd, UsdGeom
import omni.isaac.IsaacSensorSchema as IsaacSensorSchema
from omni.isaac.core.utils.render_product import get_camera_prim_path, add_aov


class OgnROS1RtxLidarHelper:
    @dataclass
    class State:
        initialized: bool = False
        graph = None
        render_product_path = None
        sensor = None

    @staticmethod
    def initialize(graph_context, node):
        pass

    @staticmethod
    def internal_state() -> State:
        return OgnROS1RtxLidarHelper.State()

    @staticmethod
    def compute(db) -> bool:
        if db.internal_state.initialized is False:
            db.internal_state.initialized = True
            stage = omni.usd.get_context().get_stage()
            keys = og.Controller.Keys
            with Usd.EditContext(stage, stage.GetSessionLayer()):
                render_product_path = db.inputs.renderProductPath
                if stage.GetPrimAtPath(render_product_path) is None:
                    # Invalid Render Product Path
                    carb.log_warn("Render product not created yet, retrying on next call")
                    db.internal_state.initialized = False
                    return False
                else:
                    prim = stage.GetPrimAtPath(get_camera_prim_path(render_product_path))
                    if prim.IsA(UsdGeom.Camera):
                        if prim.HasAPI(IsaacSensorSchema.IsaacRtxLidarSensorAPI):
                            db.internal_state.render_product_path = render_product_path
                            db.internal_state.sensor = "lidar"

                if db.internal_state.sensor is None:
                    carb.log_warn("Active camera for Render product is not an RTX Lidar")
                    db.internal_state.initialized = False
                    return False

                db.internal_state.render_product_path = render_product_path
                sensor_type = db.inputs.type

                try:
                    if sensor_type == "laser_scan":
                        submit_node_template_activation(
                            "RtxSensorCpu" + "ROS1PublishLaserScan",
                            0,
                            [render_product_path],
                            attributes={
                                "inputs:frameId": db.inputs.frameId,
                                "inputs:nodeNamespace": db.inputs.nodeNamespace,
                                "inputs:queueSize": db.inputs.queueSize,
                                "inputs:topicName": db.inputs.topicName,
                            },
                        )

                    elif sensor_type == "point_cloud":
                        submit_node_template_activation(
                            "RtxLidar" + "ROS1PublishPointCloud",
                            0,
                            [render_product_path],
                            attributes={
                                "inputs:frameId": db.inputs.frameId,
                                "inputs:nodeNamespace": db.inputs.nodeNamespace,
                                "inputs:queueSize": db.inputs.queueSize,
                                "inputs:topicName": db.inputs.topicName,
                            },
                        )

                    else:
                        carb.log_error("type is not supported")
                        db.internal_state.initialized = False
                        return False

                except Exception as e:
                    print(traceback.format_exc())
                    pass
        else:
            if db.internal_state.graph:
                pass
            return True

    @staticmethod
    def release(node):
        pass
