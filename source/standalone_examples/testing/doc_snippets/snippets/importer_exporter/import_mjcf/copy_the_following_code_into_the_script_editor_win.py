import isaacsim.core.experimental.utils.stage as stage_utils
import omni.usd
from isaacsim.asset.importer.mjcf import MJCFImporter, MJCFImporterConfig
from pxr import Gf, PhysicsSchemaTools, Sdf, UsdLux, UsdPhysics

# create new stage
omni.usd.get_context().new_stage()

# Get path to extension data:
ext_manager = omni.kit.app.get_app().get_extension_manager()
ext_id = ext_manager.get_enabled_extension_id("isaacsim.asset.importer.mjcf")
extension_path = ext_manager.get_extension_path(ext_id)

# setting up import configuration:
import_config = MJCFImporterConfig(mjcf_path=extension_path + "/data/mjcf/nv_ant.xml")

# import MJCF
importer = MJCFImporter(import_config)
output_usd_path = importer.import_mjcf()

# open the imported USD file into the current stage
result, stage = stage_utils.open_stage(output_usd_path)

# enable physics
scene = UsdPhysics.Scene.Define(stage, Sdf.Path("/physicsScene"))

# set gravity
scene.CreateGravityDirectionAttr().Set(Gf.Vec3f(0.0, 0.0, -1.0))
scene.CreateGravityMagnitudeAttr().Set(9.81)

# add lighting
distantLight = UsdLux.DistantLight.Define(stage, Sdf.Path("/DistantLight"))
distantLight.CreateIntensityAttr(500)
