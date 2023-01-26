import omni
import carb
import omni.syntheticdata
import omni.graph.core as og
from dataclasses import dataclass
import traceback
from pxr import Usd, UsdGeom
import omni.isaac.IsaacSensorSchema as IsaacSensorSchema
from omni.isaac.core.utils.render_product import get_camera_prim_path
from omni.isaac.core_nodes.scripts.utils import submit_writer_attach
import omni.replicator.core as rep


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
                if not render_product_path:
                    carb.log_warn("Render product not valid")
                    db.internal_state.initialized = False
                    return False
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
                        else:
                            db.internal_state.sensor = None

                if db.internal_state.sensor is None:
                    carb.log_warn("Active camera for Render product is not an RTX Lidar")
                    db.internal_state.initialized = False
                    return False

                db.internal_state.render_product_path = render_product_path
                sensor_type = db.inputs.type
                writer = None
                try:
                    if sensor_type == "laser_scan":
                        writer = rep.writers.get("RtxLidar" + "ROS1PublishLaserScan")

                    elif sensor_type == "point_cloud":
                        writer = rep.writers.get("RtxLidar" + "ROS1PublishPointCloud")

                    else:
                        carb.log_error("type is not supported")
                        db.internal_state.initialized = False
                        return False
                    if writer is not None:
                        writer.initialize(
                            frameId=db.inputs.frameId,
                            nodeNamespace=db.inputs.nodeNamespace,
                            queueSize=db.inputs.queueSize,
                            topicName=db.inputs.topicName,
                        )
                        submit_writer_attach(writer, render_product_path)
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
