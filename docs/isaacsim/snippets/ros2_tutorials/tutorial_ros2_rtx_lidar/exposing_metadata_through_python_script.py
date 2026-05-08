import omni.replicator.core as rep
from isaacsim.sensors.experimental.rtx import Lidar

# Create an RTX Lidar with FULL auxiliary output level so the GenericModelOutput buffer carries
# every per-point metadata field (intensity, object ID, hit normal, ...). This sets
# ``_replicator:rendervar:GenericModelOutput:channels = ["FULL"]`` on the OmniLidar prim.
lidar = Lidar.create(
    path="/World/sensor_with_metadata",
    config="Example_Rotary",
    tick_rate=10.0,
    aux_output_level="FULL",
    translations=[[0.0, 0.0, 1.0]],
)

# RTX sensors must be assigned to their own render product.
hydra_texture = rep.create.render_product(lidar.paths[0], [1, 1], name="Isaac")

# Attach the RTX-Lidar PointCloud2 writer directly. The ``output*`` flags select which
# auxiliary fields are unpacked from the GMO buffer and written into the PointCloud2 message.
writer = rep.writers.get("RtxLidarROS2PublishPointCloud")
writer.initialize(
    topicName="point_cloud",
    frameId="base_scan",
    outputIntensity=True,
    outputObjectId=True,
)
writer.attach([hydra_texture])

# Publish the Object-ID-to-prim-path map on a separate topic so subscribers can resolve
# returns back to USD prims.
object_id_map_writer = rep.writers.get("ROS2PublishObjectIdMap")
object_id_map_writer.initialize(topicName="object_id_map")
object_id_map_writer.attach([hydra_texture])
