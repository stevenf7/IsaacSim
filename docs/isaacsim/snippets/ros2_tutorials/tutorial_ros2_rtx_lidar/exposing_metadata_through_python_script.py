import omni
import omni.replicator.core as rep
from pxr import Gf

kwargs = {
    "omni:sensor:Core:auxOutputType": "FULL",
}
_, sensor = omni.kit.commands.execute(
    "IsaacSensorCreateRtxLidar",
    path="/sensor_with_metadata",
    parent=None,
    config="Example_Rotary",
    translation=(0, 0, 1.0),
    orientation=Gf.Quatd(1.0, 0.0, 0.0, 0.0),
    **kwargs,
)
hydra_texture = rep.create.render_product(sensor.GetPath(), [1, 1], name="Isaac")
# Call the build_rtx_sensor_pointcloud_writer helper method to dynamically build the Writer with the desired metadata
from isaacsim.ros2.nodes import build_rtx_sensor_pointcloud_writer

writer = build_rtx_sensor_pointcloud_writer(metadata=["Intensity", "ObjectId"], enable_full_scan=False)
writer.initialize(topicName="point_cloud", frameId="base_scan")
writer.attach([hydra_texture])
# Create a separate Writer for the ObjectId mapping
object_id_map_writer = rep.writers.get(f"ROS2PublishObjectIdMap")
object_id_map_writer.initialize(topicName="object_id_map")
object_id_map_writer.attach([hydra_texture])
