"""Test the documented example workflow for importing and configuring URDF."""

import os

import isaacsim.core.experimental.utils.stage as stage_utils
import omni
from isaacsim.asset.importer.urdf import URDFImporter, URDFImporterConfig

# Get path to extension data:
ext_manager = omni.kit.app.get_app().get_extension_manager()
ext_id = ext_manager.get_enabled_extension_id("isaacsim.asset.importer.urdf")
extension_path = ext_manager.get_extension_path(ext_id)
# import URDF

importer = URDFImporter(
    URDFImporterConfig(
        urdf_path=os.path.normpath(os.path.join(extension_path, "data", "urdf", "robots", "ur10", "urdf", "ur10.urdf")),
        usd_path=os.path.normpath(os.path.join(extension_path, "data", "urdf", "robots", "ur10", "urdf", "ur10.usd")),
        merge_mesh=True,
        allow_self_collision=True,
    )
)
output_path = importer.import_urdf()

print(output_path)
result, stage = stage_utils.open_stage(output_path)
