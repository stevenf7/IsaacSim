import omni
import omni.replicator.core as rep
from pxr import Gf

# Create an OmniLidar prim at prim path /lidar
_, sensor = omni.kit.commands.execute(
    "IsaacSensorCreateRtxLidar",
    translation=Gf.Vec3d(0.0, 0.0, 0.0),
    orientation=Gf.Quatd(1.0, 0.0, 0.0, 0.0),
    path="/lidar",
)

# Create a render product for the sensor.
render_product = rep.create.render_product(sensor.GetPath(), resolution=(1024, 1024))

# Create an annotator
annotator = rep.AnnotatorRegistry.get_annotator("IsaacExtractRTXSensorPointCloudNoAccumulator")

# Attach the render product after the annotator is initialized.
annotator.attach([render_product.path])
